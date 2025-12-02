"""
Game engine for Secret Hitler - manages game flow and state
"""
import random
from typing import List, Optional, Tuple
from .entities import (
    Player, GameState, Government, GamePhase,
    Vote, PolicyType, Party, Role
)
from .rules import GameConfig


class SecretHitlerGame:
    """Main game engine for Secret Hitler"""
    
    def __init__(self, player_names: List[str]):
        """Initialize a new game with given player names"""
        if len(player_names) < 5 or len(player_names) > 10:
            raise ValueError("Secret Hitler requires 5-10 players")
        
        self.num_players = len(player_names)
        self.state = self._initialize_game(player_names)
    
    def _initialize_game(self, player_names: List[str]) -> GameState:
        """Set up initial game state"""
        # Assign roles
        roles = GameConfig.get_roles_for_player_count(len(player_names))
        
        # Create players
        players = []
        for i, (name, role) in enumerate(zip(player_names, roles)):
            party = GameConfig.get_party_from_role(role)
            players.append(Player(id=i, name=name, role=role, party=party))
        
        # Create draw pile
        draw_pile = GameConfig.create_initial_draw_pile()
        
        # Random starting president
        starting_president = random.randint(0, len(players) - 1)
        
        return GameState(
            players=players,
            draw_pile=draw_pile,
            current_president_index=starting_president
        )
    
    def get_eligible_chancellors(self) -> List[Player]:
        """Get list of players eligible to be chancellor"""
        president = self.state.get_current_president()
        eligible = []
        
        for player in self.state.players:
            if not player.is_alive:
                continue
            if player.id == president.id:
                continue
            if player.is_term_limited:
                continue
            # Previous government members are term-limited
            if self.state.previous_chancellor and player.id == self.state.previous_chancellor.id:
                continue
            if self.state.previous_president and player.id == self.state.previous_president.id:
                # Only in games with more than 5 players
                if self.num_players > 5:
                    continue
            
            eligible.append(player)
        
        return eligible
    
    def nominate_chancellor(self, chancellor: Player) -> Government:
        """President nominates a chancellor"""
        if chancellor not in self.get_eligible_chancellors():
            raise ValueError(f"{chancellor.name} is not eligible to be chancellor")
        
        president = self.state.get_current_president()
        government = Government(president=president, chancellor=chancellor)
        self.state.current_government = government
        self.state.phase = GamePhase.ELECTION
        
        return government
    
    def conduct_election(self, votes: List[Vote]) -> bool:
        """Conduct election with player votes. Returns True if government elected."""
        if len(votes) != len(self.state.players):
            raise ValueError("Must have vote from each player")
        
        ja_votes = sum(1 for v in votes if v == Vote.JA)
        nein_votes = len(votes) - ja_votes
        
        elected = ja_votes > nein_votes
        
        if elected:
            self.state.current_government.is_elected = True
            self.state.election_tracker = 0
            
            # Check Hitler win condition (3+ fascist policies and Hitler elected chancellor)
            if (self.state.fascist_policies >= 3 and 
                self.state.current_government.chancellor.is_hitler):
                self._end_game(Party.FASCIST)
                return True
            
            # Clear term limits
            for player in self.state.players:
                player.is_term_limited = False
            
            self.state.phase = GamePhase.LEGISLATIVE_SESSION
        else:
            self.state.election_tracker += 1
            
            # Check election tracker
            if self.state.election_tracker >= GameConfig.ELECTION_TRACKER_MAX:
                self._chaos_policy()
                self.state.election_tracker = 0
            
            # Move to next president
            self._advance_to_next_government()
        
        return elected
    
    def president_discard_policy(self, policies: List[PolicyType], discarded: PolicyType) -> List[PolicyType]:
        """President discards one of three policies, passes two to chancellor"""
        if len(policies) != 3:
            raise ValueError("President must receive exactly 3 policies")
        if discarded not in policies:
            raise ValueError("Discarded policy must be one of the drawn policies")
        
        remaining = [p for p in policies if p != discarded or policies.count(p) > 1]
        if discarded in remaining:
            remaining.remove(discarded)
        
        self.state.discard_pile.append(discarded)
        return remaining
    
    def chancellor_enact_policy(self, policies: List[PolicyType], enacted: PolicyType) -> str | None:
        """Chancellor enacts one of two policies. Returns executive action if any."""
        if len(policies) != 2:
            raise ValueError("Chancellor must receive exactly 2 policies")
        if enacted not in policies:
            raise ValueError("Enacted policy must be one of the received policies")
        
        # Discard the other policy
        # Handle case where both policies are the same type
        remaining = policies.copy()
        remaining.remove(enacted)  # Remove one instance of the enacted policy
        if remaining:
            discarded = remaining[0]
        else:
            # Both policies were the same, discard the same type
            discarded = enacted
        self.state.discard_pile.append(discarded)
        
        # Enact policy
        if enacted == PolicyType.LIBERAL:
            self.state.liberal_policies += 1
            if self.state.liberal_policies >= GameConfig.LIBERAL_POLICIES_TO_WIN:
                self._end_game(Party.LIBERAL)
        else:
            self.state.fascist_policies += 1
            if self.state.fascist_policies >= GameConfig.FASCIST_POLICIES_TO_WIN:
                self._end_game(Party.FASCIST)
        
        # Set term limits
        self.state.previous_president = self.state.current_government.president
        self.state.previous_chancellor = self.state.current_government.chancellor
        self.state.current_government.chancellor.is_term_limited = True
        
        # Check for executive action
        executive_action = None
        if enacted == PolicyType.FASCIST:
            executive_action = GameConfig.get_executive_action(
                self.num_players, 
                self.state.fascist_policies
            )
            if executive_action:
                self.state.phase = GamePhase.EXECUTIVE_ACTION
                return executive_action
        
        # Move to next round
        self._advance_to_next_government()
        
        return executive_action
    
    def draw_policies(self, count: int = 3) -> List[PolicyType]:
        """Draw policies from the deck"""
        # Reshuffle if needed
        if len(self.state.draw_pile) < count:
            self.state.draw_pile.extend(self.state.discard_pile)
            self.state.discard_pile.clear()
            random.shuffle(self.state.draw_pile)
        
        drawn = self.state.draw_pile[:count]
        self.state.draw_pile = self.state.draw_pile[count:]
        
        return drawn
    
    def execute_player(self, target: Player):
        """Execute a player (executive action)"""
        target.is_alive = False
        
        # Check if Hitler was killed
        if target.is_hitler:
            self._end_game(Party.LIBERAL)
        
        self._advance_to_next_government()
    
    def investigate_player(self, target: Player) -> Party:
        """Investigate a player's party membership"""
        self._advance_to_next_government()
        return target.party
    
    def peek_policies(self) -> List[PolicyType]:
        """Peek at top 3 policies"""
        policies = self.state.draw_pile[:3] if len(self.state.draw_pile) >= 3 else self.state.draw_pile
        self._advance_to_next_government()
        return policies
    
    def special_election(self, nominee: Player):
        """Conduct special election with nominated president"""
        # Next president will be the nominee
        self.state.current_president_index = nominee.id
        self.state.phase = GamePhase.NOMINATION
        self.state.round_number += 1
    
    def _chaos_policy(self):
        """Enact top policy due to failed elections"""
        policy = self.draw_policies(1)[0]
        
        if policy == PolicyType.LIBERAL:
            self.state.liberal_policies += 1
            if self.state.liberal_policies >= GameConfig.LIBERAL_POLICIES_TO_WIN:
                self._end_game(Party.LIBERAL)
        else:
            self.state.fascist_policies += 1
            if self.state.fascist_policies >= GameConfig.FASCIST_POLICIES_TO_WIN:
                self._end_game(Party.FASCIST)
    
    def _advance_to_next_government(self):
        """Move to next round with new president"""
        self.state.advance_president()
        self.state.current_government = None
        self.state.phase = GamePhase.NOMINATION
        self.state.round_number += 1
    
    def _end_game(self, winner: Party):
        """End the game with a winner"""
        self.state.game_over = True
        self.state.winner = winner
        self.state.phase = GamePhase.GAME_OVER
    
    def get_game_info_for_player(self, player: Player) -> dict:
        """Get game information visible to a specific player"""
        info = {
            "player_name": player.name,
            "role": player.role.value,
            "party": player.party.value,
            "liberal_policies": self.state.liberal_policies,
            "fascist_policies": self.state.fascist_policies,
            "election_tracker": self.state.election_tracker,
            "alive_players": [p.name for p in self.state.players if p.is_alive],
            "phase": self.state.phase.value,
            "round": self.state.round_number,
        }
        
        # Fascists know each other
        if player.is_fascist:
            fascists = [p.name for p in self.state.players if p.is_fascist]
            hitler_name = next(p.name for p in self.state.players if p.is_hitler)
            info["fascist_team"] = fascists
            info["hitler"] = hitler_name
        
        # Hitler knows fascists in games with 7+ players
        if player.is_hitler and self.num_players >= 7:
            fascists = [p.name for p in self.state.players if p.role == Role.FASCIST]
            info["fascist_team"] = fascists
        
        return info
