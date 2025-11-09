"""
Waterpolo Scoreboard - Main Entry Point
Run the scoreboard application with setup UI and scoreboard display.

Usage:
    python main.py              # Run with setup UI first, then scoreboard
    python main.py --test       # Run unit tests without UI
    python main.py --direct     # Skip setup UI and go directly to scoreboard
"""

import sys
from ui.Scoreboard_UI import main as ui_main


def main():
    """Main entry point for the Waterpolo Scoreboard application."""
    args = sys.argv[1:]
    
    # Check if running tests
    if "--test" in args:
        return ui_main(args)
    
    # Check if skipping setup
    if "--direct" in args:
        return ui_main([arg for arg in args if arg != "--direct"])
    
    # Otherwise, show setup UI first
    from PyQt5.QtWidgets import QApplication
    from ui.setup_ui import SetupWindow, load_team_config
    from ui.Scoreboard_UI import ScoreboardWindow
    from serial_handler import start_serial_reader
    import logging
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logging.info("Starting Waterpolo Scoreboard with Setup UI")
    
    # Load existing configuration if available
    load_team_config()
    
    app = QApplication(sys.argv)
    
    # Create setup window
    setup_window = SetupWindow()
    
    # Create scoreboard window (but don't show it yet)
    scoreboard_window = None
    serial_thread = None
    
    def on_show_scoreboard():
        """Called when user clicks 'Show Scoreboard' button."""
        nonlocal scoreboard_window, serial_thread
        
        # Reload config module to get updated logo paths
        import importlib
        import config
        importlib.reload(config)
        logging.info("Configuration reloaded")
        
        # Start serial reader if not already started
        if serial_thread is None:
            try:
                import serial
                from config import PORT, BAUD
                logging.info(f"Starting serial reader on {PORT} @ {BAUD} baud...")
                # Start serial reader with a callback that accepts 3 arguments (main_str, action_display, playing)
                serial_thread = start_serial_reader(on_time_update_callback=lambda main_str, action_display, playing: None)
                logging.info(f"✓ Serial reader started successfully on {PORT}")
            except ImportError:
                logging.error("pyserial module not found. Install with: pip install pyserial")
            except Exception as e:
                logging.error(f"✗ Could not start serial reader: {e}")
                logging.info("Scoreboard will run without serial data. Check COM port connection.")
        
        # Create and show scoreboard window if not already created
        if scoreboard_window is None:
            scoreboard_window = ScoreboardWindow(on_time_update_cb=lambda elapsed: None)
        
        # Always reload logos to pick up any changes
        scoreboard_window.load_logos()
        logging.info("Logos reloaded")
        
        scoreboard_window.showMaximized()
        setup_window.hide()
        logging.info("✓ Scoreboard window displayed and ready")
    
    # Connect signal
    setup_window.show_scoreboard_signal.connect(on_show_scoreboard)
    
    # Show setup window
    setup_window.show()
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
