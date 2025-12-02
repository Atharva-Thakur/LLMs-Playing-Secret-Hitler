"""
Main entry point for Secret Hitler LLM Game
"""
import sys
from src.utils import Config, print_header, print_error, print_success, print_info
from src.game_orchestrator import GameOrchestrator


def main():
    """Run Secret Hitler game with LLM players"""
    print_header("🎮 SECRET HITLER - MULTI-LLM RESEARCH PROJECT 🎮")
    
    # Validate configuration
    try:
        Config.validate()
        print_success("Configuration validated")
    except ValueError as e:
        print_error(str(e))
        print_info("\nPlease create a .env file based on .env.example and fill in your Azure OpenAI credentials.")
        return 1
    
    # Generate player names
    num_players = Config.NUM_PLAYERS
    player_names = [f"Player_{i+1}" for i in range(num_players)]
    
    print_info(f"Starting game with {num_players} players")
    
    # Configure models - you can mix different models here
    model_configs = [
        {
            "deployment": Config.AZURE_OPENAI_DEPLOYMENT_GPT4,
            "name": "GPT-4o"
        }
    ]
    
    print_info(f"Using models: {', '.join(m['name'] for m in model_configs)}")
    
    try:
        # Create and run game
        orchestrator = GameOrchestrator(player_names, model_configs)
        results = orchestrator.run_game()
        
        print_success("\nGame completed successfully!")
        
        # Print summary statistics
        winner = results['game_data'].get('winner', 'Unknown')
        rounds = results['game_data'].get('total_rounds', 0)
        
        print_info(f"Winner: {winner.upper()}")
        print_info(f"Total rounds: {rounds}")
        print_info(f"Conversations: {len(results.get('conversation_analysis', {}).get('conversation_log', []))}")
        print_info(f"Gaslighting attempts: {len(results.get('gaslighting_attempts', []))}")
        
        if Config.SAVE_GAME_LOGS:
            print_success(f"\nLogs saved to: {Config.OUTPUT_DIR}/")
        
        return 0
        
    except KeyboardInterrupt:
        print_info("\n\nGame interrupted by user")
        return 130
    
    except Exception as e:
        print_error(f"Error during game: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
