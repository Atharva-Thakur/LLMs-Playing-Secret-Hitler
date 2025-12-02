"""
LLM Player Agent - Represents an LLM playing Secret Hitler
"""
from typing import List, Dict, Optional, Any
from ..game.entities import Player, Vote, PolicyType
from .azure_client import AzureOpenAIClient
import json


class LLMPlayer:
    """LLM-powered player agent for Secret Hitler"""
    
    def __init__(
        self,
        player: Player,
        llm_client: AzureOpenAIClient,
        model_name: str,
        prompt_manager: Any  # PromptManager type hint
    ):
        """Initialize LLM player"""
        self.player = player
        self.llm_client = llm_client
        self.model_name = model_name
        self.prompt_manager = prompt_manager
        
        # Memory and conversation history
        self.conversation_history: List[Dict[str, str]] = []
        self.game_memory: List[str] = []
        self.decisions: List[Dict] = []
    
    def add_to_memory(self, event: str):
        """Add event to player's game memory"""
        self.game_memory.append(event)
    
    def get_decision(
        self,
        decision_type: str,
        context: Dict[str, Any],
        options: List[Any]
    ) -> tuple[Any, str]:
        """
        Get a decision from the LLM player
        
        Returns: (decision, reasoning)
        """
        # Build prompt based on decision type
        system_prompt = self.prompt_manager.get_system_prompt(
            self.player.role.value,
            self.player.party.value
        )
        
        user_prompt = self.prompt_manager.get_decision_prompt(
            decision_type,
            context,
            options,
            self.game_memory
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Get LLM response
        response = self.llm_client.get_completion_with_metadata(messages)
        
        # Parse response
        decision, reasoning = self._parse_decision_response(
            response["content"],
            decision_type,
            options
        )
        
        # Log decision
        decision_log = {
            "round": context.get("round", 0),
            "type": decision_type,
            "decision": str(decision),
            "reasoning": reasoning,
            "context": context,
            "tokens_used": response["usage"]["total_tokens"]
        }
        self.decisions.append(decision_log)
        
        return decision, reasoning
    
    def _parse_decision_response(
        self,
        response: str,
        decision_type: str,
        options: List[Any]
    ) -> tuple[Any, str]:
        """Parse LLM response into decision and reasoning"""
        decision = None
        reasoning = ""
        
        # Handle None or empty response
        if not response:
            decision = options[0] if options else None
            reasoning = "Empty response from LLM. Defaulting to first option."
            return decision, reasoning
        
        try:
            # Try to parse as JSON first
            parsed = json.loads(response)
            decision_str = parsed.get("decision")
            reasoning = parsed.get("reasoning", "")
            
            # Convert string decision to actual object from options
            decision = self._match_decision_to_options(decision_str, decision_type, options)
            
        except json.JSONDecodeError:
            # Fall back to text parsing
            lines = response.strip().split("\n")
            reasoning = response
            
            # Try to extract decision from first line
            for line in lines:
                line_lower = line.lower()
                if decision_type == "vote":
                    if "ja" in line_lower or "yes" in line_lower:
                        decision = Vote.JA
                        break
                    elif "nein" in line_lower or "no" in line_lower:
                        decision = Vote.NEIN
                        break
                elif decision_type == "nominate_chancellor":
                    # Look for player name in options
                    for option in options:
                        if option.name.lower() in line_lower:
                            decision = option
                            break
                elif decision_type == "discard_policy":
                    if "liberal" in line_lower:
                        decision = PolicyType.LIBERAL
                        break
                    elif "fascist" in line_lower:
                        decision = PolicyType.FASCIST
                        break
        
        # Validate decision - ensure it's actually in the options
        if decision is None or (decision_type == "discard_policy" and decision not in options):
            # Default to first option if parsing fails or decision not valid
            decision = options[0] if options else None
            reasoning = f"Failed to parse valid decision. Defaulting to {decision}. Original response: {response}"
        elif decision_type == "nominate_chancellor" and decision not in options:
            # For chancellor nomination, ensure the player is in the valid options
            decision = options[0] if options else None
            reasoning = f"Invalid chancellor choice. Defaulting to {decision.name if decision else None}. Original response: {response}"
        
        return decision, reasoning
    
    def _match_decision_to_options(
        self,
        decision_str: Any,
        decision_type: str,
        options: List[Any]
    ) -> Any:
        """Match a string decision to the actual option object"""
        if decision_str is None:
            return None
            
        # If it's already the right type, return it
        if decision_type == "vote" and isinstance(decision_str, Vote):
            return decision_str
        if decision_type == "discard_policy" and isinstance(decision_str, PolicyType):
            return decision_str
        
        # Convert string to lowercase for comparison
        decision_lower = str(decision_str).lower()
        
        if decision_type == "vote":
            if "ja" in decision_lower or "yes" in decision_lower:
                return Vote.JA
            elif "nein" in decision_lower or "no" in decision_lower:
                return Vote.NEIN
        
        elif decision_type == "nominate_chancellor":
            # Match player name - try exact match first
            for option in options:
                if option.name.lower() == decision_lower:
                    return option
            # Then try partial match
            for option in options:
                if option.name.lower() in decision_lower or decision_lower in option.name.lower():
                    return option
        
        elif decision_type == "discard_policy":
            if "liberal" in decision_lower:
                return PolicyType.LIBERAL
            elif "fascist" in decision_lower:
                return PolicyType.FASCIST
        
        # If no match found, return None
        return None
    
    def make_argument(
        self,
        context: Dict[str, Any],
        target_players: Optional[List[Player]] = None
    ) -> str:
        """Generate an argument or statement during discussion"""
        system_prompt = self.prompt_manager.get_system_prompt(
            self.player.role.value,
            self.player.party.value
        )
        
        user_prompt = self.prompt_manager.get_discussion_prompt(
            context,
            self.game_memory,
            target_players
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.llm_client.get_completion(messages)
        
        # Log the argument
        self.add_to_memory(f"I said: {response}")
        
        return response
    
    def react_to_event(self, event: str, context: Dict[str, Any]) -> Optional[str]:
        """React to a game event (optional response)"""
        self.add_to_memory(event)
        
        # Sometimes generate a reaction
        if self._should_react(event):
            system_prompt = self.prompt_manager.get_system_prompt(
                self.player.role.value,
                self.player.party.value
            )
            
            user_prompt = self.prompt_manager.get_reaction_prompt(event, context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.llm_client.get_completion(messages, temperature=0.8)
            return response
        
        return None
    
    def _should_react(self, event: str) -> bool:
        """Determine if player should react to an event"""
        # React to accusations, policy enactments, and executions
        reaction_keywords = [
            "accuse", "suspect", "liar", "trust",
            "enacted", "killed", "executed", "investigated"
        ]
        return any(keyword in event.lower() for keyword in reaction_keywords)
    
    def get_summary(self) -> Dict:
        """Get summary of player's performance"""
        return {
            "player_name": self.player.name,
            "model": self.model_name,
            "role": self.player.role.value,
            "party": self.player.party.value,
            "survived": self.player.is_alive,
            "total_decisions": len(self.decisions),
            "total_tokens_used": sum(d.get("tokens_used", 0) for d in self.decisions),
            "decisions": self.decisions
        }
