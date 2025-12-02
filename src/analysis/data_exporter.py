"""
Data Exporter - Exports game data to CSV and other formats for analysis
"""
import csv
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime


class DataExporter:
    """Exports game data for external analysis"""
    
    def __init__(self, output_dir: str = "game_logs"):
        """Initialize exporter"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_decisions_to_csv(self, decisions: List[Dict[str, Any]], timestamp: str):
        """Export all decisions to CSV"""
        filename = self.output_dir / f"decisions_{timestamp}.csv"
        
        if not decisions:
            return None
        
        fieldnames = [
            'timestamp', 'player', 'model', 'role', 'party',
            'decision_type', 'decision', 'reasoning',
            'round', 'liberal_policies', 'fascist_policies',
            'tokens_used'
        ]
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for decision in decisions:
                row = {
                    'timestamp': decision.get('timestamp', ''),
                    'player': decision.get('player', ''),
                    'model': decision.get('model', ''),
                    'role': decision.get('role', ''),
                    'party': decision.get('party', ''),
                    'decision_type': decision.get('decision_type', ''),
                    'decision': str(decision.get('decision', '')),
                    'reasoning': decision.get('reasoning', ''),
                    'round': decision.get('context', {}).get('round', ''),
                    'liberal_policies': decision.get('context', {}).get('liberal_policies', ''),
                    'fascist_policies': decision.get('context', {}).get('fascist_policies', ''),
                    'tokens_used': decision.get('tokens_used', 0)
                }
                writer.writerow(row)
        
        print(f"Decisions exported to: {filename}")
        return filename
    
    def export_conversations_to_csv(self, conversations: List[Dict[str, str]], timestamp: str):
        """Export conversations to CSV"""
        filename = self.output_dir / f"conversations_{timestamp}.csv"
        
        if not conversations:
            return None
        
        fieldnames = ['timestamp', 'speaker', 'message', 'round', 'phase']
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for conv in conversations:
                row = {
                    'timestamp': conv.get('timestamp', ''),
                    'speaker': conv.get('speaker', ''),
                    'message': conv.get('message', ''),
                    'round': conv.get('context', {}).get('round', ''),
                    'phase': conv.get('context', {}).get('phase', '')
                }
                writer.writerow(row)
        
        print(f"Conversations exported to: {filename}")
        return filename
    
    def export_analysis_to_csv(self, analysis: Dict[str, Any], timestamp: str):
        """Export analysis results to CSV"""
        filename = self.output_dir / f"analysis_{timestamp}.csv"
        
        rows = []
        
        # Export per-player statistics
        for player, stats in analysis.get('conversation_analysis', {}).get('speaker_stats', {}).items():
            row = {
                'player': player,
                'metric': 'conversation_stats',
                'message_count': stats.get('message_count', 0),
                'avg_message_length': stats.get('avg_message_length', 0),
                'deception_count': stats.get('deception_count', 0),
                'persuasion_count': stats.get('persuasion_count', 0),
                'accusations_made': stats.get('accusations_made', 0)
            }
            rows.append(row)
        
        if rows:
            fieldnames = rows[0].keys()
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"Analysis exported to: {filename}")
            return filename
        
        return None
    
    def create_research_dataset(self, game_logs: List[str]):
        """Combine multiple game logs into research dataset"""
        dataset_file = self.output_dir / f"research_dataset_{datetime.now().strftime('%Y%m%d')}.json"
        
        combined_data = {
            "games": [],
            "metadata": {
                "total_games": len(game_logs),
                "created": datetime.now().isoformat()
            }
        }
        
        for log_file in game_logs:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    game_data = json.load(f)
                    combined_data["games"].append(game_data)
            except Exception as e:
                print(f"Error loading {log_file}: {e}")
        
        with open(dataset_file, 'w', encoding='utf-8') as f:
            json.dump(combined_data, f, indent=2)
        
        print(f"Research dataset created: {dataset_file}")
        return dataset_file
