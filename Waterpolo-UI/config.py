"""
Configuration settings for Waterpolo Scoreboard application.
"""

# Serial port configuration
PORT = "COM5"
BAUD = 9600

# Packet identifiers
TIME_PACKET = 0x16         # Main clock packet
PENALTY_PACKET = 0x1D      # Penalty times packet
PLAYER_POINTS_PACKET = 0x19  # Home player points packet
GUEST_POINTS_PACKET = 0x1A   # Guest player points packet
FOULS_PACKET = 0x02        # Personal fouls packet

# Timing configuration
PAUSE_TIMEOUT = 0.6        # Seconds before showing "PAUSED"
NO_DATA_LOG_INTERVAL = 5.0 # Seconds between no-data log messages
PPS_REPORT_INTERVAL = 5.0  # Packets per second report interval

# UI Configuration
HOME_LOGO = "C:/Users/girid/Downloads/KAR.png"
GUEST_LOGO = "C:/Users/girid/Downloads/MAH.png"

# UI Update rate
UI_REFRESH_RATE_MS = 120   # Milliseconds (~8 Hz)
