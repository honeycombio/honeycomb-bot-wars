# Battleships Workshop — Participant Guide

**45 minutes. One goal: build a bot, add eyes to it, use what you see to win.**

---

## The Story

Your bot is about to go to war — but right now it's flying blind. It fires shots, wins or loses, and you have no idea why.

By the end of this workshop you'll have **full visibility** into every shot your bot fires, every hit it scores, and every pattern in how your enemies attack you. That data is your weapon.

**The arc:**
1. Deploy a bot → watch it play blind
2. Instrument it → see what's happening inside
3. Query the data → find the pattern
4. Use the insight → climb the leaderboard

---

## Step 1 — Generate your bot with Kiro (8 min)

1. Open **Kiro**
2. Open a new empty folder as your workspace
3. Open the Kiro agent panel
4. Open **`prompt.txt`** from this repo (or copy it from the screen at the front)
5. Replace `[LANGUAGE]` on line 1 with Python
6. Paste the full prompt into the Kiro agent panel and hit send
7. Kiro will generate a working bot — save the file(s) it creates

> **Stuck or behind?** Skip to the fallback bot below.

---

## Step 2 — Run your bot (3 min)

Install dependencies and run your bot:

**Python example:**
```bash
pip install requests websockets
python your_bot.py --challenge-id "CHALLENGE-ID-ON-SCREEN" --name "your-name" --owner "Your Name"
```

> The challenge ID is on the front screen. Your credentials are saved automatically after the first run — no need to re-register.

You should see your bot connect, play through all games, and print a final score. Check the leaderboard — can you see your name?

---

## Fallback bot

If you couldn't generate a bot, use this one — it's in the same repo you're reading this from:

```bash
# From the repo root
pip install -r fallback-bot/requirements.txt
python fallback-bot/battleships_bot.py --challenge-id "CHALLENGE-ID-ON-SCREEN" --name "your-name" --owner "Your Name"
```

You'll still do all the telemetry steps — that's the real workshop.

---

## Step 3 — Connect Honeycomb (3 min)

1. Log in to **[honeycomb.io](https://honeycomb.io)**
2. From the home screen, grab your **API key** (Account → API Keys)
3. In Kiro, set an environment variable:

```bash
export HONEYCOMB_API_KEY="your-key-here"
export HONEYCOMB_DATASET="battleships"
```

Or add them to a `.env` file in your project folder:
```
HONEYCOMB_API_KEY=your-key-here
HONEYCOMB_DATASET=battleships
```

---

## Step 4 — Add telemetry with Kiro (15 min)

You'll run three prompts in Kiro. Each one adds a layer of visibility.

Paste each prompt into the Kiro agent panel in order.

---

### Telemetry Prompt 1 — Basic tracing (5 min)

> **Copy this into Kiro:**
>
> *"Add OpenTelemetry tracing to my battleships bot. Use the OTLP HTTP exporter sending to Honeycomb (`https://api.honeycomb.io`) with the API key from the `HONEYCOMB_API_KEY` environment variable and dataset name from `HONEYCOMB_DATASET`. Create a root span for each game (named `game`) that starts when a `PLACE_SHIPS_REQUEST` message is received and ends when a `GAME_RESULT` message is received for that game. Add a child span for each shot fired (named `fire`). Install any required packages."*

**After running:** restart your bot and play a game. Go to Honeycomb → you should see traces appearing. Click one — that's a complete game.

**Honeycomb query to run:**
- Dataset: `battleships`
- Visualise: `COUNT`
- Group by: `name`
- You should see `game` and `fire` events

---

### Telemetry Prompt 2 — Shot intelligence (5 min)

> **Copy this into Kiro:**
>
> *"On each `fire` span, add the following attributes: `shot.row` (int), `shot.col` (int), `shot.number` (the sequential shot count for this game, starting at 1), `shot.result` (the result string: HIT, MISS, or SUNK — read from `opponentView.shots` in the next `FIRE_REQUEST` by comparing the previous target coordinates), and `game.id` (the game ID string)."*

**After running:** restart your bot and play a few games.

**Honeycomb queries to run:**

Query 1 — *Where am I wasting shots?*
- Visualise: `COUNT`
- Filter: `name = fire` AND `shot.result = MISS`
- Group by: `shot.row`, `shot.col`
- → See which board zones you miss most

Query 2 — *What's my hit rate?*
- Visualise: `COUNT`
- Group by: `shot.result`
- → See your overall hit/miss/sunk breakdown

---

### Telemetry Prompt 3 — Game outcomes (5 min)

> **Copy this into Kiro:**
>
> *"On the `game` root span, add the following attributes when the `GAME_RESULT` message is received: `game.result` (WON or LOST, from `isWin`), `game.score` (the `points` integer from GAME_RESULT), `game.shots_fired` (total shots taken that game), `game.hits` (total hits, from `playerHits`), `game.opponent` (the `opponentDisplayName` string), `game.number` (the `gameNumber` int), `game.total` (the `totalGames` int), and `game.accuracy` (hits divided by shots_fired, as a float)."*

**After running:** restart your bot and play 5+ games.

**Honeycomb queries to run:**

Query 3 — *Am I getting better?*
- Visualise: `AVG(game.score)`
- X-axis: `time`
- → See your score trend over time

Query 4 — *Which opponents am I losing to?*
- Visualise: `AVG(game.score)`
- Group by: `game.opponent`
- → See which bots are destroying you — those are your targets

---

## Step 5 — Use the data (5 min)

You now have real data. Use it.

**Ask Kiro to improve your bot based on what you've found.** Some prompts to try:

- *"My Honeycomb data shows my hit rate is only 18%. Update my firing strategy to use a smarter checkerboard pattern that maximises coverage."*
- *"I'm consistently losing to bots that use hunt-mode targeting. Update my ship placement strategy to spread ships to the edges and corners to make them harder to find."*
- *"My average score against medium-difficulty bots is low. Add a hunt mode to my firing logic: when I get a hit, fire at adjacent cells until the ship is sunk before resuming sweep mode."*

Watch your score climb on the leaderboard.

---

## Leaderboard

The live leaderboard is on screen at the front. Final standings at **[TIME ON SCREEN]**.

Good luck.

---

*Need help? Flag down a facilitator or check the challenge page: battleships.devrel.hny.wtf/challenges*
