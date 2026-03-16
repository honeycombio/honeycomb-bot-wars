### Telemetry Prompt 1 — Basic tracing (5 min)

**Copy this into Kiro:**

*"Add OpenTelemetry tracing to my battleships bot. Use the OTLP HTTP exporter sending to Honeycomb (`https://api.honeycomb.io`) with the API key from the `HONEYCOMB_API_KEY` environment variable and dataset name from `HONEYCOMB_DATASET`. Create a root span for each game (named `game`) that starts when a `PLACE_SHIPS_REQUEST` message is received and ends when a `GAME_RESULT` message is received for that game. Add a child span for each shot fired (named `fire`). Install any required packages."*

**After running:** restart your bot and play a game. Go to Honeycomb → you should see traces appearing. Click one — that's a complete game.

**Honeycomb query to run:**
- Dataset: `battleships`
- Visualise: `COUNT`
- Group by: `name`
- You should see `game` and `fire` events