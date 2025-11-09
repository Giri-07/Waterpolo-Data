"""
PDF Score Sheet Generator for World Aquatics Water Polo Matches.
Generates official score sheets matching the exact World Aquatics template.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class ScoreSheetGenerator:
    """Generates PDF score sheets for water polo matches."""
    
    def __init__(self, config_file: str = "match_config.json"):
        """
        Initialize the score sheet generator.
        
        Args:
            config_file: Path to the JSON configuration file with match details
        """
        self.config_file = config_file
        self.config = self._load_config()
        self.page_width, self.page_height = landscape(A4)
        
        # Layout constants (in mm)
        self.margin = 10
        self.col_left_x = self.margin
        self.col_left_width = 85
        self.col_middle_x = self.col_left_x + self.col_left_width + 5
        self.col_middle_width = 95
        self.col_right_x = self.col_middle_x + self.col_middle_width + 5
        self.col_right_width = 85
        
    def _load_config(self) -> Dict:
        """Load match configuration from JSON file."""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Config file not found: {self.config_file}")
            
    def generate_scoresheet(self, scoreboard: Dict, event_logger, output_file: str = "scoresheet.pdf"):
        """
        Generate a complete score sheet PDF.
        
        Args:
            scoreboard: Current scoreboard state from the game
            event_logger: EventLogger instance with match events
            output_file: Output PDF filename
        """
        c = canvas.Canvas(output_file, pagesize=landscape(A4))
        
        # Draw header (top center)
        self._draw_header(c)
        
        # Draw three main columns
        y_start = self.page_height - 35*mm
        
        # LEFT COLUMN - Match Details + White Caps
        self._draw_left_column(c, scoreboard, event_logger, y_start)
        
        # MIDDLE COLUMN - Event Log
        self._draw_middle_column(c, event_logger, y_start)
        
        # RIGHT COLUMN - Officials + Blue Caps
        self._draw_right_column(c, scoreboard, event_logger, y_start)
        
        c.save()
        print(f"Score sheet generated: {output_file}")
        
    def _draw_header(self, c: canvas.Canvas):
        """Draw the centered header with title."""
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(self.page_width / 2, self.page_height - 18*mm, "SCORE SHEET")
        
    def _draw_left_column(self, c: canvas.Canvas, scoreboard: Dict, event_logger, y_start: float):
        """Draw left column: Match Details + White Caps team."""
        x = self.col_left_x * mm
        y = y_start
        details = self.config['match_details']
        
        # Draw match details (plain text, no borders)
        # First row: GAME and CATEG
        y -= 4*mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y, "GAME:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 13*mm, y, details.get('game', ''))
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 43*mm, y, "CATEG:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 60*mm, y, details.get('category', ''))
        
        # Second row: VENUE and No.
        y -= 5*mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y, "VENUE:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 16*mm, y, details.get('venue', ''))
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 43*mm, y, "No.:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 60*mm, y, str(details.get('match_number', '')))
        
        # Third row: DATE and DAY No.
        y -= 5*mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y, "DATE:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 14*mm, y, details.get('date', ''))
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 43*mm, y, "DAY No.:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 62*mm, y, str(details.get('day_number', '')))
        
        # Fourth row: TIME and END
        y -= 5*mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x, y, "TIME:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 14*mm, y, details.get('time', ''))
        
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 43*mm, y, "END:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 58*mm, y, details.get('end_time', ''))
        
        # WHITE CAPS section with border
        y -= 9*mm
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + self.col_left_width*mm/2, y, "WHITE CAPS")
        
        # Team info table
        y -= 3*mm
        team_box_y = y
        team_box_height = 33*mm  # Height for 6 rows (TEAM + 5 staff)
        c.rect(x, y - team_box_height, self.col_left_width*mm, team_box_height)
        
        # Vertical line separating label and name columns
        c.line(x + 33*mm, team_box_y, x + 33*mm, team_box_y - team_box_height)
        
        white_config = self.config['white_caps']
        
        # TEAM row
        y -= 3.5*mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 1*mm, y, "TEAM:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 40*mm, y, white_config.get('team_name', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_left_width*mm, y - 3*mm)
        
        # 1. Team Head Coach row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y - 1.5*mm, "1. Team Head Coach")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y - 1.5*mm, white_config.get('head_coach', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_left_width*mm, y - 3*mm)
        
        # 2. Team Assistant Coach row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y - 1.5*mm, "2. Team Assistant Coach")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y - 1.5*mm, white_config.get('assistant_coach', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_left_width*mm, y - 3*mm)
        
        # 3. Team Official row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y - 1.5*mm, "3. Team Official")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y - 1.5*mm, white_config.get('team_official', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_left_width*mm, y - 3*mm)
        
        # 4. Team General Manager row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y - 1.5*mm, "4. Team General Manager")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y - 1.5*mm, white_config.get('general_manager', ''))

        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_left_width*mm, y - 3*mm)
        
        # 5. Team Doctor row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y - 1.5*mm, "5. Team Doctor")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y - 1.5*mm, white_config.get('team_doctor', ''))

        # Player table
        y -= 8*mm
        y = self._draw_player_table(c, x, y, white_config['players'], 
                                scoreboard['players_home'], event_logger, 'home', scoreboard)
        
        # RESULT section below player table
        y -= 8*mm
        self._draw_result_table(c, x, y, event_logger, scoreboard)
        
    def _draw_player_table(self, c: canvas.Canvas, x: float, y: float, 
                           player_config: List[Dict], player_stats: List[Dict],
                           event_logger, team: str, scoreboard: Dict):
        """Draw player statistics table."""
        table_start_y = y
        table_width = self.col_left_width*mm
        row_height = 4*mm
        
        # Draw outer border
        c.rect(x, y - 72*mm, table_width, 72*mm)
        
        # Headers - Top row
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x + 3*mm, y - 4*mm, "No.")
        c.drawString(x + 7*mm, y - 4*mm, "Player")
        c.drawCentredString(x + 47*mm, y - 4*mm, "Major Fouls")
        
        # Goals by Quarter header (centered above the 4 columns)
        c.drawCentredString(x + 67*mm, y - 2.25*mm, "Goals by Quarter")
        
        # Draw horizontal line below "Goals by Quarter"
        c.line(x + 56*mm, y - 3*mm, x + table_width, y - 3*mm)
        
        # Second header row - Quarter numbers
        y -= 4*mm
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(x + 58.5*mm, y - 1.25*mm, "1")
        c.drawCentredString(x + 63.5*mm, y - 1.25*mm, "2")
        c.drawCentredString(x + 68.5*mm, y - 1.25*mm, "3")
        c.drawCentredString(x + 73.5*mm, y - 1.25*mm, "4")
        c.drawCentredString(x + 78.5*mm, y - 1.25*mm, "PSO")
        
        # Draw horizontal line after headers
        c.line(x, y - 2*mm, x + table_width, y - 2*mm)
        
        # Draw ALL vertical column lines from top to bottom of table
        # First 3 columns go all the way to the top
        c.line(x + 6*mm, table_start_y, x + 6*mm, table_start_y - 66*mm)  # After No.
        c.line(x + 38*mm, table_start_y, x + 38*mm, table_start_y - 66*mm)  # After Player
        
        # Major Fouls column divided into 3 sub-columns (starting below header)
        fouls_line_start_y = table_start_y - 6*mm
        fouls_width = 18*mm  # Width of Major Fouls section (38mm to 56mm)
        fouls_col_width = fouls_width / 3
        c.line(x + 38*mm + fouls_col_width, fouls_line_start_y, x + 38*mm + fouls_col_width, table_start_y - 66*mm)  # First divider
        c.line(x + 38*mm + 2*fouls_col_width, fouls_line_start_y, x + 38*mm + 2*fouls_col_width, table_start_y - 66*mm)  # Second divider
        c.line(x + 38*mm + 3*fouls_col_width, fouls_line_start_y, x + 38*mm + 3*fouls_col_width, table_start_y - 66*mm)  # Third divider
        
        c.line(x + 56*mm, table_start_y, x + 56*mm, table_start_y - 72*mm)  # After Major Fouls
        # Quarter columns start below "Goals by Quarter" header (at second header row level)
        quarter_line_start_y = table_start_y - 3*mm
        c.line(x + 61*mm, quarter_line_start_y, x + 61*mm, table_start_y - 72*mm)  # After Q1
        c.line(x + 66*mm, quarter_line_start_y, x + 66*mm, table_start_y - 72*mm)  # After Q2
        c.line(x + 71*mm, quarter_line_start_y, x + 71*mm, table_start_y - 72*mm)  # After Q3
        c.line(x + 76*mm, quarter_line_start_y, x + 76*mm, table_start_y - 72*mm)  # After Q4
        
        # Draw all horizontal lines for player rows upfront
        row_y = y - 2*mm  # Starting position after header
        for i in range(14):  # 14 horizontal lines (after each of the 14 player rows)
            row_y -= row_height
            c.line(x, row_y - 0.5*mm, x + table_width, row_y - 0.5*mm)

        # Get player goals by quarter
        player_goals = event_logger.get_player_goals_by_quarter(team)
        
        # Player rows
        y -= 3*mm
        c.setFont("Helvetica", 6)
        for i in range(15):  # 15 rows (14 players + 1 empty)
            if i < len(player_config):
                player_num = player_config[i]['number']
                player_name = player_config[i]['name']
                player_stat = player_stats[i] if i < len(player_stats) else {"fouls": 0}
                
                # Player number (centered in column) and name
                c.drawCentredString(x + 3*mm, y - 2*mm, str(player_num))
                name_display = player_name[:28]  # Truncate if too long
                c.drawString(x + 7*mm, y - 2*mm, name_display)
                
                # Major fouls (show as E, P letters, centered in each sub-column)
                fouls = player_stat.get('fouls', 0)
                # Major Fouls has 3 sub-columns of 6mm each (38-56mm = 18mm total)
                fouls_col_width = 6*mm
                fouls_base_x = x + 38*mm
                for f in range(min(fouls, 3)):  # Show up to 3 fouls (one per column)
                    # Determine foul type (E for most, P for penalty)
                    foul_char = "E"
                    if f >= 2:  # Last foul might be penalty
                        foul_char = "P"
                    # Center in the sub-column
                    c.drawCentredString(fouls_base_x + (f + 0.5) * fouls_col_width, y - 2*mm, foul_char)
                
                # Goals by quarter (centered in columns)
                if player_num in player_goals:
                    goals = player_goals[player_num]
                    if goals[1] > 0:
                        c.drawCentredString(x + 58.5*mm, y - 2*mm, str(goals[1]))
                    if goals[2] > 0:
                        c.drawCentredString(x + 63.5*mm, y - 2*mm, str(goals[2]))
                    if goals[3] > 0:
                        c.drawCentredString(x + 68.5*mm, y - 2*mm, str(goals[3]))
                    if goals[4] > 0:
                        c.drawCentredString(x + 73.5*mm, y - 2*mm, str(goals[4]))

            y -= row_height
        
        # TOTAL row with bold line above
        c.setLineWidth(1.5)
        c.line(x, y + 1*mm, x + table_width, y + 1*mm)
        c.setLineWidth(1)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 25*mm, y - 2*mm, "TOTAL")
        
        total_goals = event_logger.get_total_goals_by_quarter(team)
        c.drawCentredString(x + 58.5*mm, y - 2*mm, str(total_goals.get(1, 0)))
        c.drawCentredString(x + 63.5*mm, y - 2*mm, str(total_goals.get(2, 0)))
        c.drawCentredString(x + 68.5*mm, y - 2*mm, str(total_goals.get(3, 0)))
        c.drawCentredString(x + 73.5*mm, y - 2*mm, str(total_goals.get(4, 0)))
        
        # Return the final y position
        return y
        
    def _draw_result_table(self, c: canvas.Canvas, x: float, y: float, 
                          event_logger, scoreboard: Dict):
        """Draw RESULT table showing both teams' scores by quarter."""
        table_width = self.col_left_width*mm
        result_y = y
        result_height = 14*mm  # Height for 3 rows (header + 2 teams)
        c.rect(x, y - result_height, table_width, result_height)
        
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 1*mm, y - 3*mm, "RESULT")
        c.drawCentredString(x + 14.5*mm, y - 3*mm, "1")
        c.drawCentredString(x + 21*mm, y - 3*mm, "2")
        c.drawCentredString(x + 27*mm, y - 3*mm, "3")
        c.drawCentredString(x + 33*mm, y - 3*mm, "4")
        c.drawCentredString(x + 40.5*mm, y - 3*mm, "PSO")
        c.drawCentredString(x + 51*mm, y - 3*mm, "TOTAL")
        c.drawString(x + 66*mm, y - 3*mm, "TIMEOUT")
        c.drawCentredString(x + 65*mm, y - 8*mm, "1")
        c.drawCentredString(x + 80*mm, y - 8*mm, "2")
        
        # Vertical lines in RESULT section
        c.line(x + 12*mm, result_y, x + 12*mm, result_y - result_height)  # After RESULT
        c.line(x + 18*mm, result_y, x + 18*mm, result_y - result_height)  # After 1
        c.line(x + 24*mm, result_y, x + 24*mm, result_y - result_height)  # After 2
        c.line(x + 30*mm, result_y, x + 30*mm, result_y - result_height)  # After 3
        c.line(x + 36*mm, result_y, x + 36*mm, result_y - result_height)  # After 4
        c.line(x + 45*mm, result_y, x + 45*mm, result_y - result_height)  # After PSO
        c.line(x + 57*mm, result_y, x + 57*mm, result_y - result_height)  # After TOTAL
        c.line(x + 73*mm, result_y - 5*mm, x + 73*mm, result_y - result_height)  # Middle of TIMEOUT
        
        # Horizontal line after header
        c.line(x, result_y - 5*mm, x + table_width, result_y - 5*mm)
        
        # First team row (home team)
        y -= 5*mm
        c.setFont("Helvetica", 7)
        home_code = self.config['white_caps'].get('team_code', '')
        home_goals = event_logger.get_total_goals_by_quarter('home')
        c.drawString(x + 1*mm, y - 3*mm, home_code)
        c.drawCentredString(x + 14.5*mm, y - 3*mm, str(home_goals.get(1, 0)))
        c.drawCentredString(x + 21*mm, y - 3*mm, str(home_goals.get(2, 0)))
        c.drawCentredString(x + 27*mm, y - 3*mm, str(home_goals.get(3, 0)))
        c.drawCentredString(x + 33*mm, y - 3*mm, str(home_goals.get(4, 0)))
        c.drawCentredString(x + 40.5*mm, y - 3*mm, "")  # PSO
        c.drawCentredString(x + 51*mm, y - 3*mm, str(scoreboard['home_score']))
        c.drawCentredString(x + 65*mm, y - 2*mm, "")  # TIMEOUT 1
        c.drawCentredString(x + 80*mm, y - 2*mm, "")  # TIMEOUT 2
        
        # Horizontal line between teams
        c.line(x, y - 4.5*mm, x + table_width, y - 4.5*mm)
        
        # Second team row (guest team)
        y -= 4.5*mm
        guest_code = self.config['blue_caps'].get('team_code', '')
        guest_goals = event_logger.get_total_goals_by_quarter('guest')
        c.drawString(x + 1*mm, y - 3*mm, guest_code)
        c.drawCentredString(x + 14.5*mm, y - 3*mm, str(guest_goals.get(1, 0)))
        c.drawCentredString(x + 21*mm, y - 3*mm, str(guest_goals.get(2, 0)))
        c.drawCentredString(x + 27*mm, y - 3*mm, str(guest_goals.get(3, 0)))
        c.drawCentredString(x + 33*mm, y - 3*mm, str(guest_goals.get(4, 0)))
        c.drawCentredString(x + 40.5*mm, y - 3*mm, "")  # PSO
        c.drawCentredString(x + 51*mm, y - 3*mm, str(scoreboard['guest_score']))
        c.drawCentredString(x + 65*mm, y - 2*mm, "")  # TIMEOUT 1
        c.drawCentredString(x + 80*mm, y - 2*mm, "")  # TIMEOUT 2
        
    def _draw_middle_column(self, c: canvas.Canvas, event_logger, y_start: float):
        """Draw middle column: Event log with two sub-columns."""
        x_left = self.col_middle_x * mm
        x_right = x_left + 47.5*mm
        y = y_start
        table_height = 155*mm
        
        # Draw outer border for event log
        c.rect(x_left, y - table_height, self.col_middle_width*mm, table_height)
        
        # Draw vertical line separating left and right sub-columns
        c.line(x_right, y, x_right, y - table_height)
        
        # Headers for left sub-column
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(x_left + 3*mm, y - 2.5*mm, "Time")
        c.drawCentredString(x_left + 11*mm, y - 2.5*mm, "Player")
        c.drawCentredString(x_left + 18.5*mm, y - 2.5*mm, "Colour")
        c.drawCentredString(x_left + 28*mm, y - 2.5*mm, "Comment")
        c.drawCentredString(x_left + 40*mm, y - 2.5*mm, "Score")

        # Headers for right sub-column
        c.drawCentredString(x_right + 3*mm, y - 2.5*mm, "Time")
        c.drawCentredString(x_right + 11*mm, y - 2.5*mm, "Player")
        c.drawCentredString(x_right + 18.5*mm, y - 2.5*mm, "Colour")
        c.drawCentredString(x_right + 28*mm, y - 2.5*mm, "Comment")
        c.drawCentredString(x_right + 40*mm, y - 2.5*mm, "Score")

        # Draw horizontal line after headers
        header_y = y - 4*mm
        c.line(x_left, header_y, x_left + self.col_middle_width*mm, header_y)
        
        # Draw vertical lines for columns (left sub-column)
        c.line(x_left + 7.5*mm, y, x_left + 7.5*mm, y - table_height)  # After Time
        c.line(x_left + 14.5*mm, y, x_left + 14.5*mm, y - table_height)  # After Player
        c.line(x_left + 22.5*mm, y, x_left + 22.5*mm, y - table_height)  # After Colour
        c.line(x_left + 35*mm, y, x_left + 35*mm, y - table_height)  # After Comment
        
        # Draw vertical lines for columns (right sub-column)
        c.line(x_right + 7.5*mm, y, x_right + 7.5*mm, y - table_height)  # After Time
        c.line(x_right + 14.5*mm, y, x_right + 14.5*mm, y - table_height)  # After Player
        c.line(x_right + 22.5*mm, y, x_right + 22.5*mm, y - table_height)  # After Colour
        c.line(x_right + 35*mm, y, x_right + 35*mm, y - table_height)  # After Comment
        
        # Draw all horizontal lines upfront (spanning full width)
        y -= 6*mm
        event_row_height = 3.5*mm
        # Calculate how many rows fit in the available space (for data entry)
        available_height = table_height - 6*mm - 13*mm  # Subtract header and bottom space for abbreviations
        max_rows_per_column = int(available_height / event_row_height)
        max_rows = max_rows_per_column * 2  # Total for both columns
        
        # Draw horizontal lines for ALL rows until we reach the bottom (above abbreviations)
        row_y = y
        bottom_limit = 16*mm  # Stop just above where abbreviations start
        while row_y - event_row_height > bottom_limit:
            row_y -= event_row_height
            c.line(x_left, row_y + 1.5*mm, x_left + self.col_middle_width*mm, row_y + 1.5*mm)
        
        # Event rows (goals) - populate data in the grid
        c.setFont("Helvetica", 5)
        goal_events = event_logger.get_goal_events()
        event_index = 0
        max_left_rows = max_rows_per_column  # Fill all available rows in left column first
        
        # Fill left column completely first (all rows in left column)
        y_left = y
        for row in range(max_left_rows):
            # Only draw event data if we still have events AND haven't filled left column yet
            if event_index < len(goal_events):
                event = goal_events[event_index]
                c.drawCentredString(x_left + 4*mm, y_left - 1*mm, event.timestamp)
                c.drawCentredString(x_left + 11*mm, y_left - 1*mm, str(event.player) if event.player else "")
                c.drawCentredString(x_left + 17.5*mm, y_left - 1*mm, "W" if event.team == "home" else "B")
                c.drawCentredString(x_left + 28*mm, y_left - 1*mm, "G")  # Goal
                c.drawCentredString(x_left + 41*mm, y_left - 1*mm, f"{event.score_home}-{event.score_guest}")
                event_index += 1
            
            # Move to next row (always move, even if no data)
            y_left -= event_row_height
        
        # Then fill right column with remaining events (if any)
        y_right = y
        for row in range(max_rows_per_column):  # Same number of rows in right column
            # Draw remaining events in right column
            if event_index < len(goal_events):
                event = goal_events[event_index]
                c.drawCentredString(x_right + 4*mm, y_right - 1*mm, event.timestamp)
                c.drawCentredString(x_right + 11*mm, y_right - 1*mm, str(event.player) if event.player else "")
                c.drawCentredString(x_right + 17.5*mm, y_right - 1*mm, "W" if event.team == "home" else "B")
                c.drawCentredString(x_right + 28*mm, y_right - 1*mm, "G")  # Goal
                c.drawCentredString(x_right + 41*mm, y_right - 1*mm, f"{event.score_home}-{event.score_guest}")
                event_index += 1
            
            # Move to next row (always move, even if no data)
            y_right -= event_row_height
        
        # Abbreviations at bottom in a box
        abbr_box_height = 10*mm
        abbr_box_y = 13*mm
        c.rect(x_left, abbr_box_y - abbr_box_height, self.col_middle_width*mm, abbr_box_height)
        
        y_abbr = abbr_box_y - 2*mm
        c.setFont("Helvetica", 4.5)
        abbr_text = "Abbreviations: W=Sprint Won|G=Goal|IP=Penalty|IPG=Penalty Goal|EG=Extra Man Goal|E=Exclusion Foul"
        c.drawString(x_left + 1*mm, y_abbr, abbr_text)
        y_abbr -= 3*mm
        abbr_text2 = "[ES=Exclusion with Substitution] [EV=Excl. for Violent Action] [TO=Timeout] [RC=Red Card] [YC=Yellow Card]"
        c.drawString(x_left + 1*mm, y_abbr, abbr_text2)
        y_abbr -= 3*mm
        abbr_text3 = "[CHW=Challenge won] [CHL=Challenge lost] [YC1=Team yellow card ]"
        c.drawString(x_left + 1*mm, y_abbr, abbr_text3)
        
        
    def _draw_right_column(self, c: canvas.Canvas, scoreboard: Dict, event_logger, y_start: float):
        """Draw right column: Game Officials + Blue Caps team."""
        x = self.col_right_x * mm
        y = y_start
        
        # GAME OFFICIALS header
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 10*mm, y + 4*mm, "GAME OFFICIALS")
        
        # Draw officials (plain text, no borders or lines)
        officials = self.config['officials']
        
        y -= 3*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y, "REFEREE:")
        c.setFont("Helvetica", 6.5)
        c.drawString(x + 22*mm, y, officials.get('referee', '')[:60])
        
        y -= 3*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y, "VAR OFFICIAL:")
        c.setFont("Helvetica", 7)
        c.drawString(x + 22*mm, y, officials.get('var_official', ''))
        
        y -= 3*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y, "TIMEKEEPER:")
        
        y -= 3*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y, "ASSISTANT REF.:")
        
        y -= 3*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y, "TWPC DELEGATE:")
        c.setFont("Helvetica", 7)
        c.drawString(x + 30*mm, y, officials.get('twpc_delegate', ''))
        
        y -= 3*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x, y, "SECRETARY:")
        
        # BLUE CAPS section with border
        y -= 9*mm
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + self.col_right_width*mm/2, y, "BLUE CAPS")
        
        # Team info table
        y -= 3*mm
        team_box_y = y
        team_box_height = 33*mm  # Height for 6 rows (TEAM + 5 staff)
        c.rect(x, y - team_box_height, self.col_right_width*mm, team_box_height)
        
        # Vertical line separating label and name columns
        c.line(x + 33*mm, team_box_y, x + 33*mm, team_box_y - team_box_height)
        
        blue_config = self.config['blue_caps']
        
        # TEAM row
        y -= 3.5*mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 1*mm, y, "TEAM:")
        c.setFont("Helvetica", 8)
        c.drawString(x + 40*mm, y, blue_config.get('team_name', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_right_width*mm, y - 3*mm)
        
        # 1. Team Head Coach row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y- 1.5*mm, "1. Team Head Coach")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y- 1.5*mm, blue_config.get('head_coach', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_right_width*mm, y - 3*mm)
        
        # 2. Team Assistant Coach row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y- 1.5*mm, "2. Team Assistant Coach")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y- 1.5*mm, blue_config.get('assistant_coach', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_right_width*mm, y - 3*mm)
        
        # 3. Team Official row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y- 1.5*mm, "3. Team Official")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y- 1.5*mm, blue_config.get('team_official', ''))
        
        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_right_width*mm, y - 3*mm)
        
        # 4. Team General Manager row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y- 1.5*mm, "4. Team General Manager")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y- 1.5*mm, blue_config.get('general_manager', ''))

        # Horizontal line
        c.line(x, y - 3*mm, x + self.col_right_width*mm, y - 3*mm)
        
        # 5. Team Doctor row
        y -= 5*mm
        c.setFont("Helvetica-Bold", 7)
        c.drawString(x + 0.5*mm, y- 1.5*mm, "5. Team Doctor")
        c.setFont("Helvetica", 7)
        c.drawString(x + 40*mm, y- 1.5*mm, blue_config.get('team_doctor', ''))

        # Player table
        y -= 8*mm
        self._draw_player_table_right(c, x, y, blue_config['players'], 
                                      scoreboard['players_guest'], event_logger, 'guest', scoreboard)
        
    def _draw_player_table_right(self, c: canvas.Canvas, x: float, y: float, 
                                  player_config: List[Dict], player_stats: List[Dict],
                                  event_logger, team: str, scoreboard: Dict):
        """Draw player statistics table for right column (guest team)."""
        # Same as left but for guest team
        self._draw_player_table(c, x, y, player_config, player_stats, event_logger, team, scoreboard)
        
        # Add CONFIRMATION and TIMEOUT section at bottom with borders
        y_conf = 35*mm
        
        # Draw outer borders for entire section
        c.rect(x, y_conf - 15*mm, self.col_right_width*mm, 15*mm)
        
        # Vertical line separating CONFIRMATION and TIMEOUT
        conf_width = 52*mm
        c.line(x + conf_width, y_conf, x + conf_width, y_conf - 15*mm)
        
        # Draw headers
        c.setFont("Helvetica-Bold", 7)
        c.drawCentredString(x + conf_width/2, y_conf - 3.5*mm, "CONFIRMATION")
        c.drawCentredString(x + conf_width + (self.col_right_width*mm - conf_width)/2, y_conf - 3.5*mm, "TIMEOUT")
        
        # Horizontal line after headers
        c.line(x, y_conf - 5*mm, x + self.col_right_width*mm, y_conf - 5*mm)
        
        # Vertical lines in CONFIRMATION section (creating 3 columns)
        conf_col_width = conf_width / 3
        c.line(x + conf_col_width, y_conf - 5*mm, x + conf_col_width, y_conf - 15*mm)
        c.line(x + 2*conf_col_width, y_conf - 5*mm, x + 2*conf_col_width, y_conf - 15*mm)
        
        # Vertical line in TIMEOUT section (creating 2 columns)
        timeout_center = x + conf_width + (self.col_right_width*mm - conf_width) / 2
        c.line(timeout_center, y_conf - 5*mm, timeout_center, y_conf - 15*mm)
        
        # Labels in CONFIRMATION section
        y_conf -= 9*mm
        c.setFont("Helvetica", 6)
        c.drawString(x + 0.5*mm, y_conf, "Referees:")
        
        # Horizontal line separating Referees and Comments
        c.line(x, y_conf - 1*mm, x + self.col_right_width*mm, y_conf - 1*mm)
        
        y_conf -= 5*mm
        c.drawString(x + 0.5*mm, y_conf, "Comments:")
        
        # Column headers for TIMEOUT (1 and 2)
        c.setFont("Helvetica-Bold", 7)
        timeout_left_center = x + conf_width + (timeout_center - x - conf_width) / 2
        timeout_right_center = timeout_center + (x + self.col_right_width*mm - timeout_center) / 2
        c.drawCentredString(timeout_left_center, y_conf + 5*mm, "1")
        c.drawCentredString(timeout_right_center, y_conf + 5*mm, "2")
        
    def _get_quarter_ordinal(self, quarter: int) -> str:
        """Convert quarter number to ordinal string."""
        ordinals = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
        return ordinals.get(quarter, f"{quarter}th")


def generate_score_sheet(scoreboard: Dict, event_logger, output_file: str = "scoresheet.pdf", 
                        config_file: str = "match_config.json"):
    """
    Convenience function to generate a score sheet.
    
    Args:
        scoreboard: Current scoreboard state
        event_logger: EventLogger instance
        output_file: Output PDF filename
        config_file: Match configuration JSON file
    """
    generator = ScoreSheetGenerator(config_file)
    generator.generate_scoresheet(scoreboard, event_logger, output_file)
