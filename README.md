# LLMs Playing Secret Leader (Secret Hitler)

This project simulates a game of "Secret Leader" (mechanically identical to Secret Hitler) played by LLM agents (Gemini).

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Set up your API key:
    - Copy `.env.example` to `.env`
    - Add your `GEMINI_API_KEY`.
    - Get you api key from `https://aistudio.google.com/api-keys`

## Running the Game

Run the main script:

```bash
python -m src.main
```

## Logs

Logs are stored in the `logs/` directory. They contain detailed information about:
- Public speech
- Private thoughts (Internal Monologue)
- Game events
- Actions taken

## Structure

- `src/engine`: Game logic and state.
- `src/agents`: LLM agent implementation and prompts.
- `src/utils`: Helper functions (Logger, LLM Client).
