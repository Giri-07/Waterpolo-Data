# Score Sheet Quick Reference

## 📋 Before Match

1. **Edit Configuration**
   ```bash
   notepad match_config.json
   ```
   - Update team names
   - Update player names (14 per team)
   - Update coaches
   - Update officials
   - Update venue, date, time

## 🎮 During Match

1. **Run Application**
   ```bash
   python main.py
   ```

2. **Monitor Scoreboard**
   - Scores update automatically
   - Events are logged in real-time
   - All data captured from device

## 📄 Export Score Sheet

### Method 1: UI Button (Easiest)
- Click **"📄 Export Score Sheet"** button
- PDF saved as: `scoresheet_YYYYMMDD_HHMMSS.pdf`

### Method 2: Command Line
```bash
python export_scoresheet.py my_match.pdf
```

### Method 3: Test with Sample Data
```bash
python test_scoresheet.py
```

## 📊 What's Included in PDF

✅ **Auto-Populated**:
- Team scores (total and by quarter)
- Player goals (individual, by quarter)
- Player fouls (per player)
- Timeouts used
- Active penalties
- Game time and period
- Event log (time-stamped goals)

⚙️ **From Config File**:
- Team names
- Player names
- Coaches
- Officials
- Venue, date, time

## 🔧 Quick Fixes

### "Config file not found"
```bash
# Copy the template
copy match_config.json my_match_config.json
```

### "Module not found"
```bash
pip install reportlab Pillow
```

### Test PDF Generation
```bash
python test_scoresheet.py
# Opens: test_scoresheet.pdf
```

## 📁 File Locations

- **Config**: `match_config.json`
- **Output**: `scoresheet_*.pdf` (in same directory)
- **Test Output**: `test_scoresheet.pdf`
- **Documentation**: `SCORESHEET_GUIDE.md`

## 💡 Tips

- Export after each quarter for backups
- Keep match configs organized by date
- Test PDF generation before match day
- Edit config while scoreboard is running (reload not needed)

## 🆘 Support

**Check These First**:
1. Is `match_config.json` valid JSON?
2. Are all dependencies installed?
3. Does test PDF work? (`python test_scoresheet.py`)
4. Check console for error messages

**Common Issues**:
- **Missing players in PDF**: Check config file player array
- **Wrong team names**: Edit `team_name` in config
- **No event log**: Events only logged during live play
- **Button not visible**: Scroll down or maximize window

---

**Quick Command Summary**:
```bash
# Edit config
notepad match_config.json

# Run app
python main.py

# Export PDF
python export_scoresheet.py

# Test PDF
python test_scoresheet.py

# Install deps
pip install reportlab Pillow
```
