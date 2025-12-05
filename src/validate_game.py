import json
import sys
import os
import re

class GameValidator:
    def __init__(self, log_file):
        self.log_file = log_file
        self.players = []
        self.roles = {}
        self.president_index = 0
        self.blue_policies = 0
        self.red_policies = 0
        self.election_tracker = 0
        self.game_over = False
        self.logs = []
        self.current_president = None
        self.current_chancellor_nominee = None
        self.last_president = None
        self.last_chancellor = None
        self.votes = {}
        
    def load_logs(self):
        if not os.path.exists(self.log_file):
            print(f"Error: File {self.log_file} not found.")
            return False
            
        with open(self.log_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                # Attempt to fix concatenated JSONs (e.g. } { -> } \n {)
                # This is a simple heuristic
                if "}{" in line:
                    parts = line.replace("}{", "}\n{").split("\n")
                    for part in parts:
                        try:
                            self.logs.append(json.loads(part))
                        except json.JSONDecodeError:
                            print(f"Warning: Could not decode part: {part[:50]}...")
                else:
                    try:
                        self.logs.append(json.loads(line))
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode line: {line[:50]}...")
        return True

    def validate(self):
        print(f"Validating {self.log_file}...")
        if not self.load_logs():
            return

        for entry in self.logs:
            self.process_entry(entry)
            self.check_state_consistency()
            
        print("\nValidation Complete.")
        print(f"Final State:")
        print(f"  Blue Policies: {self.blue_policies}")
        print(f"  Red Policies: {self.red_policies}")
        print(f"  Election Tracker: {self.election_tracker}")
        print(f"  Game Over: {self.game_over}")
        
        if self.red_policies >= 6 and not self.game_over:
             print("ERROR: Game should have ended (6 Red Policies) but no Game Over event was detected.")
        if self.blue_policies >= 5 and not self.game_over:
             print("ERROR: Game should have ended (5 Blue Policies) but no Game Over event was detected.")

    def check_state_consistency(self):
        # Check for win conditions based on state
        if self.blue_policies >= 5:
            if not self.game_over:
                # We expect a game over message soon
                pass
        if self.red_policies >= 6:
            if not self.game_over:
                pass

    def process_entry(self, entry):
        msg_type = entry.get('type')
        data = entry.get('data', {})
        message = entry.get('message', '')

        if msg_type == 'system':
            self.handle_system(data, message)
        elif msg_type == 'game_event':
            self.handle_game_event(data, message)
        elif msg_type == 'action':
            self.handle_action(data)
        # Thoughts are ignored for validation logic

    def handle_system(self, data, message):
        msg = data.get('message', '')
        if "Game Setup Complete. Players:" in msg:
            # Extract players
            # Expected format: "Game Setup Complete. Players: ['Alice', 'Bob', ...]"
            match = re.search(r"Players: \[(.*?)\]", msg)
            if match:
                self.players = [p.strip().strip("'") for p in match.group(1).split(',')]
                print(f"Found Players: {self.players}")
            else:
                print(f"ERROR: Could not parse players from: {msg}")

        elif "Roles (SECRET):" in msg:
            # Extract roles
            # Expected format: "Roles (SECRET): {'Alice': 'Loyalist', ...}"
            match = re.search(r"Roles \(SECRET\): \{(.*?)\}", msg)
            if match:
                roles_str = match.group(1)
                # Naive parsing of the dict string
                parts = roles_str.split(',')
                for part in parts:
                    if ':' in part:
                        name, role = part.split(':')
                        self.roles[name.strip().strip("'")] = role.strip().strip("'")
                print(f"Found Roles: {len(self.roles)} roles assigned.")
            else:
                print(f"ERROR: Could not parse roles from: {msg}")

    def handle_game_event(self, data, message):
        event = data.get('event', '')
        
        if "President is" in event:
            # "President is Alice"
            name = event.replace("President is ", "").strip()
            self.current_president = name
            # Validate rotation? (Complex due to special elections)
            # For now just track it
            # print(f"  Turn: President is {name}")

        elif "nominates" in event and "for Chancellor" in event:
            # "President Alice nominates Bob for Chancellor."
            match = re.search(r"nominates (.*?) for Chancellor", event)
            if match:
                nominee = match.group(1)
                self.current_chancellor_nominee = nominee
                
                # Validation: Term Limits
                if self.last_chancellor == nominee:
                    print(f"WARNING: Term Limit Violation! {nominee} was nominated but was the previous Chancellor!")
                if len(self.players) > 5 and self.last_president == nominee:
                     print(f"WARNING: Term Limit Violation! {nominee} was nominated but was the previous President!")

        elif "Vote Passed!" in event:
            print(f"  Vote Passed! Government elected: President {self.current_president}, Chancellor {self.current_chancellor_nominee}")
            self.last_president = self.current_president
            self.last_chancellor = self.current_chancellor_nominee
            
            # Check Master Spy Chancellor win condition
            if self.red_policies >= 3:
                chancellor_role = self.roles.get(self.current_chancellor_nominee)
                if chancellor_role == "Master Spy":
                    print(f"  Master Spy {self.current_chancellor_nominee} elected Chancellor with >= 3 Red Policies! Spies should win.")
                    # We expect game over immediately

        elif "Protocol has been enacted" in event:
            if "Blue" in event:
                self.blue_policies += 1
            elif "Red" in event:
                self.red_policies += 1
            
            # Reset election tracker on enactment
            self.election_tracker = 0
            
        elif "Election Tracker increased to" in event:
            try:
                val = int(event.split("to")[-1].strip())
                self.election_tracker = val
            except:
                pass
        
        elif "win by enacting" in event or "win!" in event:
            self.game_over = True
            print(f"GAME OVER DETECTED: {event}")

    def handle_action(self, data):
        action = data.get('action')
        player = data.get('player')
        details = data.get('details')
        
        if action == "Vote":
            self.votes[player] = details
            # We could validate that 'player' is in self.players

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/validate_game.py <log_file>")
        sys.exit(1)
        
    validator = GameValidator(sys.argv[1])
    validator.validate()
