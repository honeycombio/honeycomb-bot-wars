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
4. Go to **[battleships.devrel.hny.wtf/docs/ai-generator?mode=challenge](https://battleships.devrel.hny.wtf/docs/ai-generator?mode=challenge)**
5. Select your preferred language
6. Copy the full prompt from the page
7. Paste it into the Kiro agent panel and hit send
8. Kiro will generate a working bot — save the file it creates

> **Stuck or behind?** Skip to the fallback bot below.

---

## Step 2 — Run your bot (3 min)

Install dependencies and run your bot:

**Python example:**
```bash
pip install requests websockets
python your_bot.py --name "your-name-here"
```

You should see your bot connect and start playing. Check the leaderboard on screen — can you see your bot?

> The workshop challenge ID is on the front screen. Make sure your bot is registered to that challenge.

---

## Fallback bot

If you couldn't generate a bot, use this one instead — it's a solid checkerboard-strategy bot:

**[github.com/gist/LINK-ON-SCREEN]**

```bash
# Download and run
pip install requests websockets
python battleships_bot.py --name "your-name-here"
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
> *"Add OpenTelemetry tracing to my battleships bot. Use the OTLP HTTP exporter sending to Honeycomb (`https://api.honeycomb.io`) with the API key from the `HONEYCOMB_API_KEY` environment variable and dataset name from `HONEYCOMB_DATASET`. Create a root span for each game session (named `game`) that starts when a PLACE_SHIPS_REQUEST is received and ends when the game completes. Add a child span for each shot fired (named `fire`). Install any required packages."*

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
> *"On each `fire` span, add the following attributes: `shot.row` (int), `shot.col` (int), `shot.number` (the sequential shot count for this game, starting at 1), `shot.result` (the result string: HIT, MISS, or SUNK if available from the server response or next game update), and `game.id` (the game ID string)."*

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
> *"On the `game` root span, add the following attributes when the game completes: `game.result` (COMPLETED or ABANDONED), `game.score` (the final score integer), `game.shots_fired` (total shots taken), `game.hits` (total hits), `game.misses` (total misses), `game.accuracy` (hits divided by shots_fired, as a float). Also add a `game.opponent` attribute with the name of the bot we played against, if available in the game data."*

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
