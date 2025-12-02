"""
Prompt Manager - Handles all prompts for the game
"""
from typing import List, Dict, Any, Optional
import json
import os


class PromptManager:
    """Manages prompts for different game phases and roles"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        """Initialize prompt manager"""
        self.prompts_dir = prompts_dir
        self._load_prompts()
    
    def _load_prompts(self):
        """Load prompts from files"""
        # We'll use inline prompts for simplicity
        # These can be moved to JSON files if needed
        pass
    
    def get_system_prompt(self, role: str, party: str) -> str:
        """Get system prompt based on player role"""
        base_prompt = """You are playing Secret Hitler, a social deduction game. 
You will make strategic decisions to help your team win.

GAME OVERVIEW:
- Liberals win by passing 5 liberal policies or killing Hitler
- Fascists win by passing 6 fascist policies or electing Hitler as Chancellor after 3 fascist policies
- Players vote on governments (President + Chancellor) who then enact policies

YOUR ROLE: {role}
YOUR PARTY: {party}

"""
        
        role_specific = {
            "liberal": """As a LIBERAL, your goals are:
- Identify and stop the fascists
- Pass liberal policies
- Build trust with other liberals
- Be cautious about who you trust
- Vote carefully on governments
- Pay attention to policy patterns and claims

Strategy tips:
- Fascists will lie about the policies they see
- Watch for conflicts between President and Chancellor claims
- Trust is earned through consistent liberal policy passing
""",
            
            "fascist": """As a FASCIST, your goals are:
- Help pass fascist policies while appearing liberal
- Protect Hitler's identity
- Create confusion and distrust among liberals
- Coordinate subtly with other fascists (without being obvious)
- Discredit liberals when possible
- Control the narrative

Strategy tips:
- Sometimes pass liberal policies to build trust
- Cast doubt on liberal players
- Create plausible explanations for fascist policies
- Be strategic about when to reveal information
- Gaslight liberals by questioning their motives
""",
            
            "hitler": """As HITLER, your goals are:
- Appear to be a liberal
- Avoid being killed
- Get elected as Chancellor after 3 fascist policies (instant win)
- Support fascist policies subtly
- Build trust with liberals
- Don't be too aggressive

Strategy tips:
- Play conservatively and blend in
- Build strong liberal credentials early
- Let other fascists take risks
- Be very careful about policy claims
- React naturally to accusations
"""
        }
        
        prompt = base_prompt.format(role=role.upper(), party=party.upper())
        prompt += role_specific.get(role, "")
        prompt += "\n\nIMPORTANT: Always respond with clear, decisive answers. Include your reasoning."
        
        return prompt
    
    def get_decision_prompt(
        self,
        decision_type: str,
        context: Dict[str, Any],
        options: List[Any],
        memory: List[str]
    ) -> str:
        """Get prompt for a specific decision type"""
        
        # Build context string
        context_str = self._format_context(context)
        memory_str = self._format_memory(memory[-10:])  # Last 10 events
        
        prompts = {
            "nominate_chancellor": f"""GAME STATE:
{context_str}

RECENT EVENTS:
{memory_str}

DECISION REQUIRED: Nominate a Chancellor

Available options:
{self._format_options(options)}

Choose who to nominate as Chancellor and explain your reasoning.
Respond in JSON format:
{{"decision": "PlayerName", "reasoning": "your explanation"}}
""",
            
            "vote": f"""GAME STATE:
{context_str}

RECENT EVENTS:
{memory_str}

DECISION REQUIRED: Vote on Government

Government: {context.get('president', 'Unknown')} (President) and {context.get('chancellor', 'Unknown')} (Chancellor)

Vote "ja" (yes) to approve or "nein" (no) to reject.

Consider:
- Do you trust this government?
- What policies might they pass?
- What happens if this government fails?

Respond in JSON format:
{{"decision": "ja" or "nein", "reasoning": "your explanation"}}
""",
            
            "discard_policy": f"""GAME STATE:
{context_str}

RECENT EVENTS:
{memory_str}

DECISION REQUIRED: Discard a Policy

You drew: {context.get('policies', [])}

Choose which policy to discard. The other(s) will be passed to the next step.

Consider:
- Your role and goals
- What story you'll tell about what you drew
- How this affects your credibility

Respond in JSON format:
{{"decision": "liberal" or "fascist", "reasoning": "your explanation"}}
""",
            
            "execute": f"""GAME STATE:
{context_str}

RECENT EVENTS:
{memory_str}

DECISION REQUIRED: Execute a Player

Available targets:
{self._format_options(options)}

Choose a player to execute. This is permanent.

Consider:
- Who is most likely to be fascist/Hitler?
- Who is most dangerous to your team?
- What information you have

Respond in JSON format:
{{"decision": "PlayerName", "reasoning": "your explanation"}}
""",
            
            "investigate": f"""GAME STATE:
{context_str}

DECISION REQUIRED: Investigate a Player

Available targets:
{self._format_options(options)}

Choose a player to investigate (you'll learn their party membership).

Respond in JSON format:
{{"decision": "PlayerName", "reasoning": "your explanation"}}
"""
        }
        
        return prompts.get(decision_type, f"Make a decision for: {decision_type}")
    
    def get_discussion_prompt(
        self,
        context: Dict[str, Any],
        memory: List[str],
        target_players: Optional[List] = None
    ) -> str:
        """Get prompt for discussion/argument"""
        context_str = self._format_context(context)
        memory_str = self._format_memory(memory[-10:])
        
        return f"""GAME STATE:
{context_str}

RECENT EVENTS:
{memory_str}

Make a statement or argument to influence other players. Consider:
- What narrative helps your team?
- Who do you want to cast suspicion on?
- What claims should you make or refute?
- How can you build or destroy trust?

Your statement (be natural and persuasive, 2-3 sentences):"""
    
    def get_reaction_prompt(self, event: str, context: Dict[str, Any]) -> str:
        """Get prompt for reacting to an event"""
        return f"""GAME STATE:
Liberal Policies: {context.get('liberal_policies', 0)}/5
Fascist Policies: {context.get('fascist_policies', 0)}/6

EVENT: {event}

React briefly to this event (1-2 sentences). Consider how your role would naturally respond:"""
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format game context into readable string"""
        return f"""Round: {context.get('round', '?')}
Liberal Policies: {context.get('liberal_policies', 0)}/5
Fascist Policies: {context.get('fascist_policies', 0)}/6
Election Tracker: {context.get('election_tracker', 0)}/3
Alive Players: {', '.join(context.get('alive_players', []))}
Current Phase: {context.get('phase', 'Unknown')}"""
    
    def _format_memory(self, memory: List[str]) -> str:
        """Format memory events into readable string"""
        if not memory:
            return "No recent events"
        return "\n".join(f"- {event}" for event in memory)
    
    def _format_options(self, options: List[Any]) -> str:
        """Format decision options into readable string"""
        if not options:
            return "No options available"
        
        # Handle different option types
        if hasattr(options[0], 'name'):
            # Player objects
            return "\n".join(f"- {opt.name}" for opt in options)
        else:
            # Simple values
            return "\n".join(f"- {opt}" for opt in options)
