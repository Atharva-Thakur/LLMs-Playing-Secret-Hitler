"""
Analysis script for multiple game logs
Run this after playing several games to compare results
"""
import json
import os
from pathlib import Path
from collections import Counter, defaultdict
import statistics


def analyze_game_file(filepath: str) -> dict:
    """Analyze a single game log file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    game_data = data['game_metadata']
    decisions = data['decisions']
    conversations = data['conversations']
    
    # Basic stats
    stats = {
        'winner': game_data.get('winner'),
        'rounds': game_data.get('total_rounds', 0),
        'num_players': game_data.get('num_players', 0),
        'total_conversations': len(conversations),
        'total_decisions': len(decisions),
    }
    
    # Player performance by role
    player_stats = defaultdict(lambda: {
        'total': 0,
        'wins': 0,
        'survived': 0,
        'decisions': 0,
        'messages': 0
    })
    
    for player_info in game_data.get('players', []):
        role = player_info['role']
        party = player_info['party']
        won = (party == game_data.get('winner'))
        
        player_stats[role]['total'] += 1
        if won:
            player_stats[role]['wins'] += 1
    
    # Count player decisions and messages
    for decision in decisions:
        player_name = decision.get('player', '')
        # Find player role
        for player_info in game_data.get('players', []):
            if player_info['name'] == player_name:
                player_stats[player_info['role']]['decisions'] += 1
                break
    
    for conv in conversations:
        speaker = conv.get('speaker', '')
        for player_info in game_data.get('players', []):
            if player_info['name'] == speaker:
                player_stats[player_info['role']]['messages'] += 1
                break
    
    stats['player_stats'] = dict(player_stats)
    
    return stats


def analyze_all_games(game_logs_dir: str = "game_logs"):
    """Analyze all game logs in directory"""
    logs_path = Path(game_logs_dir)
    
    if not logs_path.exists():
        print(f"Directory {game_logs_dir} not found!")
        return
    
    game_files = list(logs_path.glob("game_*.json"))
    
    if not game_files:
        print(f"No game log files found in {game_logs_dir}")
        return
    
    print(f"Found {len(game_files)} game logs\n")
    print("=" * 80)
    print("MULTI-GAME ANALYSIS")
    print("=" * 80)
    
    all_stats = []
    winners = Counter()
    total_rounds = []
    role_performance = defaultdict(lambda: {'total': 0, 'wins': 0})
    
    for game_file in game_files:
        try:
            stats = analyze_game_file(str(game_file))
            all_stats.append(stats)
            
            if stats['winner']:
                winners[stats['winner']] += 1
            
            total_rounds.append(stats['rounds'])
            
            # Aggregate role performance
            for role, role_stats in stats.get('player_stats', {}).items():
                role_performance[role]['total'] += role_stats['total']
                role_performance[role]['wins'] += role_stats['wins']
        
        except Exception as e:
            print(f"Error analyzing {game_file}: {e}")
    
    # Print aggregate statistics
    print(f"\nTotal Games Analyzed: {len(all_stats)}")
    print(f"\nWin Distribution:")
    for party, count in winners.items():
        percentage = (count / len(all_stats)) * 100
        print(f"  {party.upper()}: {count} ({percentage:.1f}%)")
    
    print(f"\nGame Length Statistics:")
    print(f"  Average rounds: {statistics.mean(total_rounds):.1f}")
    print(f"  Median rounds: {statistics.median(total_rounds):.1f}")
    print(f"  Min rounds: {min(total_rounds)}")
    print(f"  Max rounds: {max(total_rounds)}")
    
    print(f"\nRole Performance:")
    for role, perf in role_performance.items():
        if perf['total'] > 0:
            win_rate = (perf['wins'] / perf['total']) * 100
            print(f"  {role.upper()}:")
            print(f"    Times played: {perf['total']}")
            print(f"    Wins: {perf['wins']}")
            print(f"    Win rate: {win_rate:.1f}%")
    
    # Conversation statistics
    total_convs = sum(s['total_conversations'] for s in all_stats)
    avg_convs = total_convs / len(all_stats) if all_stats else 0
    
    print(f"\nConversation Statistics:")
    print(f"  Total conversations across all games: {total_convs}")
    print(f"  Average per game: {avg_convs:.1f}")
    
    print("\n" + "=" * 80)
    print("Analysis complete!")
    print(f"Individual game logs available in: {game_logs_dir}/")


if __name__ == "__main__":
    analyze_all_games()
