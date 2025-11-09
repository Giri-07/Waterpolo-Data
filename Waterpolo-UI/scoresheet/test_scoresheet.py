"""
Test script to generate a sample score sheet with mock data.
Run this to verify the PDF generation works correctly.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import scoreboard, state_lock
from scoresheet.event_logger import event_logger
from scoresheet.scoresheet_generator import generate_score_sheet


def setup_test_data():
    """Setup test data similar to the THA-HKG match."""
    with state_lock:
        # Match state
        scoreboard["home_name"] = "Iran"
        scoreboard["guest_name"] = "P.R. China"
        scoreboard["home_score"] = 15
        scoreboard["guest_score"] = 14
        scoreboard["period"] = 4
        scoreboard["main_time"] = "00:00"
        scoreboard["timeouts_home"] = 2
        scoreboard["timeouts_guest"] = 2
        
        # Player points - HOME TEAM (Iran)
        home_goals = {
            1: 2,  # Player #2: 2 goals
            8: 2,  # Player #9: 2 goals  
            9: 1,  # Player #10: 1 goal
            10: 1, # Player #11: 1 goal
            13: 1  # Player #14: 1 goal
        }
        for player_idx, goals in home_goals.items():
            if player_idx < 14:
                scoreboard["players_home"][player_idx]["points"] = goals
        
        # Player points - GUEST TEAM (China)
        guest_goals = {
            1: 2,  # Player #2: 2 goals
            2: 2,  # Player #3: 2 goals
            3: 2,  # Player #4: 2 goals
            7: 2,  # Player #8: 2 goals
            9: 4,  # Player #10: 4 goals
            10: 1  # Player #11: 1 goal
        }
        for player_idx, goals in guest_goals.items():
            if player_idx < 14:
                scoreboard["players_guest"][player_idx]["points"] = goals
        
        # Player fouls - HOME TEAM
        home_fouls = {
            1: 2, 2: 1, 4: 2, 5: 1, 6: 1, 8: 3, 9: 2, 10: 1, 12: 2
        }
        for player_idx, fouls in home_fouls.items():
            if player_idx < 14:
                scoreboard["players_home"][player_idx]["fouls"] = fouls
        
        # Player fouls - GUEST TEAM
        guest_fouls = {
            1: 2, 2: 1, 4: 2, 7: 3, 8: 1, 10: 1, 11: 1, 14: 1
        }
        for player_idx, fouls in guest_fouls.items():
            if player_idx < 14:
                scoreboard["players_guest"][player_idx]["fouls"] = fouls
    
    # Setup event log with sample goals
    event_logger.clear_events()
    
    # Quarter 1 goals - Home: 3, Guest: 2
    event_logger.log_goal("8:00", "home", 2, 1, 0, 1)
    event_logger.log_goal("7:41", "home", 9, 2, 0, 1)
    event_logger.log_goal("6:37", "guest", 8, 2, 1, 1)
    event_logger.log_goal("6:04", "guest", 10, 2, 2, 1)
    event_logger.log_goal("4:57", "home", 10, 3, 2, 1)
    
    # Quarter 2 goals - Home: 2, Guest: 5
    event_logger.log_goal("8:00", "guest", 10, 3, 3, 2)
    event_logger.log_goal("6:37", "guest", 3, 3, 4, 2)
    event_logger.log_goal("6:04", "guest", 4, 3, 5, 2)
    event_logger.log_goal("4:36", "home", 11, 4, 5, 2)
    event_logger.log_goal("3:58", "guest", 2, 4, 6, 2)
    event_logger.log_goal("2:20", "home", 2, 5, 6, 2)
    event_logger.log_goal("0:22", "guest", 8, 5, 7, 2)
    
    # Quarter 3 goals - Home: 3, Guest: 2
    event_logger.log_goal("8:00", "home", 2, 6, 7, 3)
    event_logger.log_goal("7:41", "guest", 3, 6, 8, 3)
    event_logger.log_goal("6:48", "home", 9, 7, 8, 3)
    event_logger.log_goal("5:53", "guest", 10, 7, 9, 3)
    event_logger.log_goal("3:53", "home", 11, 8, 9, 3)
    
    # Quarter 4 goals - Home: 7, Guest: 5
    event_logger.log_goal("8:00", "guest", 10, 8, 10, 4)
    event_logger.log_goal("7:24", "guest", 2, 8, 11, 4)
    event_logger.log_goal("6:19", "home", 14, 9, 11, 4)
    event_logger.log_goal("5:31", "guest", 11, 9, 12, 4)
    event_logger.log_goal("4:35", "home", 9, 10, 12, 4)
    event_logger.log_goal("3:38", "guest", 4, 10, 13, 4)
    event_logger.log_goal("2:51", "guest", 2, 10, 14, 4)
    event_logger.log_goal("2:19", "home", 10, 11, 14, 4)
    event_logger.log_goal("1:48", "home", 9, 12, 14, 4)
    event_logger.log_goal("1:09", "home", 11, 13, 14, 4)
    event_logger.log_goal("0:43", "home", 14, 14, 14, 4)
    event_logger.log_goal("0:21", "home", 2, 15, 14, 4)
    
    print("Test data loaded successfully!")
    print(f"  Home Score: {scoreboard['home_score']}")
    print(f"  Guest Score: {scoreboard['guest_score']}")
    print(f"  Total Events: {len(event_logger.get_events())}")
    print(f"  Goal Events: {len(event_logger.get_goal_events())}")


def main():
    """Generate a test score sheet."""
    print("="*60)
    print("Score Sheet Generator - Test Script")
    print("="*60)
    print()
    
    # Setup test data
    print("Setting up test data...")
    setup_test_data()
    print()
    
    # Generate PDF
    print("Generating PDF score sheet...")
    output_file = "test_scoresheet.pdf"
    
    try:
        generate_score_sheet(
            scoreboard=scoreboard,
            event_logger=event_logger,
            output_file=output_file,
            config_file="match_config.json"
        )
        print()
        print("="*60)
        print(f"✓ SUCCESS! Score sheet generated: {output_file}")
        print("="*60)
        print()
        print("You can now open the PDF to view the score sheet.")
        
    except Exception as e:
        print()
        print("="*60)
        print(f"✗ ERROR: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
