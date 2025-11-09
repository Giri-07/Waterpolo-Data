"""
Event logger for tracking match events (goals, fouls, timeouts).
Maintains a detailed chronological log of all match events.
"""

import time
import threading
from typing import List, Dict, Optional


class MatchEvent:
    """Represents a single match event."""
    
    def __init__(self, event_type: str, timestamp: str, team: str, player: Optional[int] = None,
                 score_home: int = 0, score_guest: int = 0, quarter: int = 1, 
                 foul_type: Optional[str] = None, comment: Optional[str] = None):
        self.event_type = event_type  # 'goal', 'foul', 'timeout', 'penalty'
        self.timestamp = timestamp  # Game clock time (MM:SS)
        self.team = team  # 'home' or 'guest'
        self.player = player  # Player number
        self.score_home = score_home
        self.score_guest = score_guest
        self.quarter = quarter
        self.foul_type = foul_type  # 'E', 'P', 'B', 'W', etc.
        self.comment = comment
        self.real_time = time.time()  # Real timestamp when event occurred


class EventLogger:
    """
    Tracks all match events for score sheet generation.
    Thread-safe event logging system.
    """
    
    def __init__(self):
        self.events: List[MatchEvent] = []
        self.lock = threading.Lock()
        self.last_score_home = 0
        self.last_score_guest = 0
        self.last_quarter = 1
        self.quarter_goals_home = {1: [], 2: [], 3: [], 4: []}  # {quarter: [player_nums]}
        self.quarter_goals_guest = {1: [], 2: [], 3: [], 4: []}
        
    def log_goal(self, timestamp: str, team: str, player: int, 
                 score_home: int, score_guest: int, quarter: int):
        """Log a goal event."""
        with self.lock:
            event = MatchEvent(
                event_type='goal',
                timestamp=timestamp,
                team=team,
                player=player,
                score_home=score_home,
                score_guest=score_guest,
                quarter=quarter,
                comment=f"{self._get_quarter_name(quarter)}"
            )
            self.events.append(event)
            
            # Track quarter goals
            if team == 'home':
                self.quarter_goals_home[quarter].append(player)
            else:
                self.quarter_goals_guest[quarter].append(player)
            
            self.last_score_home = score_home
            self.last_score_guest = score_guest
            
    def log_foul(self, timestamp: str, team: str, player: int, 
                 foul_type: str, quarter: int):
        """Log a foul event."""
        with self.lock:
            event = MatchEvent(
                event_type='foul',
                timestamp=timestamp,
                team=team,
                player=player,
                foul_type=foul_type,
                quarter=quarter,
                comment=f"{self._get_quarter_name(quarter)}"
            )
            self.events.append(event)
            
    def log_timeout(self, timestamp: str, team: str, quarter: int):
        """Log a timeout event."""
        with self.lock:
            event = MatchEvent(
                event_type='timeout',
                timestamp=timestamp,
                team=team,
                quarter=quarter,
                comment=f"Timeout - {self._get_quarter_name(quarter)}"
            )
            self.events.append(event)
            
    def log_penalty(self, timestamp: str, team: str, player: int, 
                    minutes: int, seconds: int, quarter: int):
        """Log a penalty event."""
        with self.lock:
            event = MatchEvent(
                event_type='penalty',
                timestamp=timestamp,
                team=team,
                player=player,
                quarter=quarter,
                comment=f"Penalty {minutes}:{seconds:02d} - Player {player}"
            )
            self.events.append(event)
            
    def get_events(self) -> List[MatchEvent]:
        """Get all logged events."""
        with self.lock:
            return list(self.events)
            
    def get_goal_events(self) -> List[MatchEvent]:
        """Get only goal events."""
        with self.lock:
            return [e for e in self.events if e.event_type == 'goal']
            
    def get_quarter_summary(self, quarter: int) -> Dict:
        """Get summary of a specific quarter."""
        with self.lock:
            quarter_events = [e for e in self.events if e.quarter == quarter]
            goals_home = [e for e in quarter_events if e.event_type == 'goal' and e.team == 'home']
            goals_guest = [e for e in quarter_events if e.event_type == 'goal' and e.team == 'guest']
            
            return {
                'quarter': quarter,
                'goals_home': len(goals_home),
                'goals_guest': len(goals_guest),
                'events': quarter_events
            }
            
    def get_player_goals_by_quarter(self, team: str) -> Dict[int, Dict[int, int]]:
        """
        Get goals by player by quarter.
        Returns: {player_num: {quarter: goal_count}}
        """
        with self.lock:
            player_goals = {}
            goals = self.quarter_goals_home if team == 'home' else self.quarter_goals_guest
            
            for quarter in [1, 2, 3, 4]:
                for player_num in goals[quarter]:
                    if player_num not in player_goals:
                        player_goals[player_num] = {1: 0, 2: 0, 3: 0, 4: 0}
                    player_goals[player_num][quarter] += 1
                    
            return player_goals
            
    def get_total_goals_by_quarter(self, team: str) -> Dict[int, int]:
        """Get total goals per quarter for a team."""
        with self.lock:
            goals = self.quarter_goals_home if team == 'home' else self.quarter_goals_guest
            return {quarter: len(goals[quarter]) for quarter in [1, 2, 3, 4]}
            
    def update_quarter(self, quarter: int):
        """Update the current quarter."""
        with self.lock:
            self.last_quarter = quarter
            
    def clear_events(self):
        """Clear all logged events (for new match)."""
        with self.lock:
            self.events.clear()
            self.last_score_home = 0
            self.last_score_guest = 0
            self.last_quarter = 1
            self.quarter_goals_home = {1: [], 2: [], 3: [], 4: []}
            self.quarter_goals_guest = {1: [], 2: [], 3: [], 4: []}
            
    def _get_quarter_name(self, quarter: int) -> str:
        """Convert quarter number to name."""
        names = {1: "1st Quarter", 2: "2nd Quarter", 3: "3rd Quarter", 4: "4th Quarter"}
        return names.get(quarter, f"{quarter}th Quarter")
        
    def detect_score_change(self, current_score_home: int, current_score_guest: int, 
                           current_quarter: int, game_time: str) -> Optional[Dict]:
        """
        Detect if score has changed and return event details.
        Call this periodically from the main loop.
        
        Returns: Dict with event info if score changed, None otherwise
        """
        with self.lock:
            changed = False
            team = None
            score_diff = 0
            
            if current_score_home > self.last_score_home:
                changed = True
                team = 'home'
                score_diff = current_score_home - self.last_score_home
            elif current_score_guest > self.last_score_guest:
                changed = True
                team = 'guest'
                score_diff = current_score_guest - self.last_score_guest
                
            if changed:
                return {
                    'team': team,
                    'timestamp': game_time,
                    'score_home': current_score_home,
                    'score_guest': current_score_guest,
                    'quarter': current_quarter,
                    'score_diff': score_diff
                }
            return None


# Global event logger instance
event_logger = EventLogger()
