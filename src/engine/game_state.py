import random
from src.utils.logger import log_game_event, log_system

class GameEngine:
    def __init__(self, player_names):
        self.player_names = player_names
        self.num_players = len(player_names)
        self.roles = {}  # player_name -> role
        self.party_membership = {} # player_name -> party (Loyalist/Spy)
        self.deck = []
        self.discard_pile = []
        self.blue_policies_enacted = 0
        self.red_policies_enacted = 0
        self.election_tracker = 0
        self.president_index = 0
        self.chancellor = None
        self.previous_president = None
        self.previous_chancellor = None
        self.game_over = False
        self.winner = None
        self.veto_power_unlocked = False
        
        self.setup_game()

    def setup_game(self):
        # 1. Assign Roles
        # Standard Secret Hitler role distribution
        role_distribution = {
            5:  {"Loyalist": 3, "Spy": 1, "Master Spy": 1},
            6:  {"Loyalist": 4, "Spy": 1, "Master Spy": 1},
            7:  {"Loyalist": 4, "Spy": 2, "Master Spy": 1},
            8:  {"Loyalist": 5, "Spy": 2, "Master Spy": 1},
            9:  {"Loyalist": 5, "Spy": 3, "Master Spy": 1},
            10: {"Loyalist": 6, "Spy": 3, "Master Spy": 1},
        }
        
        if self.num_players not in role_distribution:
            raise ValueError("Game supports 5-10 players.")

        dist = role_distribution[self.num_players]
        roles_list = ["Loyalist"] * dist["Loyalist"] + ["Spy"] * dist["Spy"] + ["Master Spy"] * dist["Master Spy"]
        random.shuffle(roles_list)
        
        for i, name in enumerate(self.player_names):
            self.roles[name] = roles_list[i]
            if roles_list[i] == "Loyalist":
                self.party_membership[name] = "Loyalist"
            else:
                self.party_membership[name] = "Spy" # Master Spy is also Spy party

        # 2. Create Deck (6 Blue, 11 Red)
        self.deck = ["Blue"] * 6 + ["Red"] * 11
        random.shuffle(self.deck)
        
        log_system(f"Game Setup Complete. Players: {self.player_names}")
        # Log roles privately (in a real app this wouldn't be logged or would be hidden)
        log_system(f"Roles (SECRET): {self.roles}")

    def get_president(self):
        return self.player_names[self.president_index]

    def advance_president(self):
        self.president_index = (self.president_index + 1) % len(self.player_names)

    def draw_policies(self, num):
        if len(self.deck) < num:
            self.deck.extend(self.discard_pile)
            self.discard_pile = []
            random.shuffle(self.deck)
            log_game_event("Deck reshuffled.")
        
        drawn = self.deck[:num]
        self.deck = self.deck[num:]
        return drawn

    def enact_policy(self, policy):
        if policy == "Blue":
            self.blue_policies_enacted += 1
            log_game_event("A Blue (Loyalist) Protocol has been enacted.")
        else:
            self.red_policies_enacted += 1
            log_game_event("A Red (Spy) Protocol has been enacted.")
        
        self.check_win_conditions()
        if not self.game_over and policy == "Red":
            return self.get_executive_action()
        return None

    def get_executive_action(self):
        # Returns the type of action the President must take based on Red policies count
        # 5-6 players: 3: Peek, 4: Kill, 5: Kill
        # 7-8 players: 2: Investigate, 3: Special Election, 4: Kill, 5: Kill
        # 9-10 players: 1: Investigate, 2: Investigate, 3: Special Election, 4: Kill, 5: Kill
        
        n = self.num_players
        r = self.red_policies_enacted
        
        if r == 6: return None # Game over anyway
        
        if n <= 6:
            if r == 3: return "policy_peek"
            if r == 4: return "execution"
            if r == 5: return "execution"
        elif n <= 8:
            if r == 2: return "investigate_loyalty"
            if r == 3: return "special_election"
            if r == 4: return "execution"
            if r == 5: return "execution"
        else:
            if r == 1: return "investigate_loyalty"
            if r == 2: return "investigate_loyalty"
            if r == 3: return "special_election"
            if r == 4: return "execution"
            if r == 5: return "execution"
            
        return None

    def check_win_conditions(self):
        if self.blue_policies_enacted >= 5:
            self.game_over = True
            self.winner = "Loyalists"
            log_game_event("Loyalists win by enacting 5 Blue Protocols!")
        elif self.red_policies_enacted >= 6:
            self.game_over = True
            self.winner = "Spies"
            log_game_event("Spies win by enacting 6 Red Protocols!")

    def check_chancellor_win(self, chancellor_name):
        if self.red_policies_enacted >= 3 and self.roles[chancellor_name] == "Master Spy":
            self.game_over = True
            self.winner = "Spies"
            log_game_event(f"Spies win! Master Spy {chancellor_name} was elected Chancellor after 3 Red Protocols.")

    def kill_player(self, player_name):
        if player_name in self.player_names:
            self.player_names.remove(player_name)
            # Adjust president index to ensure rotation continues correctly
            # If we just removed someone, the list shrinks.
            # If the removed person was BEFORE the current president index, we must decrement index.
            # However, since we usually advance president at end of turn, we need to be careful.
            # Simplest approach for MVP: Just remove. The controller gets president by index.
            # If index is out of bounds, wrap it.
            if self.president_index >= len(self.player_names):
                self.president_index = 0
            
            log_game_event(f"Player {player_name} has been executed.")
            if self.roles[player_name] == "Master Spy":
                self.game_over = True
                self.winner = "Loyalists"
                log_game_event(f"Loyalists win! Master Spy {player_name} was executed.")

    def get_public_game_state(self):
        return {
            "blue_enacted": self.blue_policies_enacted,
            "red_enacted": self.red_policies_enacted,
            "election_tracker": self.election_tracker,
            "players_remaining": self.player_names,
            "last_president": self.previous_president,
            "last_chancellor": self.previous_chancellor
        }
