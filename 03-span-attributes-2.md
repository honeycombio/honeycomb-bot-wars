### Telemetry Prompt 3 — Game outcomes (5 min)

> **Copy this into Kiro:**
>
> *"On the `game` root span, add the following attributes when the `GAME_RESULT` message is received: `game.result` (WON or LOST, from `isWin`), `game.score` (the `points` integer from GAME_RESULT), `game.shots_fired` (total shots taken that game), `game.hits` (total hits, from `playerHits`), `game.opponent` (the `opponentDisplayName` string), `game.number` (the `gameNumber` int), `game.total` (the `totalGames` int), and `game.accuracy` (hits divided by shots_fired, as a float)."*

**After running:** restart your bot and play 5+ games.

**Honeycomb queries to run:**

Query 3 — *Am I getting better?*
- SELECT: `AVG(game.score)`
- → See your score trend over time

Query 4 — *Which opponents am I losing to?*
- SELECT: `AVG(game.score)`
- Group by: `game.opponent`
- → See which bots are destroying you — those are your targets
