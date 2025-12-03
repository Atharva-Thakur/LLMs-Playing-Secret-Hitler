import logging
import os
import json
from datetime import datetime
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "type": getattr(record, "log_type", "system"),
            "data": getattr(record, "log_data", {})
        }
        return json.dumps(log_record)

def setup_logger(log_dir="logs"):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"game_session_{timestamp}.log")
    json_log_file = os.path.join(log_dir, f"game_session_{timestamp}.jsonl")

    # Create a custom logger
    logger = logging.getLogger("SecretHitlerLogger")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    if logger.handlers:
        logger.handlers.clear()

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(log_file, encoding='utf-8')
    j_handler = logging.FileHandler(json_log_file, encoding='utf-8')

    c_handler.setLevel(logging.INFO)
    f_handler.setLevel(logging.DEBUG)
    j_handler.setLevel(logging.DEBUG)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(message)s')
    f_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    j_formatter = JsonFormatter('%(asctime)s')

    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)
    j_handler.setFormatter(j_formatter)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)
    logger.addHandler(j_handler)

    return logger

logger = setup_logger()

def log_player_action(player_name, action, details):
    extra = {"log_type": "action", "log_data": {"player": player_name, "action": action, "details": details}}
    logger.info(f"{Fore.CYAN}[ACTION]{Style.RESET_ALL} {player_name}: {action} - {details}", extra=extra)

def log_player_speech(player_name, speech):
    extra = {"log_type": "speech", "log_data": {"player": player_name, "speech": speech}}
    logger.info(f"{Fore.GREEN}[SPEECH]{Style.RESET_ALL} {player_name}: \"{speech}\"", extra=extra)

def log_player_thought(player_name, thought):
    extra = {"log_type": "thought", "log_data": {"player": player_name, "thought": thought}}
    logger.info(f"{Fore.MAGENTA}[THOUGHT]{Style.RESET_ALL} {player_name}: (Internal) {thought}", extra=extra)

def log_game_event(event, data=None):
    extra = {"log_type": "game_event", "log_data": data if data else {"event": event}}
    logger.info(f"{Fore.YELLOW}[GAME]{Style.RESET_ALL} {event}", extra=extra)

def log_system(message):
    extra = {"log_type": "system", "log_data": {"message": message}}
    logger.info(f"{Fore.WHITE}[SYSTEM]{Style.RESET_ALL} {message}", extra=extra)
