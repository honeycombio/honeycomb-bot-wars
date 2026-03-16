#!/usr/bin/env python3
"""
Battleships Workshop Bot — Challenge Mode
------------------------------------------
Registers for a challenge, connects via WebSocket, and plays all games automatically.
Credentials are saved locally so you can reconnect without re-registering.

Usage:
    pip install -r requirements.txt

    # First run — register by challenge ID:
    python battleships_bot.py --challenge-id "abc-123" --name "your-bot" --owner "Your Name"

    # Or register by challenge name:
    python battleships_bot.py --challenge-name "Spring Challenge" --name "your-bot" --owner "Your Name"

    # Subsequent runs — credentials are saved, just run again:
    python battleships_bot.py --challenge-id "abc-123" --name "your-bot" --owner "Your Name"
"""

import asyncio
import json
import os
import random
import argparse
import urllib.parse
import requests
import websockets
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────

SERVER_URL   = "https://battleships.devrel.hny.wtf"
CREDS_FILE   = ".battleships-registration.json"

SHIPS = [
    {"typeId": "CARRIER",    "size": 5},
    {"typeId": "BATTLESHIP", "size": 4},
    {"typeId": "CRUISER",    "size": 3},
    {"typeId": "SUBMARINE",  "size": 3},
    {"typeId": "DESTROYER",  "size": 2},
]

# ─── Credential persistence ───────────────────────────────────────────────────

def load_credentials(challenge_key: str) -> dict | None:
    """Load saved registration credentials for a challenge."""
    if not Path(CREDS_FILE).exists():
        return None
    with open(CREDS_FILE) as f:
        all_creds = json.load(f)
    return all_creds.get(challenge_key)


def save_credentials(challenge_key: str, creds: dict):
    """Persist registration credentials so we can reconnect without re-registering."""
    all_creds = {}
    if Path(CREDS_FILE).exists():
        with open(CREDS_FILE) as f:
            all_creds = json.load(f)
    all_creds[challenge_key] = creds
    with open(CREDS_FILE, "w") as f:
        json.dump(all_creds, f, indent=2)
    print(f"  Credentials saved to {CREDS_FILE}")


# ─── Registration ─────────────────────────────────────────────────────────────

def register_bot(
    bot_name:       str,
    owner:          str,
    challenge_id:   str | None = None,
    challenge_name: str | None = None,
) -> dict:
    """
    Register bot with the challenge server.
    If the same displayName is used, the server returns the existing registration.
    """
    payload = {"displayName": bot_name, "owner": owner}

    if challenge_id:
        url = f"{SERVER_URL}/api/v1/challenges/{urllib.parse.quote(challenge_id)}/bots"
    elif challenge_name:
        url = f"{SERVER_URL}/api/v1/challenges/by-name/{urllib.parse.quote(challenge_name)}/bots"
    else:
        raise ValueError("Provide either --challenge-id or --challenge-name")

    print(f"  Registering at {url} ...")
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    print(f"  Registration ID : {data['registrationId']}")
    print(f"  Challenge Bot ID: {data['challengeBotId']}")
    print(f"  WebSocket URL   : {data['webSocketUrl']}")
    if data.get("message"):
        print(f"  Server says     : {data['message']}")

    return data


def get_or_register(args) -> dict:
    """Return saved credentials if available, otherwise register fresh."""
    challenge_key = args.challenge_id or args.challenge_name
    saved = load_credentials(challenge_key)

    if saved:
        print(f"  Found saved registration: {saved['registrationId']}")
        return saved

    print("  No saved credentials — registering now...")
    creds = register_bot(
        bot_name=args.name,
        owner=args.owner,
        challenge_id=args.challenge_id,
        challenge_name=args.challenge_name,
    )
    save_credentials(challenge_key, creds)
    return creds


# ─── Ship placement ───────────────────────────────────────────────────────────

def place_ships(allow_adjacent: bool = False) -> list:
    """
    Place all ships horizontally with 2-row gaps.
    Guarantees no adjacency violations even when adjacency is not allowed.
    """
    placements = []
    occupied   = set()
    row        = 0

    for ship in SHIPS:
        placed = False
        while row <= 9 and not placed:
            for col in range(10 - ship["size"] + 1):
                cells = [(row, col + i) for i in range(ship["size"])]
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
                        "typeId":      ship["typeId"],
                        "start":       {"row": row, "col": col},
                        "orientation": "H",
                    })
                    placed = True
                    row += 2  # leave a gap row
                    break
            if not placed:
                row += 1

    return placements


# ─── Firing strategy ──────────────────────────────────────────────────────────

def build_target_queue() -> list:
    """
    Checkerboard sweep — covers all ships of size ≥2 in the fewest possible shots.
    Both halves are shuffled so opponents can't predict our pattern.
    """
    primary   = [(r, c) for r in range(10) for c in range(10) if (r + c) % 2 == 0]
    secondary = [(r, c) for r in range(10) for c in range(10) if (r + c) % 2 == 1]
    random.shuffle(primary)
    random.shuffle(secondary)
    return primary + secondary


def new_game_state() -> dict:
    return {
        "shots_fired":  set(),
        "hunt_queue":   [],   # adjacent cells to explore after a hit
        "target_queue": build_target_queue(),
    }


def sync_shots(state: dict, opponent_view: dict):
    """Update local state from the opponentView the server sends us."""
    for shot in opponent_view.get("shots", []):
        coord  = (shot["row"], shot["col"])
        result = shot.get("result", "")
        if coord in state["shots_fired"]:
            continue
        state["shots_fired"].add(coord)
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
    """Pick next firing target: hunt mode first, then checkerboard sweep."""
    while state["hunt_queue"]:
        coord = state["hunt_queue"].pop(0)
        if coord not in state["shots_fired"]:
            return {"row": coord[0], "col": coord[1]}

    for coord in state["target_queue"]:
        if coord not in state["shots_fired"]:
            return {"row": coord[0], "col": coord[1]}

    # Exhaustive fallback (shouldn't be needed in normal play)
    for r in range(10):
        for c in range(10):
            if (r, c) not in state["shots_fired"]:
                return {"row": r, "col": c}

    return {"row": 0, "col": 0}


# ─── Bot ─────────────────────────────────────────────────────────────────────

class ChallengeBot:
    def __init__(self, name: str):
        self.name  = name
        self.games: dict[str, dict] = {}

    async def run(self, registration_id: str, ws_url: str, auth_token: str | None):
        """Connect to the challenge WebSocket and play until CHALLENGE_COMPLETE."""
        # Force wss:// — server may return ws://, http://, or https:// but always runs over TLS
        connect_url = "wss://" + ws_url.split("://", 1)[-1]

        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
            # Append as query param fallback only when token is non-empty
            if "?" not in connect_url:
                connect_url = f"{connect_url}?token={auth_token}"

        print(f"\nConnecting to {connect_url}")
        async with websockets.connect(connect_url, additional_headers=headers) as ws:
            print("WebSocket connected.\n")
            async for raw in ws:
                msg = json.loads(raw)
                should_continue = await self.handle(ws, msg)
                if not should_continue:
                    break

    async def handle(self, ws, msg: dict) -> bool:
        """
        Dispatch incoming messages. Returns False when the session is complete.
        """
        msg_type = msg.get("messageType", msg.get("type", "UNKNOWN"))
        payload  = msg.get("payload", msg)  # some servers flatten the payload

        if msg_type == "CHALLENGE_REGISTERED":
            bot_name  = payload.get("displayName", self.name)
            challenge = payload.get("challengeName", "")
            print(f"Confirmed: {bot_name} registered in '{challenge}'")
            print(payload.get("message", ""))

        elif msg_type == "PLACE_SHIPS_REQUEST":
            req     = payload.get("request", payload)
            game_id = req.get("gameId", payload.get("gameId", ""))
            rules   = req.get("rules", {})
            allow_adjacent = rules.get("allowAdjacentShips", False)

            self.games[game_id] = new_game_state()
            ships = place_ships(allow_adjacent)
            print(f"  [{game_id[:8]}] Placing ships...")

            await ws.send(json.dumps({
                "messageType": "PLACE_SHIPS_RESPONSE",
                "payload": {
                    "gameId": game_id,
                    "response": {"placements": ships},
                },
            }))

        elif msg_type == "FIRE_REQUEST":
            req           = payload.get("request", payload)
            game_id       = req.get("gameId", payload.get("gameId", ""))
            turn          = req.get("turnNumber", "?")
            opponent_view = req.get("opponentView", {})

            if game_id not in self.games:
                self.games[game_id] = new_game_state()

            state = self.games[game_id]
            sync_shots(state, opponent_view)
            target     = choose_target(state)
            shot_count = len(state["shots_fired"])
            print(f"  [{game_id[:8]}] Turn {turn} — firing at ({target['row']}, {target['col']})")

            await ws.send(json.dumps({
                "messageType": "FIRE_RESPONSE",
                "payload": {
                    "gameId": game_id,
                    "response": {"target": target},
                },
            }))

        elif msg_type == "GAME_RESULT":
            game_id  = payload.get("gameId", "?")[:8]
            opponent = payload.get("opponentDisplayName", payload.get("opponentId", "?"))
            won      = payload.get("isWin", False)
            points   = payload.get("points", "?")
            p_hits   = payload.get("playerHits", "?")
            o_hits   = payload.get("opponentHits", "?")
            game_num = payload.get("gameNumber", "?")
            total    = payload.get("totalGames", "?")
            result   = "WON" if won else "LOST"
            print(f"\nGame {game_num}/{total}: vs {opponent}")
            print(f"  Result : {result}")
            print(f"  Hits   : {p_hits} (us) vs {o_hits} (them)")
            print(f"  Points : +{points}")
            # Clean up game state
            self.games.pop(payload.get("gameId", ""), None)

        elif msg_type == "CHALLENGE_COMPLETE":
            wins        = payload.get("wins", "?")
            losses      = payload.get("losses", "?")
            points      = payload.get("totalPoints", "?")
            hit_diff    = payload.get("hitDifference", "?")
            new_best    = payload.get("isNewBest", False)
            print("\n" + "─" * 40)
            print("CHALLENGE COMPLETE")
            print("─" * 40)
            print(f"  Wins          : {wins}")
            print(f"  Losses        : {losses}")
            print(f"  Total Points  : {points}")
            print(f"  Hit Difference: {hit_diff}")
            if new_best:
                print("  ★  New personal best!")
            print("─" * 40)
            print("\nConnection closed by server.")
            return False  # signal to stop the loop

        elif msg_type == "ERROR":
            error_code = payload.get("errorCode", "")
            message    = payload.get("message", str(payload))
            print(f"\n[ERROR] {error_code}: {message}")

        else:
            print(f"[{msg_type}] {payload}")

        return True  # keep the loop going


# ─── Entry point ─────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Battleships Challenge Bot")
    parser.add_argument("--server",         default=SERVER_URL,  help="Server base URL")
    parser.add_argument("--challenge-id",   default=None,        help="Challenge ID")
    parser.add_argument("--challenge-name", default=None,        help="Challenge name (case-sensitive)")
    parser.add_argument("--name",           required=True,       help="Your bot's display name")
    parser.add_argument("--owner",          default="",          help="Your name (owner)")
    args = parser.parse_args()

    if not args.challenge_id and not args.challenge_name:
        parser.error("Provide either --challenge-id or --challenge-name")

    global SERVER_URL
    SERVER_URL = args.server.rstrip("/")

    print("Battleships Challenge Bot")
    print("─" * 40)
    print(f"  Server   : {SERVER_URL}")
    print(f"  Challenge: {args.challenge_id or args.challenge_name}")
    print(f"  Bot name : {args.name}")
    print(f"  Owner    : {args.owner or '(not set)'}")
    print("─" * 40)

    creds         = get_or_register(args)
    registration_id = creds["registrationId"]
    ws_url          = creds["webSocketUrl"]
    auth_token      = creds.get("authToken")  # present on first registration; may be absent on reconnect

    bot = ChallengeBot(args.name)
    await bot.run(registration_id, ws_url, auth_token)


if __name__ == "__main__":
    asyncio.run(main())
