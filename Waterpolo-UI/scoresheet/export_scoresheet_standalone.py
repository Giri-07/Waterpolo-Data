"""
Standalone Score Sheet Exporter
Run this script independently to export the current game state to PDF.
This is completely separate from the Scoreboard UI to avoid any interference.

Usage:
    python export_scoresheet_standalone.py [output_filename.pdf]
"""

import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from state import get_scoreboard_snapshot
from scoresheet.event_logger import event_logger
from scoresheet.scoresheet_generator import generate_score_sheet


def main():
    """Main entry point for standalone scoresheet export."""
    # Determine output filename
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"scoresheet_{timestamp}.pdf"
    
    try:
        print("=" * 60)
        print("SCORESHEET EXPORT - Standalone Mode")
        print("=" * 60)
        
        # Get current scoreboard snapshot (thread-safe)
        snapshot = get_scoreboard_snapshot()
        
        print(f"\nCurrent Game State:")
        print(f"  Home: {snapshot['home_name']} - Score: {snapshot['home_score']}")
        print(f"  Guest: {snapshot['guest_name']} - Score: {snapshot['guest_score']}")
        print(f"  Period: {snapshot['period']}")
        print(f"  Time: {snapshot['main_time']}")
        print(f"  Total Events Logged: {len(event_logger.get_events())}")
        print(f"  Goal Events: {len(event_logger.get_goal_events())}")
        
        print(f"\nGenerating PDF score sheet...")
        
        # Generate the PDF
        generate_score_sheet(
            scoreboard=snapshot,
            event_logger=event_logger,
            output_file=output_file,
            config_file="match_config.json"
        )
        
        print(f"\n✓ SUCCESS: Score sheet generated: {output_file}")
        print("=" * 60)
        return 0
        
    except FileNotFoundError as e:
        print(f"\n✗ ERROR: {e}")
        print("  Make sure 'match_config.json' exists in the current directory.")
        print("=" * 60)
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: Failed to generate scoresheet")
        print(f"  {type(e).__name__}: {e}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
