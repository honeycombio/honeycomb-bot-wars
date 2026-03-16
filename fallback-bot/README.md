# battleships-bot-starter

A ready-to-run Battleships bot for the workshop. If you couldn't generate your own bot with Kiro, start here — it's a solid competitor. You'll still do all the telemetry steps, which is the real workshop.

---

## Quickstart

```bash
pip install -r requirements.txt
```

Register and play by **challenge ID**:
```bash
python battleships_bot.py --challenge-id "YOUR-CHALLENGE-ID" --name "your-bot-name" --owner "Your Name"
```

Or by **challenge name**:
```bash
python battleships_bot.py --challenge-name "Workshop Challenge" --name "your-bot-name" --owner "Your Name"
```

Your credentials are saved to `.battleships-registration.json` automatically. On subsequent runs, the bot reconnects without re-registering.

**Example output:**
```
Battleships Challenge Bot
────────────────────────────────────────
  Server   : https://battleships.devrel.hny.wtf
  Challenge: YOUR-CHALLENGE-ID
  Bot name : your-bot-name
  Owner    : Your Name
────────────────────────────────────────
  No saved credentials — registering now...
  Registration ID : reg-550e8400-...
  Challenge Bot ID: bot-abc123
  Credentials saved to .battleships-registration.json

Connecting to wss://battleships.devrel.hny.wtf/ws/challenge/reg-550e8400-...
WebSocket connected.

Confirmed: your-bot-name registered in 'Workshop Challenge'

Game 1/6: vs Bumbling Bee
  Result : WON
  Hits   : 17 (us) vs 12 (them)
  Points : +15
...

────────────────────────────────────────
CHALLENGE COMPLETE
────────────────────────────────────────
  Wins          : 5
  Losses        : 1
  Total Points  : 74
  Hit Difference: +28
  ★  New personal best!
────────────────────────────────────────
```

---

## What this bot does

- Places ships spread across the board with gap rows — no adjacency violations
- Fires in a **checkerboard sweep** (most efficient pattern for a 10×10 board)
- Switches to **hunt mode** when it scores a hit — targets adjacent cells until the ship sinks
- Falls back to full-grid sweep to finish remaining ships

It will beat beginner and easy bots reliably. To beat medium and hard bots, use Kiro to add telemetry and let the data show you what to improve.

---

## Add telemetry with Kiro

This bot has no observability — that's intentional. Use these three Kiro prompts to add it layer by layer.

Set your Honeycomb credentials first:

```bash
export HONEYCOMB_API_KEY="your-api-key"
export HONEYCOMB_DATASET="battleships"
```

---

### Prompt 1 — Basic tracing

Paste into the Kiro agent panel:

```
Add OpenTelemetry tracing to my battleships bot. Use the OTLP HTTP exporter
sending to Honeycomb (https://api.honeycomb.io) with the API key from the
HONEYCOMB_API_KEY environment variable and dataset name from HONEYCOMB_DATASET.
Create a root span for each game (named `game`) that starts on PLACE_SHIPS_REQUEST
and ends on GAME_RESULT. Add a child span for each shot fired (named `fire`).
Install any required packages.
```

Restart your bot and check Honeycomb. Run this query:
- **Visualise:** `COUNT` — **Group by:** `name`
- You should see `game` and `fire` rows. Click a trace — that's your entire game.

---

### Prompt 2 — Shot intelligence

```
On each `fire` span, add the following attributes:
- shot.row (int) and shot.col (int) — the target coordinates
- shot.number (int) — sequential shot count for this game, starting at 1
- shot.result (string) — HIT, MISS, or SUNK from the server's opponentView
- game.id (string) — the game ID
```

Restart and play a few games. Run these queries:

**Where am I wasting shots?**
- Visualise: `COUNT` — Filter: `name = fire AND shot.result = MISS` — Group by: `shot.row`, `shot.col`

**What's my overall hit rate?**
- Visualise: `COUNT` — Group by: `shot.result`

---

### Prompt 3 — Game outcomes

```
On the `game` root span, add these attributes when GAME_RESULT is received:
- game.result (string) — WON or LOST
- game.score (int) — the points value from the server
- game.shots_fired (int) — total shots taken
- game.hits (int) — total hits scored
- game.misses (int) — total misses
- game.accuracy (float) — hits / shots_fired
- game.opponent (string) — the opponent bot's display name
```

Play 5+ games, then run these queries:

**Am I getting better over time?**
- Visualise: `AVG(game.score)` — X-axis: time

**Which opponent is destroying me?**
- Visualise: `AVG(game.score)` — Group by: `game.opponent`

---

## Improve your bot with Kiro

Use your Honeycomb data to pick the right improvement. Paste into Kiro:

**Low hit rate:**
```
My hit rate is low. Update my firing strategy to use a smarter checkerboard
pattern that maximises board coverage.
```

**Losing to hunt-mode bots:**
```
I keep losing to bots that track my ships efficiently. Update my ship placement
to spread ships to the edges and corners, making them harder to locate.
```

**Poor scores against medium-difficulty bots:**
```
Improve my hunt mode: after a hit, fire along both axes to determine ship
orientation before committing to a direction, then sweep the full ship length.
```

---

## Requirements

- Python 3.10+
- `requests`
- `websockets`

```bash
pip install -r requirements.txt
```

---

## Arguments

| Argument | Required | Description |
|---|---|---|
| `--name` | Yes | Your bot's display name |
| `--owner` | No | Your name (shown on leaderboard) |
| `--challenge-id` | One of these | The challenge UUID |
| `--challenge-name` | One of these | The challenge name (case-sensitive) |
| `--server` | No | Override the server URL |

---

## Platform

**[battleships.devrel.hny.wtf](https://battleships.devrel.hny.wtf)** — leaderboard, challenges, and docs
