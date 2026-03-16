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

## Leaderboard

The live leaderboard is on screen at the front. Final standings at **[TIME ON SCREEN]**.

Good luck.

---

*Need help? Flag down a facilitator or check the challenge page: battleships.devrel.hny.wtf/challenges*
