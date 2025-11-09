# Scoresheet Module

This directory contains all scoresheet-related functionality for the Waterpolo Scoreboard application.

## Files

### Core Modules
- **`scoresheet_generator.py`** - Main scoresheet generation logic
- **`export_scoresheet.py`** - PDF export functionality
- **`export_scoresheet_standalone.py`** - Standalone scoresheet export tool
- **`event_logger.py`** - Event logging for match events

### Testing & Documentation
- **`test_scoresheet.py`** - Unit tests for scoresheet functionality
- **`test_scoresheet.pdf`** - Sample scoresheet output for testing
- **`SCORESHEET_GUIDE.md`** - Comprehensive guide for scoresheet features

## Usage

```python
from scoresheet import generate_scoresheet, export_to_pdf, EventLogger

# Generate scoresheet
scoresheet_data = generate_scoresheet(match_data)

# Export to PDF
export_to_pdf(scoresheet_data, output_path="match_scoresheet.pdf")

# Log events
logger = EventLogger()
logger.log_goal(player=5, team="home", time="05:30")
```

## Maintenance

All scoresheet-related features should be developed and maintained within this directory to keep the codebase organized and modular.
