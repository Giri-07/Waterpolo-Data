"""
Export Score Sheet Command
Generates a PDF score sheet from current game state.
"""

import os
import sys
from datetime import datetime
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import scoreboard, state_lock, get_scoreboard_snapshot
from scoresheet.event_logger import event_logger
from scoresheet.scoresheet_generator import generate_score_sheet


def export_scoresheet(output_file: str = None):
    """
    Export current game state to a PDF score sheet.
    
    Args:
        output_file: Optional custom output filename
    """
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"scoresheet_{timestamp}.pdf"
    
    try:
        # Get current scoreboard snapshot
        snapshot = get_scoreboard_snapshot()
        
        print(f"Generating score sheet...")
        print(f"  Home Score: {snapshot['home_score']}")
        print(f"  Guest Score: {snapshot['guest_score']}")
        print(f"  Period: {snapshot['period']}")
        print(f"  Time: {snapshot['main_time']}")
        print(f"  Total Events Logged: {len(event_logger.get_events())}")
        print(f"  Goal Events: {len(event_logger.get_goal_events())}")
        
        # Generate the PDF
        generate_score_sheet(
            scoreboard=snapshot,
            event_logger=event_logger,
            output_file=output_file,
            config_file="match_config.json"
        )
        
        print(f"\n✓ Score sheet successfully generated: {output_file}")
        return True
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("  Make sure 'match_config.json' exists in the current directory.")
        return False
    except Exception as e:
        print(f"\n✗ Error generating score sheet: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    """
    Run this script to export the current game state to a PDF.
    Usage: python export_scoresheet.py [output_filename.pdf]
    """
    output_file = sys.argv[1] if len(sys.argv) > 1 else None
    export_scoresheet(output_file)
