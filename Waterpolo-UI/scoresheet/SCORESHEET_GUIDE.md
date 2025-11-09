# Score Sheet Generator - User Guide

## Overview

The Score Sheet Generator creates official World Aquatics-style PDF score sheets from your live match data. It combines:
- **Pre-configured match details** (teams, players, officials) from `match_config.json`
- **Live game statistics** from your device (scores, fouls, penalties, time)
- **Event logging** for detailed goal-by-goal tracking

## Quick Start

### 1. Configure Match Details

Edit `match_config.json` before the match starts with:
- Match details (venue, date, time, category)
- Team names and rosters (14 players each)
- Coaching staff
- Game officials

### 2. Run Your Application

Start the scoreboard application as usual:
```cmd
python main.py
```

### 3. Export Score Sheet

**Option A: From UI (Recommended)**
- Click the **"📄 Export Score Sheet"** button at the bottom of the scoreboard
- PDF will be saved with timestamp: `scoresheet_YYYYMMDD_HHMMSS.pdf`

**Option B: Command Line**
```cmd
python export_scoresheet.py [optional_filename.pdf]
```

**Option C: Programmatically**
```python
from export_scoresheet import export_scoresheet
export_scoresheet("my_match.pdf")
```

## What Gets Auto-Populated

### ✅ From Your Device
- **Live Scores**: Home and guest team totals
- **Game Clock**: Current time and period
- **Goals by Quarter**: Individual player scoring breakdown
- **Personal Fouls**: Tracked per player (0-15)
- **Timeouts**: Used timeouts for each team
- **Penalties**: Active penalties with time remaining
- **Event Log**: Time-stamped goal events with running score

### ⚙️ From Configuration File
- Team names, player names, and numbers
- Coaching staff and officials
- Match venue, date, and time
- Category and match numbers

## File Structure

```
Waterpolo-UI/
├── match_config.json          # Pre-match setup (EDIT THIS)
├── scoresheet_generator.py    # PDF generation engine
├── event_logger.py            # Match event tracking
├── export_scoresheet.py       # Export command
├── test_scoresheet.py         # Test with sample data
└── state.py                   # Enhanced with event detection
```

## Configuration File Format

### `match_config.json`

```json
{
  "match_details": {
    "game": "THA-HKG",
    "venue": "Ahmedabad, IND",
    "date": "10.10.2025",
    "time": "14:00",
    "category": "Men",
    "match_number": 21,
    "day_number": 7
  },
  "officials": {
    "referee": "IVANOVSKI Stanko (MNE) AMBETOV Adil (KAZ)",
    "var_official": "FUKAYA Shuei (JPN)",
    "timekeeper": "",
    "assistant_ref": "",
    "twpc_delegate": "NANAVATI Kamlesh",
    "secretary": ""
  },
  "white_caps": {
    "team_name": "Thailand",
    "team_code": "THA",
    "head_coach": "JARANON Ronnakrit",
    "assistant_coach": "JARANON Wasin",
    "players": [
      {"number": 1, "name": "PONGPRAYOON Sutthiya"},
      {"number": 2, "name": "KAEWWANEE Suteenan"},
      ...
    ]
  },
  "blue_caps": {
    "team_name": "Hong Kong China",
    "team_code": "HKG",
    "head_coach": "RUSTAMOV Kirill",
    "assistant_coach": "KU Yat Wa",
    "players": [
      {"number": 1, "name": "LIU Yeu Yan Ians"},
      {"number": 2, "name": "CHING Taz Shun"},
      ...
    ]
  }
}
```

## Testing

Generate a test PDF with sample data:
```cmd
python test_scoresheet.py
```

This creates `test_scoresheet.pdf` with realistic match data to verify the layout.

## Event Logging

The system automatically logs:
- **Goals**: Timestamp, player, team, quarter, running score
- **Score changes**: Detected automatically from device data
- **Quarter tracking**: Goals organized by quarter

### Enhanced Features Coming Soon
- Automatic player detection (who scored)
- Foul event logging
- Timeout event tracking
- Penalty event logging

## Troubleshooting

### "Config file not found"
- Make sure `match_config.json` exists in the Waterpolo-UI directory
- Copy and edit the provided template

### "Module 'reportlab' not found"
```cmd
pip install reportlab Pillow
```

### PDF shows wrong team/player names
- Edit `match_config.json` with correct information
- Names must match your roster exactly

### Scores are correct but no goals in event log
- Event logging tracks goals as they happen during live play
- Pre-set scores won't show in the detailed event log
- For historical matches, you'll see totals but not time-stamped events

## Advanced Usage

### Custom PDF Location
```python
from scoresheet_generator import ScoreSheetGenerator
from state import scoreboard
from event_logger import event_logger

generator = ScoreSheetGenerator("match_config.json")
generator.generate_scoresheet(scoreboard, event_logger, "custom_output.pdf")
```

### Multiple Match Configs
Keep different config files for different matches:
```cmd
python export_scoresheet.py --config match1_config.json --output match1.pdf
```

## Dependencies

- **reportlab**: PDF generation
- **Pillow**: Image processing (for logos - future feature)
- **PyQt5**: UI integration (already installed)

## Future Enhancements

- [ ] Team logos in PDF
- [ ] Signature fields
- [ ] Auto-detect which player scored
- [ ] Foul type codes (E, P, B, W, etc.)
- [ ] Multi-page support for longer event logs
- [ ] Email/cloud upload integration
- [ ] Match statistics summary page

## Support

For issues or questions:
1. Check `match_config.json` is properly formatted
2. Verify all dependencies are installed
3. Run `test_scoresheet.py` to test PDF generation
4. Check console output for error messages

---

**Generated by**: Waterpolo Scoreboard System  
**Version**: 2.0  
**Date**: November 2025
