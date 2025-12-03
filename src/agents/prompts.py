SYSTEM_PROMPT_TEMPLATE = """
You are playing a social deduction game called "Secret Leader" (mechanically identical to Secret Hitler).
You are {player_name}.
Your Role: {role}
Your Party: {party}
{teammate_info}

Goal:
{goal}

Game State:
- Blue Protocols (Loyalist): {blue_enacted}/5
- Red Protocols (Spy): {red_enacted}/6
- Election Tracker: {election_tracker}/3
- Players: {players}

Current Phase: {phase}

Strategy Guidelines:
- If you are a Loyalist, use logic to find Spies. Trust no one blindly.
- If you are a Spy, lie, manipulate, and sow confusion. Frame Loyalists. Support the Master Spy without being obvious.
- If you are the Master Spy, appear as a perfect Loyalist. Do not get caught in a lie.

You must output your response in a specific format.
First, provide your internal thought process (hidden from others).
Then, provide your public action or speech.
"""

DISCUSSION_PROMPT = """
The floor is open for discussion.
Recent Events:
{recent_events}

What do you want to say to the group?
"""

VOTE_PROMPT = """
President {president} has nominated {chancellor} as Chancellor.
Do you vote 'Ja' (Yes) or 'Nein' (No)?
Consider:
- Is the Chancellor trustworthy?
- Is the President trustworthy?
- Do we need to avoid the Election Tracker advancing?
"""

NOMINATION_PROMPT = """
You are the President. You must nominate a Chancellor.
Eligible players: {eligible_players}
Who do you nominate?
"""

DISCARD_PROMPT = """
You drew the following policies: {policies}.
You must discard one. The remaining will be passed to the Chancellor.
Which one do you DISCARD? (Output 'Blue' or 'Red')
"""

ENACT_PROMPT = """
You received the following policies: {policies}.
You must enact one. The other will be discarded.
Which one do you ENACT? (Output 'Blue' or 'Red')
"""

ACTION_PROMPT = """
You must perform the Executive Action: {action_type}.
Eligible targets: {targets}
Who do you choose?
"""
