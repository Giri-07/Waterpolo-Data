"""
Shared state management for Waterpolo Scoreboard application.
"""

import time
import threading
from scoresheet.event_logger import event_logger

# ----------------------
# Shared state
# ----------------------
scoreboard = {
    "home_name": "HOME",
    "guest_name": "GUEST",
    "home_score": 0,
    "guest_score": 0,
    "period": 1,
    "main_time": "00:00",
    "action_time": "00",   # always shown (overridden by timeout seconds if active)
    "timeouts_home": 0,    # used timeouts HOME (from B9)
    "timeouts_guest": 0,   # used timeouts GUEST (from B9)
    "possession": None,
    # Penalty data from 0x1D packets
    "penalties": {
        "home": [
            {"player": None, "minutes": 0, "seconds": 0, "type": None},  # Penalty 1
            {"player": None, "minutes": 0, "seconds": 0, "type": None},  # Penalty 2
        ],
        "guest": [
            {"player": None, "minutes": 0, "seconds": 0, "type": None},  # Penalty 1
            {"player": None, "minutes": 0, "seconds": 0, "type": None},  # Penalty 2
        ],
    },
    "players_home": [
        {"num": i + 1, "name": "", "points": 0, "fouls": 0} for i in range(14)
    ],
    "players_guest": [
        {"num": i + 1, "name": "", "points": 0, "fouls": 0} for i in range(14)
    ],
    # Track cumulative penalty count per player (for bubble visualization)
    "penalty_counts_home": {},  # {player_num: count}
    "penalty_counts_guest": {},
}

# Thread safety
state_lock = threading.Lock()

# Tracking variables
last_valid_packet_time = 0.0  # for pause UI
last_logged_clock = None
last_logged_score_tuple = None
last_b9_logged = (-1, -1)     # (home_used, guest_used) for change-detect logs
last_logged_penalties = None  # for penalty change-detect logs


def get_scoreboard_snapshot():
    """Get a thread-safe snapshot of the scoreboard state."""
    with state_lock:
        return {
            "main_time": scoreboard["main_time"],
            "action_time": scoreboard["action_time"],
            "period": scoreboard["period"],
            "home_name": scoreboard["home_name"],
            "guest_name": scoreboard["guest_name"],
            "home_score": scoreboard["home_score"],
            "guest_score": scoreboard["guest_score"],
            "timeouts_home": scoreboard.get("timeouts_home", 0),
            "timeouts_guest": scoreboard.get("timeouts_guest", 0),
            "possession": scoreboard.get("possession"),
            "penalties_home": [dict(p) for p in scoreboard["penalties"]["home"]],
            "penalties_guest": [dict(p) for p in scoreboard["penalties"]["guest"]],
            "players_home": [dict(scoreboard["players_home"][i]) for i in range(14)],
            "players_guest": [dict(scoreboard["players_guest"][i]) for i in range(14)],
            "penalty_counts_home": dict(scoreboard["penalty_counts_home"]),
            "penalty_counts_guest": dict(scoreboard["penalty_counts_guest"]),
        }


def update_last_valid_packet_time():
    """Update the timestamp of the last valid packet received."""
    global last_valid_packet_time
    last_valid_packet_time = time.time()


def get_last_valid_packet_time():
    """Get the timestamp of the last valid packet received."""
    return last_valid_packet_time


def detect_and_log_score_changes():
    """
    Monitor scoreboard for score changes and log goal events.
    Should be called periodically from the main loop.
    """
    global last_logged_score_tuple
    
    current_home = scoreboard["home_score"]
    current_guest = scoreboard["guest_score"]
    current_period = scoreboard["period"]
    current_time = scoreboard["main_time"]
    
    if last_logged_score_tuple is None:
        last_logged_score_tuple = (current_home, current_guest)
        return
    
    last_home, last_guest = last_logged_score_tuple
    
    # Detect home team goal
    if current_home > last_home:
        # Try to determine which player scored (use player points data)
        # For now, log with player=None, can be enhanced later
        event_logger.log_goal(
            timestamp=current_time,
            team='home',
            player=None,  # Would need additional logic to determine scorer
            score_home=current_home,
            score_guest=current_guest,
            quarter=current_period
        )
        last_logged_score_tuple = (current_home, current_guest)
    
    # Detect guest team goal
    elif current_guest > last_guest:
        event_logger.log_goal(
            timestamp=current_time,
            team='guest',
            player=None,  # Would need additional logic to determine scorer
            score_home=current_home,
            score_guest=current_guest,
            quarter=current_period
        )
        last_logged_score_tuple = (current_home, current_guest)
