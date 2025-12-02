"""
Game logger - Records all game events and conversations
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path


class GameLogger:
    """Logs all game events, decisions, and conversations"""
    
    def __init__(self, output_dir: str = "game_logs", auto_save: bool = True):
        """Initialize game logger"""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_log: List[Dict[str, Any]] = []
        self.conversation_log: List[Dict[str, str]] = []
        self.decision_log: List[Dict[str, Any]] = []
        
        self.auto_save = auto_save
        self.incremental_log_file = self.output_dir / f"game_{self.timestamp}_incremental.jsonl"
        
        # Create incremental log file
        if self.auto_save:
            with open(self.incremental_log_file, 'w', encoding='utf-8') as f:
                f.write(json.dumps({"type": "game_start", "timestamp": self.timestamp}) + "\n")
        
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Log a game event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        self.game_log.append(entry)
        
        # Write to incremental log
        if self.auto_save:
            self._append_to_incremental_log({"type": "event", **entry})
    
    def log_conversation(self, speaker: str, message: str, context: Dict[str, Any]):
        """Log a conversation/statement"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "speaker": speaker,
            "message": message,
            "context": context
        }
        self.conversation_log.append(entry)
        
        # Write to incremental log
        if self.auto_save:
            self._append_to_incremental_log({"type": "conversation", **entry})
    
    def log_decision(self, player: str, decision_type: str, decision: Any, reasoning: str, context: Dict[str, Any]):
        """Log a player decision"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "player": player,
            "decision_type": decision_type,
            "decision": str(decision),
            "reasoning": reasoning,
            "context": context
        }
        self.decision_log.append(entry)
        
        # Write to incremental log
        if self.auto_save:
            self._append_to_incremental_log({"type": "decision", **entry})
    
    def _append_to_incremental_log(self, entry: Dict[str, Any]):
        """Append entry to incremental log file"""
        try:
            with open(self.incremental_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Warning: Failed to write to incremental log: {e}")
    
    def save_game_log(self, game_data: Dict[str, Any]):
        """Save complete game log to JSON file"""
        filename = self.output_dir / f"game_{self.timestamp}.json"
        
        complete_log = {
            "game_metadata": game_data,
            "events": self.game_log,
            "conversations": self.conversation_log,
            "decisions": self.decision_log,
            "timestamp": self.timestamp
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(complete_log, f, indent=2, ensure_ascii=False)
        
        print(f"Game log saved to: {filename}")
        if self.auto_save:
            print(f"Incremental log available at: {self.incremental_log_file}")
        return filename
    
    def save_summary(self, summary: str):
        """Save human-readable game summary"""
        filename = self.output_dir / f"summary_{self.timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"Summary saved to: {filename}")
        return filename
    
    def get_conversation_transcript(self) -> str:
        """Get formatted conversation transcript"""
        transcript = []
        transcript.append("=" * 80)
        transcript.append("GAME CONVERSATION TRANSCRIPT")
        transcript.append("=" * 80)
        transcript.append("")
        
        for entry in self.conversation_log:
            timestamp = entry['timestamp'].split('T')[1][:8]
            speaker = entry['speaker']
            message = entry['message']
            transcript.append(f"[{timestamp}] {speaker}: {message}")
            transcript.append("")
        
        return "\n".join(transcript)
