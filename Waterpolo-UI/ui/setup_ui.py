"""
Setup UI - Configuration window for team and player setup before showing scoreboard.
"""

import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QGridLayout, QScrollArea, QFileDialog,
    QGroupBox, QTabWidget, QMessageBox
)
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from state import scoreboard, state_lock


class SetupWindow(QWidget):
    """Configuration window for setting up teams and players."""
    
    # Signal emitted when user clicks "Show Scoreboard"
    show_scoreboard_signal = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Waterpolo Scoreboard - Setup")
        self.setMinimumSize(900, 700)
        
        # Paths for logo images
        self.home_logo_path = "home_logo.png"
        self.guest_logo_path = "guest_logo.png"
        
        self.init_ui()
        self.load_existing_data()
        
    def init_ui(self):
        """Initialize the setup UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("Scoreboard Setup")
        title.setStyleSheet("font-size: 24pt; font-weight: bold; color: #003366;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Tab widget for Home and Guest teams
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #003366;
                border-radius: 5px;
                background: white;
                margin-top: 0px;
            }
            QTabBar::tab {
                background: #E0E0E0;
                padding: 12px 50px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-size: 14pt;
                font-weight: bold;
                min-width: 150px;
                height: 30px;
            }
            QTabBar::tab:selected {
                background: #003366;
                color: white;
            }
        """)
        
        # Create Home and Guest tabs
        self.home_tab = self.create_team_tab("home")
        self.guest_tab = self.create_team_tab("guest")
        
        self.tabs.addTab(self.home_tab, "Home Team")
        self.tabs.addTab(self.guest_tab, "Guest Team")
        
        main_layout.addWidget(self.tabs)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #0088CC;
                color: white;
                font-size: 14pt;
                font-weight: bold;
                padding: 12px 25px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: #006699;
            }
        """)
        self.save_btn.clicked.connect(self.save_configuration)
        
        self.show_scoreboard_btn = QPushButton("Show Scoreboard")
        self.show_scoreboard_btn.setStyleSheet("""
            QPushButton {
                background: #00AA00;
                color: white;
                font-size: 16pt;
                font-weight: bold;
                padding: 15px 35px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background: #008800;
            }
        """)
        self.show_scoreboard_btn.clicked.connect(self.show_scoreboard)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.show_scoreboard_btn)
        
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
    def create_team_tab(self, team_type):
        """Create a tab for home or guest team configuration."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Team info section
        team_info_group = QGroupBox(f"{team_type.capitalize()} Team Information")
        team_info_group.setStyleSheet("""
            QGroupBox {
                font-size: 14pt;
                font-weight: bold;
                border: 2px solid #003366;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        team_info_layout = QVBoxLayout()
        
        # Team name
        name_layout = QHBoxLayout()
        name_label = QLabel("Team Name:")
        name_label.setStyleSheet("font-size: 12pt; font-weight: normal;")
        name_label.setFixedWidth(120)
        team_name_input = QLineEdit()
        team_name_input.setPlaceholderText(f"Enter {team_type} team name")
        team_name_input.setStyleSheet("font-size: 12pt; padding: 8px;")
        name_layout.addWidget(name_label)
        name_layout.addWidget(team_name_input)
        team_info_layout.addLayout(name_layout)
        
        # Logo selection
        logo_layout = QHBoxLayout()
        logo_label = QLabel("Team Logo:")
        logo_label.setStyleSheet("font-size: 12pt; font-weight: normal;")
        logo_label.setFixedWidth(120)
        
        logo_preview = QLabel()
        logo_preview.setFixedSize(80, 60)
        logo_preview.setStyleSheet("border: 2px solid #CCCCCC; background: #F5F5F5;")
        logo_preview.setAlignment(Qt.AlignCenter)
        
        logo_btn = QPushButton("Choose Logo")
        logo_btn.setStyleSheet("""
            QPushButton {
                background: #0088CC;
                color: white;
                font-size: 11pt;
                padding: 8px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #006699;
            }
        """)
        logo_btn.clicked.connect(lambda: self.choose_logo(team_type, logo_preview))
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(logo_preview)
        logo_layout.addWidget(logo_btn)
        logo_layout.addStretch()
        team_info_layout.addLayout(logo_layout)
        
        team_info_group.setLayout(team_info_layout)
        layout.addWidget(team_info_group)
        
        # Players section
        players_group = QGroupBox("Player Names")
        players_group.setStyleSheet("""
            QGroupBox {
                font-size: 14pt;
                font-weight: bold;
                border: 2px solid #003366;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Scrollable area for players
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        players_widget = QWidget()
        players_layout = QGridLayout()
        players_layout.setSpacing(8)
        players_layout.setContentsMargins(5, 5, 5, 5)
        
        player_inputs = []
        for i in range(14):
            # Player number label
            num_label = QLabel(f"#{i+1}")
            num_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #003366;")
            num_label.setFixedWidth(40)
            num_label.setAlignment(Qt.AlignCenter)
            
            # Player name input
            player_input = QLineEdit()
            player_input.setPlaceholderText(f"Player {i+1} name")
            player_input.setStyleSheet("font-size: 11pt; padding: 6px;")
            
            player_inputs.append(player_input)
            
            # Add to grid (2 columns of players)
            row = i % 7
            col = i // 7
            players_layout.addWidget(num_label, row, col * 2)
            players_layout.addWidget(player_input, row, col * 2 + 1)
        
        players_widget.setLayout(players_layout)
        scroll.setWidget(players_widget)
        
        players_group_layout = QVBoxLayout()
        players_group_layout.addWidget(scroll)
        players_group.setLayout(players_group_layout)
        
        layout.addWidget(players_group)
        
        tab.setLayout(layout)
        
        # Store references for later access
        if team_type == "home":
            self.home_name_input = team_name_input
            self.home_logo_preview = logo_preview
            self.home_player_inputs = player_inputs
        else:
            self.guest_name_input = team_name_input
            self.guest_logo_preview = logo_preview
            self.guest_player_inputs = player_inputs
        
        return tab
    
    def choose_logo(self, team_type, preview_label):
        """Open file dialog to choose a logo image."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select {team_type.capitalize()} Team Logo",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp)"
        )
        
        if file_path:
            # Store the path
            if team_type == "home":
                self.home_logo_path = file_path
            else:
                self.guest_logo_path = file_path
            
            # Show preview
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                preview_label.setPixmap(pixmap.scaled(80, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
    def load_existing_data(self):
        """Load existing team and player data from scoreboard state."""
        with state_lock:
            # Load team names
            self.home_name_input.setText(scoreboard.get("home_name", "HOME"))
            self.guest_name_input.setText(scoreboard.get("guest_name", "GUEST"))
            
            # Load player names
            for i in range(14):
                home_player = scoreboard["players_home"][i]
                guest_player = scoreboard["players_guest"][i]
                
                self.home_player_inputs[i].setText(home_player.get("name", ""))
                self.guest_player_inputs[i].setText(guest_player.get("name", ""))
            
            # Load logo previews if files exist
            if os.path.exists(self.home_logo_path):
                pixmap = QPixmap(self.home_logo_path)
                if not pixmap.isNull():
                    self.home_logo_preview.setPixmap(pixmap.scaled(80, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            
            if os.path.exists(self.guest_logo_path):
                pixmap = QPixmap(self.guest_logo_path)
                if not pixmap.isNull():
                    self.guest_logo_preview.setPixmap(pixmap.scaled(80, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def save_configuration(self):
        """Save the configuration to scoreboard state and config file."""
        with state_lock:
            # Save team names
            scoreboard["home_name"] = self.home_name_input.text().strip() or "HOME"
            scoreboard["guest_name"] = self.guest_name_input.text().strip() or "GUEST"
            
            # Save player names
            for i in range(14):
                home_name = self.home_player_inputs[i].text().strip()
                guest_name = self.guest_player_inputs[i].text().strip()
                
                scoreboard["players_home"][i]["name"] = home_name
                scoreboard["players_guest"][i]["name"] = guest_name
        
        # Save to config file
        config = {
            "home_name": scoreboard["home_name"],
            "guest_name": scoreboard["guest_name"],
            "home_logo": self.home_logo_path,
            "guest_logo": self.guest_logo_path,
            "players_home": [{"num": i+1, "name": scoreboard["players_home"][i]["name"]} for i in range(14)],
            "players_guest": [{"num": i+1, "name": scoreboard["players_guest"][i]["name"]} for i in range(14)]
        }
        
        try:
            with open("team_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Update config.py with logo paths
            self.update_config_file()
            
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {e}")
    
    def update_config_file(self):
        """Update the config.py file with new logo paths."""
        try:
            # Read current config.py
            config_path = "config.py"
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # Update logo paths
                new_lines = []
                for line in lines:
                    if line.startswith("HOME_LOGO ="):
                        new_lines.append(f'HOME_LOGO = "{self.home_logo_path}"\n')
                    elif line.startswith("GUEST_LOGO ="):
                        new_lines.append(f'GUEST_LOGO = "{self.guest_logo_path}"\n')
                    else:
                        new_lines.append(line)
                
                with open(config_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
        except Exception as e:
            print(f"Warning: Could not update config.py: {e}")
    
    def show_scoreboard(self):
        """Save configuration and emit signal to show scoreboard."""
        self.save_configuration()
        self.show_scoreboard_signal.emit()
        # Keep setup window open in background for easy access


def load_team_config():
    """Load team configuration from file if it exists."""
    config_file = "team_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            with state_lock:
                scoreboard["home_name"] = config.get("home_name", "HOME")
                scoreboard["guest_name"] = config.get("guest_name", "GUEST")
                
                # Load player names
                for i in range(14):
                    if i < len(config.get("players_home", [])):
                        scoreboard["players_home"][i]["name"] = config["players_home"][i].get("name", "")
                    if i < len(config.get("players_guest", [])):
                        scoreboard["players_guest"][i]["name"] = config["players_guest"][i].get("name", "")
            
            return config
        except Exception as e:
            print(f"Error loading team config: {e}")
    
    return None
