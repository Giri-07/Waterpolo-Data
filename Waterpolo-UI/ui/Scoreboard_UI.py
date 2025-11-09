"""
Scoreboard UI - PyQt5-based graphical interface for Waterpolo Scoreboard.
"""

import sys
import os
import time
import logging
import argparse

# Import from refactored modules
from config import HOME_LOGO, GUEST_LOGO, PAUSE_TIMEOUT, UI_REFRESH_RATE_MS
from state import get_scoreboard_snapshot, get_last_valid_packet_time
from serial_handler import start_serial_reader
from tests import run_tests


# ----------------------
# Logging
# ----------------------
def setup_logging():
    """Setup console logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(threadName)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logging.info("Console logging enabled (minimal)")


# ----------------------
# Serial import check
# ----------------------
try:
    import serial  # type: ignore
    _SERIAL_AVAILABLE = True
except Exception:
    serial = None
    _SERIAL_AVAILABLE = False
# ----------------------
# PyQt UI (retained)
# ----------------------
_PYQT_AVAILABLE = False
try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QPushButton
    )
    from PyQt5.QtGui import QPixmap
    from PyQt5.QtCore import Qt, QTimer
    _PYQT_AVAILABLE = True
except Exception:
    pass


if _PYQT_AVAILABLE:
    class PlayerRow(QWidget):
        def __init__(self, parent=None, is_white_team=False):
            super().__init__(parent)
            self.is_white_team = is_white_team  # Flag to determine styling (white team gets white bg)
            self.num_label = QLabel("")
            self.name_label = QLabel("")
            self.points_label = QLabel("")
            self.foul_container = QWidget()
            self._last_num = None
            self._last_name = None
            self._last_points = None
            self._last_fouls = None
            self._init_ui()

        def _init_ui(self):
            h = QHBoxLayout()
            h.setSpacing(8)
            h.setContentsMargins(2, 0, 2, 0)

            # Color scheme based on team
            if self.is_white_team:
                # White team - blue text on white background
                text_color = "#003366"
                points_color = "#0066CC"
                foul_border_color = "#003366"
            else:
                # Blue team - white text on dark background
                text_color = "white"
                points_color = "#FFD700"
                foul_border_color = "white"

            self.num_label.setFixedWidth(50)
            self.num_label.setAlignment(Qt.AlignCenter)
            self.num_label.setStyleSheet(f"font-weight:bold; font-size:18pt; color:{text_color};")

            self.name_label.setStyleSheet(f"font-size:18pt; color:{text_color};")

            self.points_label.setFixedWidth(50)
            self.points_label.setAlignment(Qt.AlignCenter)
            self.points_label.setStyleSheet(f"font-size:20pt; color:{points_color}; font-weight:bold;")

            self.foul_layout = QHBoxLayout(self.foul_container)
            self.foul_layout.setSpacing(6)
            self.foul_layout.setContentsMargins(0, 0, 0, 0)
            self.foul_dots = []
            for _ in range(3):
                lbl = QLabel()
                lbl.setFixedSize(20, 20)
                lbl.setStyleSheet(f"background: transparent; border-radius:10px; border:3px solid {foul_border_color};")
                self.foul_layout.addWidget(lbl)
                self.foul_dots.append(lbl)

            h.addWidget(self.num_label)
            h.addWidget(self.name_label, 1)
            h.addWidget(self.points_label)
            h.addWidget(self.foul_container)
            self.setLayout(h)

        def update(self, num="", name="", points=0, fouls=0):
            if num != self._last_num:
                self.num_label.setText(str(num) if num else "")
                self._last_num = num
            if name != self._last_name:
                self.name_label.setText(name if name else "")
                self._last_name = name
            if points != self._last_points:
                self.points_label.setText(str(points if points is not None else 0))
                self._last_points = points

            fouls = int(fouls or 0)
            if fouls == self._last_fouls:
                return
            self._last_fouls = fouls

            # Color scheme based on team
            if self.is_white_team:
                border_color = "#003366"
                fill_color = "#003366"
            else:
                border_color = "white"
                fill_color = "white"

            for i, dot in enumerate(self.foul_dots):
                if fouls == 0:
                    dot.setStyleSheet(f"background: transparent; border-radius:10px; border:3px solid {border_color};")
                elif fouls == 1:
                    if i == 0:
                        dot.setStyleSheet(f"background: {fill_color}; border-radius:10px;")
                    else:
                        dot.setStyleSheet(f"background: transparent; border-radius:10px; border:3px solid {border_color};")
                elif fouls == 2:
                    if i <= 1:
                        dot.setStyleSheet(f"background: {fill_color}; border-radius:10px;")
                    else:
                        dot.setStyleSheet(f"background: transparent; border-radius:10px; border:3px solid {border_color};")
                else:
                    if i <= 1:
                        dot.setStyleSheet(f"background: {fill_color}; border-radius:10px;")
                    elif i == 2:
                        dot.setStyleSheet("background: red; border-radius:10px;")
                    else:
                        dot.setStyleSheet(f"background: transparent; border-radius:10px; border:3px solid {border_color};")


    class ScoreboardWindow(QWidget):
        def __init__(self, on_time_update_cb):
            super().__init__()
            self.on_time_update_cb = on_time_update_cb
            self.setWindowTitle("CKN Full Scoreboard v2")
            self.setStyleSheet("""
                QWidget {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #001F3F,
                        stop:0.5 #003366,
                        stop:1 #004080);
                    color: white;
                }
                QLabel { background: transparent; }
            """)
            self.home_logo = None
            self.guest_logo = None
            self._init_exclusion_widgets()
            self.load_logos()
            self.init_ui()
            self.timer = QTimer()
            self.timer.timeout.connect(self.refresh_ui)
            self.timer.start(UI_REFRESH_RATE_MS)  # ~8 Hz

        def _init_exclusion_widgets(self):
            self.home_exclusion = QFrame()
            self.home_exclusion.setFixedSize(100, 350)
            self.home_exclusion.setStyleSheet("""
                background: rgba(255, 107, 107, 0.1);
                border: 1px solid #FF6B6B;
                border-radius: 8px;
            """)

            self.guest_exclusion = QFrame()
            self.guest_exclusion.setFixedSize(100, 350)
            self.guest_exclusion.setStyleSheet("""
                background: rgba(255, 107, 107, 0.1);
                border: 1px solid #FF6B6B;
                border-radius: 8px;
            """)

        def load_logos(self):
            def load(path):
                if os.path.exists(path):
                    try:
                        return QPixmap(path)
                    except Exception:
                        return None
                return None
            # Import config here to get the latest values
            import config
            self.home_logo = load(config.HOME_LOGO)
            self.guest_logo = load(config.GUEST_LOGO)
            
            # Update the flag displays with new logos
            if self.home_logo and hasattr(self, 'home_flag'):
                self.home_flag.setPixmap(self.home_logo.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            if self.guest_logo and hasattr(self, 'guest_flag'):
                self.guest_flag.setPixmap(self.guest_logo.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        def init_ui(self):
            layout = QVBoxLayout()
            layout.setContentsMargins(10, 2, 10, 2)  # Further reduced top/bottom margins
            layout.setSpacing(3)  # Further reduced spacing between sections

            # Top row
            top_row = QHBoxLayout()

            # Home block (with left margin to move content right)
            home_block = QVBoxLayout()
            home_block.setContentsMargins(60, 0, 0, 0)  # Add left margin to move right
            self.home_flag = QLabel()
            self.home_flag.setFixedSize(100, 60)
            self.home_flag.setStyleSheet("background: #ffffff20; border-radius:8px;")
            if self.home_logo:
                self.home_flag.setPixmap(self.home_logo.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.home_name = QLabel("HOME")
            self.home_name.setStyleSheet("font-size:16pt; font-weight:bold; color:white;")
            self.home_score_label = QLabel("0")
            self.home_score_label.setStyleSheet("font-size:56pt; font-weight:bold; color:white;")
            self.home_score_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.home_to = QLabel("TO: 0")
            self.home_to.setStyleSheet("""
                font-size: 14pt; color: #FFD700; font-weight: bold;
                background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 3px 8px;
                border: 1px solid #FFD700;
            """)
            self.home_penalty = QLabel("")
            self.home_penalty.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            self.home_penalty.setWordWrap(False)
            self.home_penalty.setMinimumWidth(180)
            self.home_penalty.setStyleSheet("""
                font-size: 18pt; color: #FF3333; font-weight: bold;
                background: rgba(255, 51, 51, 0.25); border-radius: 10px; padding: 10px 14px;
                border: 3px solid #FF3333;
            """)
            
            # Create horizontal layout for TO and Penalty
            home_to_penalty_row = QHBoxLayout()
            home_to_penalty_row.setSpacing(28)
            home_to_penalty_row.addWidget(self.home_to)
            home_to_penalty_row.addStretch(1)
            home_to_penalty_row.addWidget(self.home_penalty)
            home_to_penalty_row.addStretch(1)
            
            home_block.addWidget(self.home_flag, alignment=Qt.AlignLeft)
            home_block.addWidget(self.home_name, alignment=Qt.AlignLeft)
            home_block.addWidget(self.home_score_label, alignment=Qt.AlignLeft)
            home_block.addLayout(home_to_penalty_row)
            top_row.addLayout(home_block, 2)

            # Center block
            center_block = QVBoxLayout()
            center_block.setSpacing(2)  # Reduced spacing for compact layout
            self.period_label = QLabel("PERIOD 1")
            self.period_label.setStyleSheet("""
                font-size: 18pt; font-weight: bold; color: #E0F7FF;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0088CC, stop:1 #005580);
                border-radius: 12px; padding: 6px 16px; border: 2px solid #00A0E6;
            """)
            self.main_time_label = QLabel("00:00")
            self.main_time_label.setStyleSheet("""
                font-size: 38pt; font-weight: bold; color: white;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(0, 0, 0, 0.8), stop:1 rgba(0, 0, 0, 0.6));
                padding: 12px 25px; border-radius: 18px; border: 3px solid #00A0E6;
            """)
            self.action_time_label = QLabel("00")
            self.action_time_label.setStyleSheet("""
                font-size: 22pt; font-weight: bold; color: #00FFCC;
                background: rgba(0, 255, 204, 0.1); border-radius: 10px;
                padding: 4px 12px; border: 2px solid #00FFCC;
            """)
            # Pause status label
            self.status_label = QLabel("")   # "", "WAITING...", or "PAUSED"
            self.status_label.setAlignment(Qt.AlignCenter)
            self.status_label.setStyleSheet("""
                font-size: 14pt; font-weight: bold; color: #FFB74D;
            """)

            self.poss = QLabel("")
            self.poss.setStyleSheet("""
                font-size: 18pt; color: #FFD700; font-weight: bold;
                background: radial-gradient(circle, #FFD700 30%, transparent 70%);
                min-width: 30px; min-height: 30px; border-radius: 15px;
            """)
            center_block.addWidget(self.period_label, alignment=Qt.AlignCenter)
            center_block.addWidget(self.main_time_label, alignment=Qt.AlignCenter)
            center_block.addWidget(self.action_time_label, alignment=Qt.AlignCenter)
            center_block.addWidget(self.status_label, alignment=Qt.AlignCenter)
            center_block.addWidget(self.poss, alignment=Qt.AlignCenter)
            top_row.addLayout(center_block, 2)

            # Guest block (with right margin to move content left)
            guest_block = QVBoxLayout()
            guest_block.setContentsMargins(0, 0, 60, 0)  # Add right margin to move left
            self.guest_flag = QLabel()
            self.guest_flag.setFixedSize(100, 60)
            self.guest_flag.setStyleSheet("background: #ffffff20; border-radius:8px;")
            if self.guest_logo:
                self.guest_flag.setPixmap(self.guest_logo.scaled(100, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.guest_name = QLabel("GUEST")
            self.guest_name.setStyleSheet("font-size:16pt; font-weight:bold; color:white;")
            self.guest_score_label = QLabel("0")
            self.guest_score_label.setStyleSheet("font-size:56pt; font-weight:bold; color:white;")
            self.guest_score_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.guest_to = QLabel("TO: 0")
            self.guest_to.setStyleSheet("""
                font-size: 14pt; color: #FFD700; font-weight: bold;
                background: rgba(0, 0, 0, 0.3); border-radius: 8px; padding: 3px 8px;
                border: 1px solid #FFD700;
            """)
            self.guest_penalty = QLabel("")
            self.guest_penalty.setAlignment(Qt.AlignRight | Qt.AlignTop)
            self.guest_penalty.setWordWrap(False)
            self.guest_penalty.setMinimumWidth(180)
            self.guest_penalty.setStyleSheet("""
                font-size: 18pt; color: #FF3333; font-weight: bold;
                background: rgba(255, 51, 51, 0.25); border-radius: 10px; padding: 10px 14px;
                border: 3px solid #FF3333;
            """)
            
            # Create horizontal layout for TO and Penalty
            guest_to_penalty_row = QHBoxLayout()
            guest_to_penalty_row.setSpacing(28)
            guest_to_penalty_row.addStretch(1)
            guest_to_penalty_row.addWidget(self.guest_penalty)
            guest_to_penalty_row.addStretch(1)
            guest_to_penalty_row.addWidget(self.guest_to)
            
            guest_block.addWidget(self.guest_flag, alignment=Qt.AlignRight)
            guest_block.addWidget(self.guest_name, alignment=Qt.AlignRight)
            guest_block.addWidget(self.guest_score_label, alignment=Qt.AlignRight)
            guest_block.addLayout(guest_to_penalty_row)
            top_row.addLayout(guest_block, 2)

            layout.addLayout(top_row)

            # Players lists (compact layout to fit all 14 players)
            lists = QHBoxLayout()
            self.home_list_widget = QWidget()
            # White background for home (white team)
            self.home_list_widget.setStyleSheet("""
                QWidget {
                    background: white;
                    border-radius: 10px;
                }
            """)
            hlayout = QVBoxLayout()
            hlayout.setSpacing(3)  # Reduced spacing to fit all 14 players
            hlayout.setContentsMargins(8, 4, 8, 4)
            self.home_rows = []
            for i in range(14):
                r = PlayerRow(is_white_team=True)  # Home is white team
                r.setFixedHeight(46)  # Slightly reduced to fit all 14 with large fonts
                self.home_rows.append(r)
                hlayout.addWidget(r)
            # Remove stretch - use all available space for players
            self.home_list_widget.setLayout(hlayout)

            self.guest_list_widget = QWidget()
            glayout = QVBoxLayout()
            glayout.setSpacing(3)  # Reduced spacing to fit all 14 players
            glayout.setContentsMargins(8, 4, 8, 4)
            self.guest_rows = []
            for i in range(14):
                r = PlayerRow(is_white_team=False)  # Guest is blue team
                r.setFixedHeight(46)  # Slightly reduced to fit all 14 with large fonts
                self.guest_rows.append(r)
                glayout.addWidget(r)
            # Remove stretch - use all available space for players
            self.guest_list_widget.setLayout(glayout)

            lists.addWidget(self.home_list_widget, 2)
            lists.addWidget(self.guest_list_widget, 2)
            layout.addLayout(lists)

            self.setLayout(layout)
            self.showMaximized()

        def refresh_ui(self):
            # Get a thread-safe snapshot of the scoreboard state
            snapshot = get_scoreboard_snapshot()
            
            main_time = snapshot["main_time"]
            action_time = snapshot["action_time"]
            period = snapshot["period"]
            home_name = snapshot["home_name"]
            guest_name = snapshot["guest_name"]
            home_score = snapshot["home_score"]
            guest_score = snapshot["guest_score"]
            to_home = snapshot["timeouts_home"]
            to_guest = snapshot["timeouts_guest"]
            poss = snapshot["possession"]
            penalties_home = snapshot["penalties_home"]
            penalties_guest = snapshot["penalties_guest"]
            players_home = snapshot["players_home"]
            players_guest = snapshot["players_guest"]
            penalty_counts_home = snapshot["penalty_counts_home"]
            penalty_counts_guest = snapshot["penalty_counts_guest"]
            last_time = get_last_valid_packet_time()

            # Update static-ish things
            self.home_name.setText(home_name)
            self.guest_name.setText(guest_name)
            self.home_score_label.setText(str(home_score))
            self.guest_score_label.setText(str(guest_score))
            self.period_label.setText(f"PERIOD {period}")

            # Main + action time (no tenths)
            self.main_time_label.setText(main_time)
            self.action_time_label.setText(action_time)

            # Pause UI = show "PAUSED" if gap > timeout
            if last_time == 0:
                self.status_label.setText("WAITING...")
            elif time.time() - last_time > PAUSE_TIMEOUT:
                self.status_label.setText("PAUSED")
            else:
                self.status_label.setText("")

            # possession
            if poss == "home":
                self.poss.setText("●")
            elif poss == "guest":
                self.poss.setText("○")
            else:
                self.poss.setText("")

            # TO labels reflect B9 "used timeouts"
            self.home_to.setText(f"TO: {to_home}")
            self.guest_to.setText(f"TO: {to_guest}")

            # Penalty labels - stacked vertically (no P1/P2 prefixes, no # before player)
            home_pen_lines = []
            for pen in penalties_home:
                if pen.get("player") and (pen.get("minutes", 0) > 0 or pen.get("seconds", 0) > 0):
                    time_str = f"{pen['minutes']:02d}:{pen['seconds']:02d}"
                    home_pen_lines.append(f"{pen['player']} {time_str}")
            self.home_penalty.setVisible(bool(home_pen_lines))
            self.home_penalty.setText("\n".join(home_pen_lines) if home_pen_lines else "")

            guest_pen_lines = []
            for pen in penalties_guest:
                if pen.get("player") and (pen.get("minutes", 0) > 0 or pen.get("seconds", 0) > 0):
                    time_str = f"{pen['minutes']:02d}:{pen['seconds']:02d}"
                    guest_pen_lines.append(f"{pen['player']} {time_str}")
            self.guest_penalty.setVisible(bool(guest_pen_lines))
            self.guest_penalty.setText("\n".join(guest_pen_lines) if guest_pen_lines else "")

            # Players
            for i in range(14):
                ph = players_home[i] if i < len(players_home) else {}
                pg = players_guest[i] if i < len(players_guest) else {}
                # Override fouls display to represent cumulative penalty count:
                # 1st penalty = 1 bubble filled, 2nd = 2 bubbles, 3rd = 3 bubbles (last red).
                ph_num = ph.get("num")
                pg_num = pg.get("num")
                ph_fouls_vis = penalty_counts_home.get(ph_num, 0)
                pg_fouls_vis = penalty_counts_guest.get(pg_num, 0)
                self.home_rows[i].update(
                    num=ph.get("num", ""),
                    name=ph.get("name", "") or f"Player {i+1}",
                    points=ph.get("points", 0),
                    fouls=ph_fouls_vis,
                )
                self.guest_rows[i].update(
                    num=pg.get("num", ""),
                    name=pg.get("name", "") or f"Player {i+1}",
                    points=pg.get("points", 0),
                    fouls=pg_fouls_vis,
                )


# ----------------------
# Main
# ----------------------
def main(argv=None):
    """Main entry point for the Scoreboard UI application."""
    parser = argparse.ArgumentParser(
        description="CKN Full Scoreboard v3 - Waterpolo Scoreboard with PyQt5 UI"
    )
    parser.add_argument("--test", action="store_true", help="Run unit tests and exit (no UI)")
    args = parser.parse_args(argv)

    if args.test:
        return run_tests()

    setup_logging()

    if not _PYQT_AVAILABLE:
        logging.error("PyQt5 not installed. Install with: pip install pyqt5")
        return 1
    if not _SERIAL_AVAILABLE:
        logging.error("pyserial not installed. Install with: pip install pyserial")
        return 1

    app = QApplication(sys.argv)

    # UI instance
    def on_time_update_cb(main_time: str, action_time: str, playing: bool):
        # UI polls state every ~120 ms; callback reserved for future push updates.
        pass

    w = ScoreboardWindow(on_time_update_cb)

    # Start serial reader thread (decodes stream + updates shared state)
    start_serial_reader(on_time_update_cb)

    return app.exec_()
