# Waterpolo Scoreboard Application

A real-time scoreboard application for water polo games with serial data integration and **official score sheet PDF generation**.

## Project Structure

```
Waterpolo-UI/
├── main.py                 # Main entry point - run the application from here
├── config.py              # Configuration settings (ports, timeouts, packet IDs)
├── state.py               # Shared state management and thread-safe access
├── serial_handler.py      # Serial communication and packet decoding
├── ui/                    # UI components directory
│   ├── __init__.py       # Package initialization
│   └── Scoreboard_UI.py  # PyQt5 UI implementation
├── decoders/             # Packet decoder modules
│   ├── __init__.py
│   ├── packet_decoder.py   # Time packet decoder
│   ├── penalty_decoder.py  # Penalty packet decoder
│   ├── player_decoder.py   # Player points decoder
│   └── time_decoder.py     # Timeout decoder
├── tests/                # Test modules
│   ├── __init__.py
│   └── test_decoders.py # Unit tests for decoders
├── SampleData.py         # Sample data generator
└── Test.py               # Legacy test file
```

## Running the Application

### Run with UI and Serial Connection
```bash
python main.py
```

### Run Tests Only (No UI)
```bash
python main.py --test
```

## Features

- ⏱️ **Real-time Scoreboard**: Live display of scores, time, penalties, and fouls
- 📊 **Player Statistics**: Individual player points and fouls tracking
- 🎯 **Penalty Tracking**: Active penalties with countdown timers
- 📄 **Score Sheet Export**: Generate official World Aquatics-style PDF score sheets
- 🔄 **Event Logging**: Detailed chronological tracking of all match events
- 🖥️ **Full-Screen UI**: Professional PyQt5 interface with team logos

## Score Sheet Generation

**NEW FEATURE!** Export official World Aquatics-style score sheets as PDF documents.

### Quick Start
1. **Configure match details**: Edit `match_config.json` with team names, player rosters, officials
2. **Run the application**: `python main.py`
3. **Export during/after match**: Click "📄 Export Score Sheet" button in the UI

### What Gets Included
- ✅ Live scores and game clock
- ✅ Goals by quarter (team and individual)
- ✅ Personal fouls per player
- ✅ Timeout tracking
- ✅ Active penalties
- ✅ Detailed event log with timestamps

📖 **Full Documentation**: See [SCORESHEET_GUIDE.md](SCORESHEET_GUIDE.md) for complete instructions

### Test It Out
```bash
python test_scoresheet.py
```
This generates `test_scoresheet.pdf` with sample data.

## Requirements

- Python 3.x
- PyQt5: `pip install pyqt5`
- pyserial: `pip install pyserial`
- reportlab: `pip install reportlab` (for PDF generation)
- Pillow: `pip install Pillow` (for image processing)

## Configuration

Serial port and application settings can be configured in `config.py`:
- PORT: COM5 (default)
- BAUD: 9600
- PAUSE_TIMEOUT: 0.6 seconds
- Packet identifiers (TIME_PACKET, PENALTY_PACKET, etc.)

## Architecture

### Separation of Concerns

The application is organized into distinct modules:

- **config.py**: All configuration constants in one place
- **state.py**: Thread-safe state management with locks and event detection
- **serial_handler.py**: Serial communication and packet processing
- **ui/**: PyQt5 user interface components
- **decoders/**: Packet decoding logic
- **event_logger.py**: Match event tracking system
- **scoresheet_generator.py**: PDF generation engine
- **export_scoresheet.py**: Score sheet export utility
- **tests/**: Unit tests for all decoders

### Benefits of Modular Design

- **Maintainability**: Each module has a single responsibility
- **Testability**: Tests are separated from application code
- **Reusability**: Components can be imported and used independently
- **Readability**: Smaller, focused files are easier to understand

## Legacy Features

- Real-time scoreboard display
- Penalty tracking for both teams
- Player statistics (points, fouls)
- Timeout management
- Serial data stream decoding for packets:
  - 0x16 (time/score)
  - 0x1D (penalties)
  - 0x19 (home player points)
  - 0x1A (guest player points)
