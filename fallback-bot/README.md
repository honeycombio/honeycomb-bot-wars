# battleships-bot-starter

A ready-to-run Battleships bot for the workshop. If you couldn't generate your own bot with Kiro, start here. You'll still do all the telemetry steps — that's the real workshop.

---

## Quickstart

```bash
pip install -r requirements.txt
python battleships_bot.py --name "your-name-here"
```

You should see:
```
Registering bot 'your-name-here'...
Registered! Player ID: abc123...
Connecting to wss://battleships.devrel.hny.wtf/ws/player/...
Connected — waiting for games...
```

Your bot will start playing automatically. Check the leaderboard at **[battleships.devrel.hny.wtf](https://battleships.devrel.hny.wtf)**.

---

## What this bot does

- Places ships spread across the board with gap rows to avoid adjacency violations
- Fires in a **checkerboard sweep** pattern — the most efficient way to cover a 10×10 board
- Switches to **hunt mode** when it gets a hit — targets adjacent cells until the ship sinks
- Falls back to full grid sweep to finish off remaining ships

It will beat beginner and easy bots reliably. To beat medium and hard bots, you'll need to add telemetry and use the data to improve.

---

## Add telemetry with Kiro

This bot has no observability yet — that's intentional. Use these prompts in Kiro to add it layer by layer.

### Prompt 1 — Basic tracing

Paste this into the Kiro agent panel:

```
Add OpenTelemetry tracing to my battleships bot. Use the OTLP HTTP exporter
sending to Honeycomb (https://api.honeycomb.io) with the API key from the
HONEYCOMB_API_KEY environment variable and dataset name from HONEYCOMB_DATASET.
Create a root span for each game session (named `game`) that starts when a
PLACE_SHIPS_REQUEST is received and ends when the game completes. Add a child
span for each shot fired (named `fire`). Install any required packages.
```

Then set your environment variables and restart:

```bash
export HONEYCOMB_API_KEY="your-api-key"
export HONEYCOMB_DATASET="battleships"
python battleships_bot.py --name "your-name"
```

Open Honeycomb and run:
- Visualise: `COUNT` — Group by: `name`
- You should see `game` and `fire` events. Click a trace — that's your entire game.

---

### Prompt 2 — Shot intelligence

```
On each `fire` span, add the following attributes: `shot.row` (int),
`shot.col` (int), `shot.number` (the sequential shot count for this game,
starting at 1), `shot.result` (the result string: HIT, MISS, or SUNK if
available from the server response or next game update), and `game.id`
(the game ID string).
```

Restart your bot and run these queries in Honeycomb:

**Where am I missing?**
- Visualise: `COUNT` — Filter: `name = fire AND shot.result = MISS` — Group by: `shot.row`, `shot.col`

**What's my hit rate?**
- Visualise: `COUNT` — Group by: `shot.result`

---

### Prompt 3 — Game outcomes

```
On the `game` root span, add the following attributes when the game completes:
`game.result` (COMPLETED or ABANDONED), `game.score` (the final score integer),
`game.shots_fired` (total shots taken), `game.hits` (total hits), `game.misses`
(total misses), `game.accuracy` (hits divided by shots_fired, as a float).
Also add a `game.opponent` attribute with the name of the bot we played against,
if available in the game data.
```

Play 5+ games, then run these queries:

**Am I getting better?**
- Visualise: `AVG(game.score)` — X-axis: time

**Who is beating me?**
- Visualise: `AVG(game.score)` — Group by: `game.opponent`

---

## Improve your bot with Kiro

Once you have data, use it. Pick the prompt that matches what your Honeycomb queries are telling you:

**Low hit rate:**
```
My hit rate is low. Update my firing strategy to use a smarter checkerboard
pattern that maximises coverage.
```

**Losing to hunt-mode bots:**
```
I'm losing badly to bots that use hunt-mode targeting. Update my ship placement
to spread ships to the edges and corners to make them harder to find.
```

**Poor scores against medium bots:**
```
Add hunt mode to my firing logic: when I get a hit, fire at adjacent cells until
the ship is sunk before resuming sweep mode.
```

---

## Requirements

- Python 3.8+
- `requests`
- `websockets`

```bash
pip install -r requirements.txt
```

---

## Platform

**[battleships.devrel.hny.wtf](https://battleships.devrel.hny.wtf)** — leaderboard, challenges, and docs
