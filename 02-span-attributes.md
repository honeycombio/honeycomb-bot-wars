### Telemetry Prompt 2 — Shot intelligence (5 min)

**Copy this into Kiro:**

*"On each `fire` span, add the following attributes: `shot.row` (int), `shot.col` (int), `shot.number` (the sequential shot count for this game, starting at 1), `shot.result` (the result string: HIT, MISS, or SUNK — read from `opponentView.shots` in the next `FIRE_REQUEST` by comparing the previous target coordinates), and `game.id` (the game ID string)."*

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