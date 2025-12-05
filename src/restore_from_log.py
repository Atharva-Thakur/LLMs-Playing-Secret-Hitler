import re
import pickle
import random
import sys
import os
from src.engine.game_state import GameEngine
from src.main import GameController
from src.agents.player_agent import PlayerAgent
from src.utils.llm_client import LLMClient

import glob

# Pre-compiled Regex for ANSI codes
RE_ANSI = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def find_latest_log_file(log_dir="logs"):
    """Finds the most recently created .log file in the logs directory."""
    # Check if directory exists
    if not os.path.exists(log_dir):
        return None
        
    list_of_files = glob.glob(os.path.join(log_dir, "*.log"))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def restore_game_from_log(log_file_path, output_file="last_game_state.pkl"):
    print(f"Restoring game from {log_file_path}...")
    
    with open(log_file_path, 'r') as f:
        lines = f.readlines()

    # Helper to strip ANSI codes
    def strip_ansi(text):
        return RE_ANSI.sub('', text)

    # 1. Extract Players and Roles
    players = []
    roles = {}
    
    for line in lines:
        clean_line = strip_ansi(line)
        if "[SYSTEM] Game Setup Complete. Players:" in clean_line:
            match = re.search(r"Players: \[(.*?)\]", clean_line)
            if match:
                players = [p.strip().strip("'") for p in match.group(1).split(',')]
        
        if "[SYSTEM] Roles (SECRET):" in clean_line:
            match = re.search(r"Roles \(SECRET\): \{(.*?)\}", clean_line)
            if match:
                roles_str = match.group(1)
                # Parse dictionary string roughly
                # 'Alice': 'Loyalist', 'Bob': 'Spy', ...
                role_pairs = roles_str.split(',')
                for pair in role_pairs:
                    p, r = pair.split(':')
                    p = p.strip().strip("'")
                    r = r.strip().strip("'")
                    roles[p] = r
            break # Found roles, stop looking for setup

    if not players or not roles:
        print("Could not find players or roles in log.")
        return

    # Initialize Controller
    controller = GameController(players)
    # Override roles with what was in the log (since GameController randomizes them)
    controller.engine.roles = roles
    for name in players:
        if roles[name] == "Loyalist":
            controller.engine.party_membership[name] = "Loyalist"
        else:
            controller.engine.party_membership[name] = "Spy"
    
    # Re-setup agents with correct roles
    controller.setup_agents()

    # 2. Reconstruct Game State
    blue_enacted = 0
    red_enacted = 0
    discards = []
    
    current_president = None
    previous_president = None
    previous_chancellor = None
    election_tracker = 0
    
    # We need to track the deck composition to reconstruct it
    # Total: 6 Blue, 11 Red
    total_blue = 6
    total_red = 11
    
    for line in lines:
        clean_line = strip_ansi(line)
        
        # Track Enactments
        if "A Blue (Loyalist) Protocol has been enacted" in clean_line:
            blue_enacted += 1
            election_tracker = 0
        elif "A Red (Spy) Protocol has been enacted" in clean_line:
            red_enacted += 1
            election_tracker = 0
            
        # Track Discards
        if "[ACTION]" in clean_line and "Discarded -" in clean_line:
            if "Blue" in clean_line:
                discards.append("Blue")
            elif "Red" in clean_line:
                discards.append("Red")
                
        # Track President
        if "[GAME] President is" in clean_line:
            match = re.search(r"President is (\w+)", clean_line)
            if match:
                current_president = match.group(1)
                
        # Track Election Tracker
        if "Vote Failed!" in clean_line:
            election_tracker += 1
        if "Vote Passed!" in clean_line:
            election_tracker = 0
            # We need to know who was Chancellor to set previous_chancellor
            # We can find the last nomination
            # But simpler: just rely on the fact that if vote passed, the last nominated chancellor became chancellor
            pass
            
        # Track Nominations to set previous_chancellor on vote pass
        if "nominates" in clean_line and "for Chancellor" in clean_line:
             match = re.search(r"nominates (\w+) for Chancellor", clean_line)
             if match:
                 last_nominee = match.group(1)

        if "Vote Passed!" in clean_line:
             previous_president = current_president
             previous_chancellor = last_nominee

        # Track Private Info (Memory)
        if "[THOUGHT]" in clean_line and "Received private info:" in clean_line:
            # ... [THOUGHT] Name: (Internal) ... Received private info: ...
            parts = clean_line.split("[THOUGHT]")
            if len(parts) > 1:
                content = parts[1]
                name_match = re.search(r"^\s*(\w+):", content)
                if name_match:
                    name = name_match.group(1)
                    if "Received private info:" in content:
                        info_match = re.search(r"Received private info: (.*)", content)
                        if info_match:
                            info = info_match.group(1).strip()
                            if name in controller.agents:
                                controller.agents[name].memory.append(f"PRIVATE INFO: {info}")

    # Update Engine State
    controller.engine.blue_policies_enacted = blue_enacted
    controller.engine.red_policies_enacted = red_enacted
    controller.engine.election_tracker = election_tracker
    
    if current_president:
        try:
            controller.engine.president_index = players.index(current_president)
        except ValueError:
            pass
            
    controller.engine.previous_president = previous_president
    controller.engine.previous_chancellor = previous_chancellor
    
    controller.engine.discard_pile = discards
    
    # Store the log file path so we can resume logging to it
    controller.log_file_path = os.path.abspath(log_file_path)

    # Determine Round Number
    round_count = 0
    for line in lines:
        if "--- Round" in line:
             round_count += 1
    
    # If we found rounds, set the next round number
    controller.round_num = round_count + 1 if round_count > 0 else 1
    
    # Reconstruct Deck
    # Remaining = Total - Enacted - Discarded
    # Note: This assumes no cards were "burned" or lost in other ways (like top deck peek doesn't remove)
    # If election tracker reaches 3, a policy is enacted from top. It is NOT discarded.
    # So Enacted + Discarded + Deck = Total.
    
    blue_gone = blue_enacted + discards.count("Blue")
    red_gone = red_enacted + discards.count("Red")
    
    blue_remaining = max(0, total_blue - blue_gone)
    red_remaining = max(0, total_red - red_gone)
    
    new_deck = ["Blue"] * blue_remaining + ["Red"] * red_remaining
    random.shuffle(new_deck)
    controller.engine.deck = new_deck
    
    # Save
    controller.save_game(output_file)
    print(f"Game state restored and saved to {output_file}")
    print(f"Blue: {blue_enacted}, Red: {red_enacted}, Tracker: {election_tracker}")
    print(f"President: {current_president}")
    
    return controller

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/restore_from_log.py <log_file>")
    else:
        restore_game_from_log(sys.argv[1])
