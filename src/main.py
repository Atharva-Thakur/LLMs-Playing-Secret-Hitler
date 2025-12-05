import random
import pickle
import os
import sys
from src.engine.game_state import GameEngine
from src.agents.player_agent import PlayerAgent
from src.utils.llm_client import LLMClient
from src.utils.logger import log_system, log_game_event, reconfigure_logger, setup_logger

# DEFAULT_PLAYERS = ["Alice", "Bob", "Charlie", "David", "Eve", "Mark", "Nina"]
DEFAULT_PLAYERS = ["Alice", "Bob", "Charlie", "David", "Eve"]

class GameController:
    def __init__(self, player_names=None):
        if player_names:
            self.engine = GameEngine(player_names)
            self.agents = {}
            self.llm_client = LLMClient()
            self.setup_agents()

    def setup_agents(self):
        # Determine who knows who
        spies = [p for p, r in self.engine.roles.items() if r == "Spy"]
        master_spy = [p for p, r in self.engine.roles.items() if r == "Master Spy"][0]
        
        for name in self.engine.player_names:
            role = self.engine.roles[name]
            party = self.engine.party_membership[name]
            teammates = []
            
            if role == "Spy":
                # Spies know other spies and the Master Spy
                teammates = [p for p in spies if p != name] + [master_spy]
            elif role == "Master Spy":
                # Master Spy knows spies only in 5-6 player games
                if self.engine.num_players <= 6:
                    teammates = spies
                else:
                    teammates = []
            
            self.agents[name] = PlayerAgent(name, role, party, teammates, self.llm_client)

    def save_game(self, filename="last_game_state.pkl"):
        # Temporarily remove LLM client references as they might not be picklable
        temp_client = self.llm_client
        self.llm_client = None
        agent_clients = {}
        for name, agent in self.agents.items():
            agent_clients[name] = agent.llm_client
            agent.llm_client = None
            
        try:
            with open(filename, "wb") as f:
                pickle.dump(self, f)
            log_system(f"Game state saved to {filename}")
        except Exception as e:
            log_system(f"Failed to save game state: {e}")
        finally:
            # Restore clients
            self.llm_client = temp_client
            for name, agent in self.agents.items():
                agent.llm_client = agent_clients[name]

    @staticmethod
    def load_game(filename="last_game_state.pkl"):
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Save file {filename} not found.")
            
        with open(filename, "rb") as f:
            controller = pickle.load(f)
            
        # Re-initialize LLM client
        controller.llm_client = LLMClient()
        for agent in controller.agents.values():
            agent.llm_client = controller.llm_client
            
        # Reconfigure logger if a path was saved
        if hasattr(controller, 'log_file_path') and controller.log_file_path:
            reconfigure_logger(controller.log_file_path)
            
        log_system(f"Game loaded from {filename}")
        return controller

    def run_game(self):
        log_system("Starting Game Session...")
        # If resuming, we might want to know the round number. 
        # For now, we'll just increment from where we think we are or just keep running.
        # Ideally, round_num should be part of the state, but it's a local variable here.
        # We can add it to self.
        if not hasattr(self, 'round_num'):
            self.round_num = 1
        
        while not self.engine.game_over:
            self.save_game() # Save before each round
            log_system(f"--- Round {self.round_num} ---")
            self.play_round()
            self.round_num += 1
            
        log_system(f"GAME OVER. Winner: {self.engine.winner}")

    def play_round(self):
        president_name = self.engine.get_president()
        president_agent = self.agents[president_name]
        
        log_game_event(f"President is {president_name}")
        
        # 1. Nomination
        eligible_chancellors = [p for p in self.engine.player_names if p != president_name and p != self.engine.previous_chancellor]
        if len(self.engine.player_names) > 5 and self.engine.previous_president:
             if self.engine.previous_president in eligible_chancellors:
                 eligible_chancellors.remove(self.engine.previous_president)

        chancellor_nominee = president_agent.nominate_chancellor(self.engine.get_public_game_state(), eligible_chancellors)
        log_game_event(f"President {president_name} nominates {chancellor_nominee} for Chancellor.")
        
        # 2. Discussion
        recent_events = f"{president_name} nominated {chancellor_nominee}."
        discussion_history = ""
        
        # Round 1: Everyone speaks
        log_system("--- Discussion Round 1 ---")
        # Shuffle order each discussion round so it's not always the same people speaking first
        speakers = list(self.engine.player_names)
        random.shuffle(speakers)
        
        for name in speakers:
            speech = self.agents[name].discuss(self.engine.get_public_game_state(), recent_events, discussion_history)
            discussion_history += f"{name}: {speech}\n"

        # Round 2: President and Chancellor Nominee respond/conclude
        log_system("--- Discussion Round 2 (Key Players) ---")
        key_speakers = [president_name, chancellor_nominee]
        
        for name in key_speakers:
            speech = self.agents[name].discuss(self.engine.get_public_game_state(), recent_events, discussion_history)
            discussion_history += f"{name}: {speech}\n"

        # 3. Voting
        votes = {}
        ja_votes = 0
        for name in self.engine.player_names:
            vote = self.agents[name].vote(self.engine.get_public_game_state(), president_name, chancellor_nominee)
            votes[name] = vote
            if vote == "Ja":
                ja_votes += 1
        
        log_game_event(f"Votes: {votes}")
        
        if ja_votes > len(self.engine.player_names) / 2:
            log_game_event("Vote Passed!")
            self.engine.previous_president = president_name
            self.engine.previous_chancellor = chancellor_nominee
            self.engine.chancellor = chancellor_nominee
            self.engine.election_tracker = 0
            
            # Check if Master Spy was elected Chancellor (after 3 Red policies)
            self.engine.check_chancellor_win(chancellor_nominee)
            if self.engine.game_over: return

            self.legislative_session(president_agent, self.agents[chancellor_nominee])
        else:
            log_game_event("Vote Failed!")
            self.engine.election_tracker += 1
            self.engine.chancellor = None
            if self.engine.election_tracker == 3:
                log_game_event("Election Tracker reached 3. Top policy enacted.")
                top_policy = self.engine.draw_policies(1)[0]
                self.engine.enact_policy(top_policy)
                self.engine.election_tracker = 0
                self.engine.previous_president = None # Reset term limits on chaos
                self.engine.previous_chancellor = None
            
            self.engine.advance_president()

    def legislative_session(self, president_agent, chancellor_agent):
        # Draw 3
        policies = self.engine.draw_policies(3)
        log_game_event(f"President draws 3 policies (Hidden).")
        
        # President discards 1
        discarded = president_agent.discard_policy(self.engine.get_public_game_state(), policies)
        policies.remove(discarded)
        self.engine.discard_pile.append(discarded)
        
        # Chancellor receives 2
        log_game_event(f"Chancellor receives 2 policies (Hidden).")
        enacted = chancellor_agent.enact_policy(self.engine.get_public_game_state(), policies)
        policies.remove(enacted)
        self.engine.discard_pile.append(policies[0]) # Discard the other one
        
        # Enact
        action = self.engine.enact_policy(enacted)
        
        # Post-Legislative Discussion
        self.post_legislative_discussion(president_agent, chancellor_agent, enacted)

        # Executive Action
        if action:
            self.handle_executive_action(president_agent, action)
            
        self.engine.advance_president()

    def post_legislative_discussion(self, president_agent, chancellor_agent, enacted_policy):
        log_system("--- Post-Legislative Discussion ---")
        
        # President speaks
        president_context = f"You were President. A {enacted_policy} policy was enacted. Explain your card draw and discard choice."
        president_agent.discuss(self.engine.get_public_game_state(), president_context)
        
        # Chancellor speaks
        chancellor_context = f"You were Chancellor. You enacted a {enacted_policy} policy. Explain your choice."
        chancellor_agent.discuss(self.engine.get_public_game_state(), chancellor_context)

    def handle_executive_action(self, president_agent, action):
        log_game_event(f"Executive Action Triggered: {action}")
        
        if action == "policy_peek":
            # President sees top 3 cards
            top_3 = self.engine.deck[:3] # Just peek, don't draw
            info = f"You peeked at the top 3 policies: {top_3}"
            president_agent.receive_private_info(info)
            log_system(f"President peeks at top 3 policies (Hidden from others).")
            
        elif action == "execution":
            targets = [p for p in self.engine.player_names if p != president_agent.name]
            target = president_agent.perform_executive_action(self.engine.get_public_game_state(), "Execution", targets)
            self.engine.kill_player(target)
            
        elif action == "investigate_loyalty":
            targets = [p for p in self.engine.player_names if p != president_agent.name] # In real game, can't investigate self? Yes.
            target = president_agent.perform_executive_action(self.engine.get_public_game_state(), "Investigate Loyalty", targets)
            party = self.engine.party_membership[target]
            
            info = f"You investigated {target} and found they belong to the {party} party."
            president_agent.receive_private_info(info)
            log_system(f"President investigates {target} (Result hidden).")
            
        elif action == "special_election":
            targets = [p for p in self.engine.player_names if p != president_agent.name]
            target = president_agent.perform_executive_action(self.engine.get_public_game_state(), "Call Special Election", targets)
            # Set next president to target. After their turn, return to normal order.
            # This requires complex turn management.
            # For simplicity, we'll just set the index to that player - 1 (so when we advance, it's them).
            # But we need to remember to return.
            # Let's skip the "return to normal order" complexity for this MVP and just change the president.
            try:
                new_index = self.engine.player_names.index(target)
                self.engine.president_index = (new_index - 1) % len(self.engine.player_names)
            except ValueError:
                pass

if __name__ == "__main__":
    # Check for resume flag
    if "--resume" in sys.argv:
        from src.restore_from_log import restore_game_from_log, find_latest_log_file
        print("Attempting to resume game...")
        # 1. Try to restore from the latest log file (most robust method)
        latest_log = find_latest_log_file()
        if latest_log:
            print(f"Found latest log file: {latest_log}")
            # Reconfigure logger to append to this file
            reconfigure_logger(latest_log)
            try:
                # Restore and update the pickle
                controller = restore_game_from_log(latest_log)
                if controller:
                    print("Successfully restored from log.")
                    controller.run_game()
                else:
                    print("Failed to restore from log.")
            except Exception as e:
                print(f"Error restoring from log: {e}")
                print("Falling back to pickle load...")
                try:
                    controller = GameController.load_game()
                    controller.run_game()
                except FileNotFoundError:
                    print("No saved game found.")
        else:
            print("No log files found. Trying to load pickle directly...")
            try:
                controller = GameController.load_game()
                controller.run_game()
            except FileNotFoundError:
                print("No saved game found. Starting new game.")
                setup_logger()
                controller = GameController(DEFAULT_PLAYERS)
                controller.run_game()
    else:
        setup_logger()
        # Example 7 player game
        controller = GameController(DEFAULT_PLAYERS)
        controller.run_game()
