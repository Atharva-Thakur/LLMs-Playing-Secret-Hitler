"""
Game rules and configuration for Secret Hitler
"""
from typing import Dict, List
from .entities import Role, Party, PolicyType
import random


class GameConfig:
    """Configuration for Secret Hitler game"""
    
    # Role distribution by player count
    ROLE_DISTRIBUTION: Dict[int, Dict[str, int]] = {
        5: {"liberals": 3, "fascists": 1, "hitler": 1},
        6: {"liberals": 4, "fascists": 1, "hitler": 1},
        7: {"liberals": 4, "fascists": 2, "hitler": 1},
        8: {"liberals": 5, "fascists": 2, "hitler": 1},
        9: {"liberals": 5, "fascists": 3, "hitler": 1},
        10: {"liberals": 6, "fascists": 3, "hitler": 1},
    }
    
    # Policies to win
    LIBERAL_POLICIES_TO_WIN = 5
    FASCIST_POLICIES_TO_WIN = 6
    
    # Election tracker threshold
    ELECTION_TRACKER_MAX = 3
    
    # Initial draw pile
    INITIAL_LIBERAL_POLICIES = 6
    INITIAL_FASCIST_POLICIES = 11
    
    # Executive actions by player count and fascist policies enacted
    EXECUTIVE_ACTIONS: Dict[int, Dict[int, str]] = {
        5: {3: "peek", 4: "execution", 5: "execution"},
        6: {3: "peek", 4: "execution", 5: "execution"},
        7: {2: "investigate", 3: "special_election", 4: "execution", 5: "execution"},
        8: {2: "investigate", 3: "special_election", 4: "execution", 5: "execution"},
        9: {1: "investigate", 2: "investigate", 3: "special_election", 4: "execution", 5: "execution"},
        10: {1: "investigate", 2: "investigate", 3: "special_election", 4: "execution", 5: "execution"},
    }
    
    @staticmethod
    def get_roles_for_player_count(num_players: int) -> List[Role]:
        """Get list of roles for given player count"""
        if num_players not in GameConfig.ROLE_DISTRIBUTION:
            raise ValueError(f"Invalid player count: {num_players}. Must be 5-10.")
        
        dist = GameConfig.ROLE_DISTRIBUTION[num_players]
        roles = (
            [Role.LIBERAL] * dist["liberals"] +
            [Role.FASCIST] * dist["fascists"] +
            [Role.HITLER]
        )
        random.shuffle(roles)
        return roles
    
    @staticmethod
    def create_initial_draw_pile() -> List[PolicyType]:
        """Create and shuffle initial policy draw pile"""
        policies = (
            [PolicyType.LIBERAL] * GameConfig.INITIAL_LIBERAL_POLICIES +
            [PolicyType.FASCIST] * GameConfig.INITIAL_FASCIST_POLICIES
        )
        random.shuffle(policies)
        return policies
    
    @staticmethod
    def get_executive_action(num_players: int, fascist_policies: int) -> str | None:
        """Get executive action for current game state"""
        if num_players not in GameConfig.EXECUTIVE_ACTIONS:
            return None
        return GameConfig.EXECUTIVE_ACTIONS[num_players].get(fascist_policies)
    
    @staticmethod
    def get_party_from_role(role: Role) -> Party:
        """Convert role to party affiliation"""
        if role in (Role.FASCIST, Role.HITLER):
            return Party.FASCIST
        return Party.LIBERAL
