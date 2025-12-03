import json
import glob
import os
import sys
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

def find_latest_log():
    log_files = glob.glob('logs/*.jsonl')
    if not log_files:
        return None
    return max(log_files, key=os.path.getctime)

def format_message(entry):
    msg_type = entry.get('type', 'unknown')
    data = entry.get('data', {})
    timestamp = entry.get('timestamp', '').split(' ')[1].split(',')[0] # Extract time only
    
    prefix = f"{Style.DIM}[{timestamp}]{Style.RESET_ALL} "

    if msg_type == 'system':
        message = data.get('message', '')
        return f"{prefix}{Fore.CYAN}{Style.BRIGHT}[SYSTEM] {message}"
    
    elif msg_type == 'game_event':
        event = data.get('event', '')
        return f"{prefix}{Fore.YELLOW}[GAME] {event}"
    
    elif msg_type == 'thought':
        player = data.get('player', 'Unknown')
        thought = data.get('thought', '')
        # Indent thought for better readability
        formatted_thought = thought.replace('\n', '\n' + ' ' * 12)
        return f"{prefix}{Fore.MAGENTA}[THOUGHT] {player}: {formatted_thought}"
    
    elif msg_type == 'speech':
        player = data.get('player', 'Unknown')
        speech = data.get('speech', '')
        return f"{prefix}{Fore.GREEN}{Style.BRIGHT}[SPEECH] {player}: {speech}"
    
    elif msg_type == 'action':
        player = data.get('player', 'Unknown')
        action = data.get('action', '')
        details = data.get('details', '')
        return f"{prefix}{Fore.BLUE}[ACTION] {player}: {action} - {details}"
    
    else:
        return f"{prefix}{entry}"

def render_log(file_path):
    print(f"{Fore.WHITE}{Style.BRIGHT}Reading log file: {file_path}\n")
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    print(format_message(entry))
                except json.JSONDecodeError:
                    print(f"{Fore.RED}Error decoding line: {line.strip()}")
    except FileNotFoundError:
        print(f"{Fore.RED}File not found: {file_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = find_latest_log()
    
    if log_file:
        render_log(log_file)
    else:
        print(f"{Fore.RED}No log files found.")
