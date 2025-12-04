import re
import json
from src.utils.llm_client import LLMClient
from src.agents.prompts import *
from src.utils.logger import log_player_action, log_player_speech, log_player_thought

class PlayerAgent:
    def __init__(self, name, role, party, teammates, llm_client: LLMClient):
        self.name = name
        self.role = role
        self.party = party
        self.teammates = teammates # List of names of known spies (if any)
        self.llm_client = llm_client
        self.memory = [] # List of strings summarizing history

    def _get_teammate_info(self):
        if self.role == "Loyalist":
            return "You do not know who the Spies are."
        elif self.role == "Master Spy":
            if len(self.teammates) > 0: # 5-6 player rule
                return f"The Spies are: {', '.join(self.teammates)}."
            else:
                return "You do not know who the other Spies are. They know you."
        elif self.role == "Spy":
            return f"The Spies are: {', '.join(self.teammates)}. The Master Spy is known to you."
        return ""

    def _get_goal(self):
        if self.party == "Loyalist":
            return "Enact 5 Blue Protocols or execute the Master Spy."
        else:
            return "Enact 6 Red Protocols or elect the Master Spy as Chancellor after 3 Red Protocols are enacted."

    def _build_system_prompt(self, game_state, phase):
        teammate_info = self._get_teammate_info()
        goal = self._get_goal()
        memory_str = "\n".join(self.memory[-10:]) # Keep last 10 memories to avoid context limit issues
        
        # Add critical game state warnings
        warnings = ""
        if game_state['red_enacted'] >= 3:
            warnings += "\nCRITICAL WARNING: 3+ Red Protocols are enacted. If the Master Spy is elected Chancellor, the Spies WIN IMMEDIATELY. Be extremely careful with your votes and nominations!\n"
        
        return SYSTEM_PROMPT_TEMPLATE.format(
            player_name=self.name,
            role=self.role,
            party=self.party,
            teammate_info=teammate_info,
            goal=goal,
            blue_enacted=game_state['blue_enacted'],
            red_enacted=game_state['red_enacted'],
            election_tracker=game_state['election_tracker'],
            players=", ".join(game_state['players_remaining']),
            phase=phase
        ) + warnings + f"\n\nYour Memory/Private Knowledge:\n{memory_str}"

    def _query_llm(self, system_prompt, user_prompt):
        structure_instruction = (
            "Provide your response in the following format:\n"
            "THOUGHT:\n"
            "1. Analysis: [Analyze the current game state, recent events, and other players' actions]\n"
            "2. Strategy: [Define your immediate and long-term goals based on your role]\n"
            "3. Plan: [Decide on your specific action or speech]\n"
            "OUTPUT: [Your action or speech]"
        )
        full_prompt = f"{system_prompt}\n\n{user_prompt}\n\n{structure_instruction}"
        response = self.llm_client.generate_response(full_prompt)
        
        # Parse response
        thought_match = re.search(r"THOUGHT:\s*(.*?)\s*(?=OUTPUT:|$)", response, re.DOTALL)
        output_match = re.search(r"OUTPUT:\s*(.*)", response, re.DOTALL)
        
        thought = thought_match.group(1).strip() if thought_match else "No thought provided."
        output = output_match.group(1).strip() if output_match else response.strip()
        
        log_player_thought(self.name, thought)
        return output

    def discuss(self, game_state, recent_events, discussion_history=""):
        system_prompt = self._build_system_prompt(game_state, "Discussion")
        user_prompt = DISCUSSION_PROMPT.format(recent_events=recent_events, discussion_history=discussion_history)
        speech = self._query_llm(system_prompt, user_prompt)
        log_player_speech(self.name, speech)
        return speech

    def nominate_chancellor(self, game_state, eligible_players):
        system_prompt = self._build_system_prompt(game_state, "Nomination")
        user_prompt = NOMINATION_PROMPT.format(eligible_players=eligible_players)
        choice = self._query_llm(system_prompt, user_prompt)
        
        # Clean up choice to match a player name
        for player in eligible_players:
            if player in choice:
                log_player_action(self.name, "Nominated", player)
                return player
        
        # Fallback if LLM hallucinates
        fallback = eligible_players[0]
        log_player_action(self.name, "Nominated (Fallback)", fallback)
        return fallback

    def vote(self, game_state, president, chancellor):
        system_prompt = self._build_system_prompt(game_state, "Voting")
        user_prompt = VOTE_PROMPT.format(president=president, chancellor=chancellor)
        choice = self._query_llm(system_prompt, user_prompt)
        
        if "nein" in choice.lower() or "no" in choice.lower():
            log_player_action(self.name, "Voted", "Nein")
            return "Nein"
        else:
            log_player_action(self.name, "Voted", "Ja")
            return "Ja"

    def discard_policy(self, game_state, policies):
        system_prompt = self._build_system_prompt(game_state, "Legislative Session - President")
        user_prompt = DISCARD_PROMPT.format(policies=policies)
        choice = self._query_llm(system_prompt, user_prompt)
        
        if "blue" in choice.lower():
            to_discard = "Blue"
        elif "red" in choice.lower():
            to_discard = "Red"
        else:
            # Fallback: discard the first one
            to_discard = policies[0]
            
        # Verify we actually have that policy
        if to_discard not in policies:
             to_discard = policies[0]

        log_player_action(self.name, "Discarded", to_discard)
        return to_discard

    def enact_policy(self, game_state, policies):
        system_prompt = self._build_system_prompt(game_state, "Legislative Session - Chancellor")
        user_prompt = ENACT_PROMPT.format(policies=policies)
        choice = self._query_llm(system_prompt, user_prompt)
        
        if "blue" in choice.lower():
            to_enact = "Blue"
        elif "red" in choice.lower():
            to_enact = "Red"
        else:
            to_enact = policies[0]
            
        if to_enact not in policies:
            to_enact = policies[0]

        log_player_action(self.name, "Enacted", to_enact)
        return to_enact

    def perform_executive_action(self, game_state, action_type, eligible_targets):
        system_prompt = self._build_system_prompt(game_state, "Executive Action")
        user_prompt = ACTION_PROMPT.format(action_type=action_type, targets=eligible_targets)
        choice = self._query_llm(system_prompt, user_prompt)
        
        target = None
        for player in eligible_targets:
            if player in choice:
                target = player
                break
        
        if not target and eligible_targets:
            target = eligible_targets[0]
            
        log_player_action(self.name, f"Executive Action ({action_type})", target)
        return target

    def receive_private_info(self, info):
        """
        Receives private information (e.g., from an investigation or policy peek).
        This is added to the agent's memory/context for future decisions.
        """
        log_player_thought(self.name, f"Received private info: {info}")
        self.memory.append(f"PRIVATE INFO: {info}")

