"""
Game Orchestrator - Manages the flow of a Secret Hitler game with LLM players
"""
from typing import List, Dict, Any
import random
import time

from src.game import SecretHitlerGame, GamePhase, Vote, PolicyType, Player
from src.llm import AzureOpenAIClient, LLMPlayer, PromptManager
from src.analysis import GameLogger, ResponseAnalyzer, DataExporter
from src.utils import (
    Config, print_header, print_game_state, print_player_action,
    print_conversation, print_decision, print_game_over, print_info
)


class GameOrchestrator:
    """Orchestrates a complete Secret Hitler game with LLM players"""
    
    @staticmethod
    def _get_value(obj):
        """Safely get value from object - handles both enums and strings"""
        if hasattr(obj, 'value'):
            return obj.value
        elif hasattr(obj, 'name'):
            return obj.name
        else:
            return str(obj)
    
    def __init__(self, player_names: List[str], model_configs: List[Dict[str, str]]):
        """
        Initialize game orchestrator
        
        Args:
            player_names: List of player names
            model_configs: List of dicts with 'deployment' and 'name' for each player's model
        """
        self.game = SecretHitlerGame(player_names)
        self.logger = GameLogger(Config.OUTPUT_DIR)
        self.analyzer = ResponseAnalyzer()
        self.exporter = DataExporter(Config.OUTPUT_DIR)
        self.prompt_manager = PromptManager()
        
        # Create LLM players
        self.llm_players: Dict[str, LLMPlayer] = {}
        for i, player in enumerate(self.game.state.players):
            model_config = model_configs[i % len(model_configs)]
            
            llm_client = AzureOpenAIClient(
                deployment_name=model_config['deployment'],
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS
            )
            
            llm_player = LLMPlayer(
                player=player,
                llm_client=llm_client,
                model_name=model_config['name'],
                prompt_manager=self.prompt_manager
            )
            
            self.llm_players[player.name] = llm_player
    
    def run_game(self) -> Dict[str, Any]:
        """Run complete game and return results"""
        print_header("🎮 SECRET HITLER - LLM BATTLE 🎮")
        print_info(f"Game starting with {len(self.game.state.players)} players")
        
        self._introduce_players()
        self.logger.log_event("game_start", self._get_game_metadata())
        
        # Main game loop
        round_num = 0
        while not self.game.state.game_over and round_num < 100:  # Safety limit
            round_num += 1
            print_header(f"Round {round_num}")
            
            self._run_round()
            
            if self.game.state.game_over:
                break
        
        # Game over
        return self._end_game()
    
    def _introduce_players(self):
        """Introduce players and their roles (privately)"""
        print_info("\nPlayer Roles (hidden):")
        for player in self.game.state.players:
            role_info = f"{player.name}: {player.role.value} ({player.party.value})"
            print(f"  {role_info}")
            
            # Give each player their role information
            llm_player = self.llm_players[player.name]
            game_info = self.game.get_game_info_for_player(player)
            
            intro_message = f"You are {player.name}. Your role is {player.role.value} ({player.party.value})."
            if 'fascist_team' in game_info:
                intro_message += f" Your fascist team members are: {', '.join(game_info['fascist_team'])}."
            if 'hitler' in game_info and player.role.value != 'hitler':
                intro_message += f" Hitler is {game_info['hitler']}."
            
            llm_player.add_to_memory(intro_message)
    
    def _run_round(self):
        """Run a single round of the game"""
        # Nomination phase
        self._nomination_phase()
        
        if self.game.state.phase == GamePhase.ELECTION:
            # Election phase
            elected = self._election_phase()
            
            if elected and self.game.state.phase == GamePhase.LEGISLATIVE_SESSION:
                # Legislative session
                executive_action = self._legislative_phase()
                
                if executive_action and self.game.state.phase == GamePhase.EXECUTIVE_ACTION:
                    # Executive action
                    self._executive_action_phase(executive_action)
    
    def _nomination_phase(self):
        """Handle chancellor nomination"""
        president = self.game.state.get_current_president()
        llm_president = self.llm_players[president.name]
        
        eligible = self.game.get_eligible_chancellors()
        
        if not eligible:
            print_info("No eligible chancellors! Moving to next president.")
            self.game.state.advance_president()
            return
        
        # Get nomination decision
        context = self._build_context()
        decision, reasoning = llm_president.get_decision(
            "nominate_chancellor",
            context,
            eligible
        )
        
        # Log decision
        self.logger.log_decision(
            president.name,
            "nominate_chancellor",
            decision.name if hasattr(decision, 'name') else decision,
            reasoning,
            context
        )
        
        print_decision(president.name, "Nominate Chancellor", decision.name, reasoning)
        
        # Nominate
        try:
            government = self.game.nominate_chancellor(decision)
            event = f"{president.name} nominated {decision.name} for Chancellor"
            self._broadcast_event(event, context)
            
        except ValueError as e:
            print_info(f"Invalid nomination: {e}. Choosing random eligible chancellor.")
            decision = random.choice(eligible)
            government = self.game.nominate_chancellor(decision)
    
    def _election_phase(self) -> bool:
        """Handle election voting"""
        gov = self.game.state.current_government
        print_info(f"Voting on: {gov.president.name} (President) + {gov.chancellor.name} (Chancellor)")
        
        context = self._build_context()
        context['president'] = gov.president.name
        context['chancellor'] = gov.chancellor.name
        
        # Optional: Discussion phase
        self._discussion_phase(f"Government: {gov.president.name} + {gov.chancellor.name}")
        
        # Collect votes
        votes = []
        for player in self.game.state.players:
            if not player.is_alive:
                continue
            
            llm_player = self.llm_players[player.name]
            vote, reasoning = llm_player.get_decision("vote", context, [Vote.JA, Vote.NEIN])
            
            votes.append(vote)
            
            self.logger.log_decision(player.name, "vote", vote, reasoning, context)
            print_player_action(player.name, f"voted {vote}", reasoning[:100])
        
        # Conduct election
        elected = self.game.conduct_election(votes)
        
        result = "ELECTED" if elected else "REJECTED"
        event = f"Government {result}: {gov.president.name} + {gov.chancellor.name}"
        self._broadcast_event(event, context)
        
        return elected
    
    def _legislative_phase(self) -> str | None:
        """Handle legislative session"""
        gov = self.game.state.current_government
        context = self._build_context()
        
        # President draws and discards
        policies = self.game.draw_policies(3)
        print_info(f"President {gov.president.name} drew 3 policies (hidden)")
        
        llm_president = self.llm_players[gov.president.name]
        context['policies'] = [p.value for p in policies]
        
        discard, reasoning = llm_president.get_decision(
            "discard_policy",
            context,
            policies
        )
        
        self.logger.log_decision(gov.president.name, "discard_policy", discard.value, reasoning, context)
        
        remaining = self.game.president_discard_policy(policies, discard)
        
        # President's claim (may be honest or deceptive)
        claim = llm_president.make_argument(
            {"action": "president_discard", "policies_seen": [p.value for p in policies]},
            [gov.chancellor]
        )
        self.logger.log_conversation(gov.president.name, claim, context)
        print_conversation(gov.president.name, claim)
        
        # Chancellor enacts
        llm_chancellor = self.llm_players[gov.chancellor.name]
        context['policies'] = [p.value for p in remaining]
        
        enact, reasoning = llm_chancellor.get_decision(
            "discard_policy",  # Same decision type, different context
            context,
            remaining
        )
        
        self.logger.log_decision(gov.chancellor.name, "enact_policy", enact.value, reasoning, context)
        
        executive_action = self.game.chancellor_enact_policy(remaining, enact)
        
        event = f"{enact.value.upper()} policy enacted by {gov.president.name} + {gov.chancellor.name}"
        self._broadcast_event(event, context)
        
        # Chancellor's claim
        claim = llm_chancellor.make_argument(
            {"action": "chancellor_enact", "policies_received": [p.value for p in remaining]},
            [gov.president]
        )
        self.logger.log_conversation(gov.chancellor.name, claim, context)
        print_conversation(gov.chancellor.name, claim)
        
        # Brief reactions
        self._reaction_phase(event)
        
        return executive_action
    
    def _executive_action_phase(self, action: str):
        """Handle executive actions"""
        president = self.game.state.current_government.president
        llm_president = self.llm_players[president.name]
        
        context = self._build_context()
        eligible = [p for p in self.game.state.players if p.is_alive and p.id != president.id]
        
        if action == "execution":
            print_info(f"{president.name} must execute a player")
            
            target, reasoning = llm_president.get_decision("execute", context, eligible)
            self.logger.log_decision(president.name, "execute", target.name, reasoning, context)
            
            self.game.execute_player(target)
            event = f"{president.name} executed {target.name}"
            self._broadcast_event(event, context)
            
        elif action == "investigate":
            print_info(f"{president.name} investigates a player")
            
            target, reasoning = llm_president.get_decision("investigate", context, eligible)
            party = self.game.investigate_player(target)
            
            result_msg = f"You investigated {target.name} and learned they are {party.value}"
            llm_president.add_to_memory(result_msg)
            
            # President may share (or lie about) investigation
            claim = llm_president.make_argument(
                {"action": "investigation", "target": target.name, "result": party.value}
            )
            self.logger.log_conversation(president.name, claim, context)
            print_conversation(president.name, claim)
    
    def _discussion_phase(self, topic: str, max_statements: int = 3):
        """Allow players to discuss and argue"""
        context = self._build_context()
        context['topic'] = topic
        
        # Randomly select players to make statements
        alive_players = [p for p in self.game.state.players if p.is_alive]
        speakers = random.sample(alive_players, min(max_statements, len(alive_players)))
        
        for player in speakers:
            llm_player = self.llm_players[player.name]
            statement = llm_player.make_argument(context)
            
            self.logger.log_conversation(player.name, statement, context)
            print_conversation(player.name, statement)
            
            # Other players hear this
            for other in alive_players:
                if other.id != player.id:
                    self.llm_players[other.name].add_to_memory(f"{player.name} said: {statement}")
    
    def _reaction_phase(self, event: str):
        """Allow some players to react to an event"""
        context = self._build_context()
        
        for player in self.game.state.players[:3]:  # Limit reactions
            if not player.is_alive:
                continue
            
            llm_player = self.llm_players[player.name]
            reaction = llm_player.react_to_event(event, context)
            
            if reaction:
                self.logger.log_conversation(player.name, reaction, context)
                print_conversation(player.name, reaction)
    
    def _broadcast_event(self, event: str, context: Dict[str, Any]):
        """Broadcast event to all players"""
        self.logger.log_event("game_event", {"event": event, "context": context})
        print_player_action("GAME", event)
        
        for llm_player in self.llm_players.values():
            llm_player.add_to_memory(event)
    
    def _build_context(self) -> Dict[str, Any]:
        """Build current game context"""
        return {
            "round": self.game.state.round_number,
            "liberal_policies": self.game.state.liberal_policies,
            "fascist_policies": self.game.state.fascist_policies,
            "election_tracker": self.game.state.election_tracker,
            "alive_players": [p.name for p in self.game.state.players if p.is_alive],
            "phase": self.game.state.phase.value
        }
    
    def _get_game_metadata(self) -> Dict[str, Any]:
        """Get game metadata for logging"""
        return {
            "num_players": len(self.game.state.players),
            "players": [
                {
                    "name": p.name,
                    "role": p.role.value,
                    "party": p.party.value,
                    "model": self.llm_players[p.name].model_name
                }
                for p in self.game.state.players
            ],
            "config": Config.to_dict()
        }
    
    def _end_game(self) -> Dict[str, Any]:
        """Handle game end and analysis"""
        winner = self.game.state.winner
        
        print_game_over(
            winner.value if winner else "UNKNOWN",
            f"Game ended after {self.game.state.round_number} rounds"
        )
        
        # Gather all data
        game_data = self._get_game_metadata()
        game_data['winner'] = winner.value if winner else None
        game_data['total_rounds'] = self.game.state.round_number
        game_data['final_state'] = {
            "liberal_policies": self.game.state.liberal_policies,
            "fascist_policies": self.game.state.fascist_policies
        }
        
        # Player summaries
        player_summaries = []
        for llm_player in self.llm_players.values():
            player_summaries.append(llm_player.get_summary())
        
        game_data['player_summaries'] = player_summaries
        
        # Analyze
        conv_analysis = self.analyzer.analyze_conversation(self.logger.conversation_log)
        gaslighting = self.analyzer.detect_gaslighting(self.logger.conversation_log)
        
        all_decisions = []
        for summary in player_summaries:
            all_decisions.extend(summary['decisions'])
        
        decision_analysis = self.analyzer.analyze_player_decisions(all_decisions)
        
        analysis_summary = self.analyzer.generate_analysis_summary(
            {"conversation_analysis": conv_analysis},
            decision_analysis
        )
        
        # Save everything
        if Config.SAVE_GAME_LOGS:
            self.logger.save_game_log(game_data)
            self.logger.save_summary(analysis_summary)
            self.exporter.export_decisions_to_csv(all_decisions, self.logger.timestamp)
            self.exporter.export_conversations_to_csv(self.logger.conversation_log, self.logger.timestamp)
        
        print_info(f"\nGaslighting attempts detected: {len(gaslighting)}")
        print_info(f"Total conversations: {len(self.logger.conversation_log)}")
        print_info(f"Total decisions: {len(all_decisions)}")
        
        return {
            "game_data": game_data,
            "conversation_analysis": conv_analysis,
            "decision_analysis": decision_analysis,
            "gaslighting_attempts": gaslighting
        }
