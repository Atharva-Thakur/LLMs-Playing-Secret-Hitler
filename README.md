# Multi-LLM Secret Hitler Game

A research project exploring how different LLMs play Secret Hitler, including analysis of their argumentation strategies, deception tactics, and decision-making processes.

## Overview

This project simulates games of Secret Hitler with multiple LLM players, logging and analyzing:

- Voting patterns and decisions
- Argumentation strategies
- Deception and persuasion attempts
- Role-based behavior differences
- Inter-LLM interactions and "gaslighting" tactics

## Project Structure

```
secret-hitler/
├── src/
│   ├── game/           # Core game logic and rules
│   ├── llm/            # LLM integration and player agents
│   ├── analysis/       # Response analysis and logging
│   └── utils/          # Shared utilities
├── prompts/            # Structured prompts for different game phases
├── game_logs/          # Output directory for game logs (generated)
├── .env.example        # Environment variables template
├── requirements.txt    # Python dependencies
└── main.py            # Main game runner
```

## Setup

1. **Clone the repository**

2. **Create virtual environment**

   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Azure OpenAI**

   - Copy `.env.example` to `.env`
   - Fill in your Azure OpenAI credentials and deployment names

5. **Run a game**
   ```bash
   python main.py
   ```

## Configuration

Edit `.env` file to customize:

- Azure OpenAI endpoints and API keys
- Model deployments
- Number of players (5-10)
- Temperature and token limits
- Logging options

## Game Rules (Simplified)

Secret Hitler is a social deduction game where:

- **Liberals** try to pass 5 liberal policies or assassinate Hitler
- **Fascists** (including Hitler) try to pass 6 fascist policies or elect Hitler as Chancellor after 3 fascist policies

Players vote on governments, and elected governments enact policies from a random deck.

## Analysis Features

The project logs and analyzes:

- **Conversation transcripts**: Full dialogue between LLMs
- **Decision justifications**: Why each LLM voted or acted as they did
- **Deception detection**: Attempts to mislead other players
- **Strategy evolution**: How tactics change throughout the game
- **Role performance**: Success rates by role and model

## Output

Game logs are saved to `game_logs/` directory with:

- `game_{timestamp}.json`: Complete game state and conversation log
- `analysis_{timestamp}.csv`: Structured data for analysis
- `summary_{timestamp}.txt`: Human-readable game summary

## Research Applications

Use this project to study:

- LLM theory of mind capabilities
- Deception and persuasion in AI
- Multi-agent coordination
- Strategic reasoning under uncertainty
- Model-specific behavioral patterns

