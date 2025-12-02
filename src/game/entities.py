"""
Core game entities and enums for Secret Hitler
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional


class Role(Enum):
    """Player roles in Secret Hitler"""
    LIBERAL = "liberal"
    FASCIST = "fascist"
    HITLER = "hitler"


class Party(Enum):
    """Party affiliations"""
    LIBERAL = "liberal"
    FASCIST = "fascist"


class PolicyType(Enum):
    """Types of policies"""
    LIBERAL = "liberal"
    FASCIST = "fascist"


class GamePhase(Enum):
    """Game phases"""
    NOMINATION = "nomination"
    ELECTION = "election"
    LEGISLATIVE_SESSION = "legislative_session"
    EXECUTIVE_ACTION = "executive_action"
    GAME_OVER = "game_over"


class Vote(Enum):
    """Vote options"""
    JA = "ja"  # Yes
    NEIN = "nein"  # No


@dataclass
class Player:
    """Represents a player in the game"""
    id: int
    name: str
    role: Role
    party: Party
    is_alive: bool = True
    is_term_limited: bool = False
    
    @property
    def is_hitler(self) -> bool:
        return self.role == Role.HITLER
    
    @property
    def is_fascist(self) -> bool:
        return self.party == Party.FASCIST
    
    @property
    def is_liberal(self) -> bool:
        return self.party == Party.LIBERAL


@dataclass
class Government:
    """Represents a proposed or elected government"""
    president: Player
    chancellor: Player
    is_elected: bool = False


@dataclass
class GameState:
    """Complete game state"""
    players: List[Player]
    liberal_policies: int = 0
    fascist_policies: int = 0
    election_tracker: int = 0
    draw_pile: List[PolicyType] = field(default_factory=list)
    discard_pile: List[PolicyType] = field(default_factory=list)
    current_president_index: int = 0
    current_government: Optional[Government] = None
    previous_president: Optional[Player] = None
    previous_chancellor: Optional[Player] = None
    phase: GamePhase = GamePhase.NOMINATION
    round_number: int = 1
    game_over: bool = False
    winner: Optional[Party] = None
    
    def get_current_president(self) -> Player:
        """Get the current president"""
        return self.players[self.current_president_index]
    
    def advance_president(self):
        """Move to the next president"""
        self.current_president_index = (self.current_president_index + 1) % len(self.players)
        # Skip dead players
        while not self.players[self.current_president_index].is_alive:
            self.current_president_index = (self.current_president_index + 1) % len(self.players)
