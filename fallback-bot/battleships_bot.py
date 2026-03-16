#!/usr/bin/env python3
"""
Battleships Workshop Fallback Bot
----------------------------------
A solid baseline bot with a checkerboard sweep + hunt-mode strategy.

If you couldn't generate your own bot, use this one.
Then use Kiro to add telemetry — that's the real workshop!

Usage:
    pip install requests websockets
    python battleships_bot.py --name "your-bot-name"
"""

import asyncio
import json
import random
import argparse
import requests
import websockets

SERVER_URL = "https://battleships.devrel.hny.wtf"

SHIPS = [
    {"type": "CARRIER",    "size": 5},
    {"type": "BATTLESHIP", "size": 4},
    {"type": "CRUISER",    "size": 3},
    {"type": "SUBMARINE",  "size": 3},
    {"type": "DESTROYER",  "size": 2},
]


def register_bot(bot_name: str):
    """Register bot with the server, return (player_id, ws_url)."""
    print(f"Registering bot '{bot_name}'...")
    resp = requests.post(
        f"{SERVER_URL}/api/v1/players",
        json={"displayName": bot_name, "maxConcurrentGames": 1},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    player_id = data["playerId"]
    ws_url = data.get("wsUrl") or f"wss://battleships.devrel.hny.wtf/ws/player/{player_id}"
    print(f"Registered! Player ID: {player_id}")
    return player_id, ws_url


def place_ships() -> list:
    """
    Place ships horizontally, spread across the board with 2-row gaps.
    Avoids adjacency violations reliably.
    """
    placements = []
    occupied = set()
    row = 0

    for ship in SHIPS:
        placed = False
        while row <= 9 and not placed:
            for col in range(10 - ship["size"] + 1):
                cells = [(row, col + i) for i in range(ship["size"])]
                # Check cell + all neighbours are clear
                conflict = any(
                    (r + dr, c + dc) in occupied
                    for r, c in cells
                    for dr in (-1, 0, 1)
                    for dc in (-1, 0, 1)
                )
                if not conflict:
                    for cell in cells:
                        occupied.add(cell)
                    placements.append({
                        "type": ship["type"],
                        "position": {"row": row, "col": col},
                        "direction": "HORIZONTAL",
                    })
                    placed = True
                    row += 2  # leave a gap row before the next ship
                    break
            if not placed:
                row += 1

    return placements


def build_target_queue() -> list:
    """
    Checkerboard pattern first (covers all ships of size 2+ in fewest shots),
    then fill in the gaps. Both halves are shuffled for unpredictability.
    """
    primary   = [(r, c) for r in range(10) for c in range(10) if (r + c) % 2 == 0]
    secondary = [(r, c) for r in range(10) for c in range(10) if (r + c) % 2 == 1]
    random.shuffle(primary)
    random.shuffle(secondary)
    return primary + secondary


def new_game_state() -> dict:
    return {
        "shots_fired": set(),
        "hunt_queue":  [],          # cells to prioritise after a hit
        "target_queue": build_target_queue(),
    }


def sync_shots(state: dict, opponent_view: dict):
    """Update local state from the server's opponent view."""
    for shot in opponent_view.get("shots", []):
        coord = (shot["row"], shot["col"])
        if coord in state["shots_fired"]:
            continue
        state["shots_fired"].add(coord)
        result = shot.get("result", "")
        if result in ("HIT", "SUNK"):
            if result == "HIT":
                # Queue adjacent cells for hunt mode
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    adj = (shot["row"] + dr, shot["col"] + dc)
                    if (
                        0 <= adj[0] <= 9
                        and 0 <= adj[1] <= 9
                        and adj not in state["shots_fired"]
                        and adj not in state["hunt_queue"]
                    ):
                        state["hunt_queue"].insert(0, adj)


def choose_target(state: dict) -> dict:
    """Pick the next cell to fire at."""
    # Hunt mode — follow up adjacent to a known hit
    while state["hunt_queue"]:
        coord = state["hunt_queue"].pop(0)
        if coord not in state["shots_fired"]:
            return {"row": coord[0], "col": coord[1]}

    # Sweep mode — work through the checkerboard queue
    for coord in state["target_queue"]:
        if coord not in state["shots_fired"]:
            return {"row": coord[0], "col": coord[1]}

    # Fallback (should never reach here in a normal game)
    for r in range(10):
        for c in range(10):
            if (r, c) not in state["shots_fired"]:
                return {"row": r, "col": c}

    return {"row": 0, "col": 0}


class BattleshipsBot:
    def __init__(self, name: str):
        self.name = name
        self.games: dict[str, dict] = {}

    async def run(self, player_id: str, ws_url: str):
        print(f"Connecting to {ws_url}")
        async with websockets.connect(ws_url) as ws:
            print("Connected — waiting for games...\n")
            async for raw in ws:
                msg = json.loads(raw)
                await self.handle(ws, msg)

    async def handle(self, ws, msg: dict):
        t        = msg.get("type", "UNKNOWN")
        game_id  = msg.get("gameId", "")
        short_id = game_id[:8] if game_id else ""

        if t == "REGISTERED":
            print(f"Server confirmed registration.")

        elif t == "PLACE_SHIPS_REQUEST":
            self.games[game_id] = new_game_state()
            ships = place_ships()
            print(f"[{short_id}] Placing {len(ships)} ships...")
            await ws.send(json.dumps({
                "type":   "PLACE_SHIPS",
                "gameId": game_id,
                "ships":  ships,
            }))

        elif t == "FIRE_REQUEST":
            if game_id not in self.games:
                self.games[game_id] = new_game_state()
            state         = self.games[game_id]
            opponent_view = msg.get("opponentView", {})
            sync_shots(state, opponent_view)
            target = choose_target(state)
            shots  = len(state["shots_fired"])
            print(f"[{short_id}] Shot #{shots + 1} → ({target['row']}, {target['col']})")
            await ws.send(json.dumps({
                "type":   "FIRE",
                "gameId": game_id,
                "row":    target["row"],
                "col":    target["col"],
            }))

        elif t == "GAME_UPDATE":
            status = msg.get("status", "")
            if status in ("COMPLETED", "ABANDONED"):
                score = msg.get("score", "?")
                shots = len(self.games.get(game_id, {}).get("shots_fired", []))
                print(f"[{short_id}] Game {status} — Score: {score}  (shots fired: {shots})\n")
                self.games.pop(game_id, None)

        elif t == "ERROR":
            print(f"[ERROR] {msg.get('message', msg)}")

        else:
            print(f"[{t}] {msg}")


async def main():
    parser = argparse.ArgumentParser(description="Battleships workshop fallback bot")
    parser.add_argument("--name", default="workshop-bot", help="Your bot's display name")
    args = parser.parse_args()

    player_id, ws_url = register_bot(args.name)
    bot = BattleshipsBot(args.name)
    await bot.run(player_id, ws_url)


if __name__ == "__main__":
    asyncio.run(main())
