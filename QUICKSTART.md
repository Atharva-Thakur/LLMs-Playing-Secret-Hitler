# Quick Start Guide

## Setup (First Time)

1. **Install Python 3.9+** (if not already installed)

2. **Create virtual environment:**

   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```cmd
   pip install -r requirements.txt
   ```

4. **Configure Azure OpenAI:**
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Azure OpenAI credentials:
     ```
     AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
     AZURE_OPENAI_API_KEY=your-api-key
     AZURE_OPENAI_DEPLOYMENT_GPT4=your-gpt4-deployment-name
     ```

## Run a Game

```cmd
python main.py
```

The game will:

- Create 5 LLM players (configurable in `.env`)
- Play a complete Secret Hitler game
- Log all conversations and decisions
- Analyze strategies and deception tactics
- Save results to `game_logs/` folder

## Customize Settings

Edit `.env` file:

- `NUM_PLAYERS`: Number of players (5-10)
- `TEMPERATURE`: LLM creativity (0.0-1.0)
- `MAX_TOKENS`: Response length limit

## Analyze Results

After running games, check the `game_logs/` directory:

- `game_*.json`: Complete game data
- `decisions_*.csv`: All player decisions
- `conversations_*.csv`: All conversations
- `analysis_*.csv`: Statistical analysis
- `summary_*.txt`: Human-readable summary

## Research Tips

1. **Run multiple games** to gather statistical data
2. **Compare different models** by changing deployments
3. **Adjust temperature** to see how creativity affects strategy
4. **Analyze gaslighting patterns** in the JSON logs
5. **Look for role-specific behaviors** in decision logs

## Troubleshooting

**"Missing Azure OpenAI credentials"**

- Make sure `.env` file exists and has correct credentials

**"Invalid player count"**

- NUM_PLAYERS must be between 5 and 10

**API Rate Limits**

- Reduce NUM_PLAYERS or add delays in the code
- Use lower tier models (GPT-3.5) for faster games

## Next Steps

1. Run your first game
2. Examine the output logs
3. Modify prompts in `prompts/base_prompts.json`
4. Experiment with different model combinations
5. Analyze patterns across multiple games
