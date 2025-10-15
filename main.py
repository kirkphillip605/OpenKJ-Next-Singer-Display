import sys
import os
import json
import sqlite3
import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QSpinBox, QHBoxLayout, QPushButton,
    QSizePolicy, QFrame, QLineEdit, QStatusBar, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QFileSystemWatcher, QTimer, pyqtSignal, QTime
from PyQt6.QtGui import QFont, QPixmap, QColor

CONFIG_FILE = 'config.json.bak'
DEFAULT_NUM_SINGERS = 5
DEFAULT_CONFIG = {
    'db_path': None,
    'num_singers': DEFAULT_NUM_SINGERS,
    'display_title': 'Singer Rotation',
    'logo_path': None,
    'venue_name': "Harry's Bar"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            config_with_defaults = DEFAULT_CONFIG.copy()
            config_with_defaults.update(config)
            return config_with_defaults
    else:
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


class ConfigWindow(QMainWindow):
    config_updated = pyqtSignal()

    def __init__(self, config, main_app):
        super().__init__()
        self.config = config
        self.main_app = main_app
        self.setWindowTitle("Configuration")
        self.db_path = config.get('db_path')
        self.num_singers = config.get('num_singers', DEFAULT_NUM_SINGERS)
        self.display_title = config.get('display_title', DEFAULT_CONFIG['display_title'])
        self.logo_path = config.get('logo_path', DEFAULT_CONFIG['logo_path'])
        self.venue_name = config.get('venue_name', DEFAULT_CONFIG['venue_name'])

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        # Database Path Configuration
        db_path_layout = QHBoxLayout()
        db_label = QLabel("Database File:")
        self.db_path_label_display = QLabel(self.db_path if self.db_path else "No database selected")
        db_button = QPushButton("Browse")
        db_button.clicked.connect(self.browse_db)
        db_path_layout.addWidget(db_label)
        db_path_layout.addWidget(self.db_path_label_display)
        db_path_layout.addWidget(db_button)
        layout.addLayout(db_path_layout)

        # Number of Singers Configuration
        num_singers_layout = QHBoxLayout()
        num_singers_label = QLabel("Number of 'Up Next' Singers to Display:")
        self.num_singers_spinbox = QSpinBox()
        self.num_singers_spinbox.setValue(self.num_singers)
        self.num_singers_spinbox.setMinimum(1)
        num_singers_layout.addWidget(num_singers_label)
        num_singers_layout.addWidget(self.num_singers_spinbox)
        layout.addLayout(num_singers_layout)

        # Display Title Configuration
        title_layout = QHBoxLayout()
        title_label = QLabel("Display Title:")
        self.title_input = QLineEdit(self.display_title)
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_input)
        layout.addLayout(title_layout)

        # Logo Path Configuration
        logo_path_layout = QHBoxLayout()
        logo_label = QLabel("Logo Image:")
        self.logo_path_label_display = QLabel(self.logo_path if self.logo_path else "No logo selected")
        logo_button = QPushButton("Browse")
        logo_button.clicked.connect(self.browse_logo)
        logo_path_layout.addWidget(logo_label)
        logo_path_layout.addWidget(self.logo_path_label_display)
        logo_path_layout.addWidget(logo_button)
        layout.addLayout(logo_path_layout)

        # Venue Name Configuration
        venue_name_layout = QHBoxLayout()
        venue_name_label = QLabel("Venue Name:")
        self.venue_name_input = QLineEdit(self.venue_name)
        venue_name_layout.addWidget(venue_name_label)
        venue_name_layout.addWidget(self.venue_name_input)
        layout.addLayout(venue_name_layout)

        # Save Button
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_config)
        layout.addWidget(save_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def browse_db(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select openkj.sqlite Database", "", "SQLite Database (*.sqlite *.db)")
        if file_path:
            self.db_path = file_path
            self.db_path_label_display.setText(self.db_path)

    def browse_logo(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select Logo Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
        if file_path:
            self.logo_path = file_path
            self.logo_path_label_display.setText(os.path.basename(self.logo_path))

    def save_config(self):
        if not self.db_path:
            QMessageBox.warning(self, "Warning", "Please select a database file.")
            return

        self.num_singers = self.num_singers_spinbox.value()
        self.display_title = self.title_input.text()
        self.venue_name = self.venue_name_input.text()
        self.config['db_path'] = self.db_path
        self.config['num_singers'] = self.num_singers
        self.config['display_title'] = self.display_title
        self.config['logo_path'] = self.logo_path
        self.config['venue_name'] = self.venue_name

        save_config(self.config)
        QMessageBox.information(self, "Success", "Configuration saved successfully.")
        self.config_updated.emit()
        self.close()


class Clock(QLabel):
    def __init__(self):
        super().__init__()
        # font = QFont('Arial', 14)
        # self.setFont(font)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        self.update_time()

    def update_time(self):
        current_time = QTime.currentTime()
        formatted_time = current_time.toString("h:mm:ss AP")
        self.setText(formatted_time)


class DisplayWindow(QMainWindow):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.setWindowTitle("Karaoke Queue")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint)

        self.db_path = self.config.get('db_path')
        self.file_watcher = QFileSystemWatcher([self.db_path]) if self.db_path else None
        if self.file_watcher:
            self.file_watcher.fileChanged.connect(self.update_display)

        self.singer_labels = []
        self.song_labels = []
        self.current_singer_label = QLabel("")
        self.current_song_label = QLabel("")
        self.message_overlay_label = QLabel("")
        self.logo_label = QLabel()
        self.display_title_label = QLabel()
        self.venue_label = QLabel()
        self.requests_label = QLabel()
        self.status_bar = QStatusBar()

        self.initUI()
        self.update_display()
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.check_db_modified)
        self.refresh_timer.start(5000)

    def initUI(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)

        # Left Section
        left_section = QFrame()
        left_section.setObjectName("leftSection")
        left_section_layout = QVBoxLayout(left_section)
        left_section_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Align Center

        # Welcome Text and Logo Layout
        welcome_layout = QVBoxLayout()
        welcome_layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Align Welcome Text and Logo to the Center
        self.venue_label = QLabel("Welcome to " + self.config.get('venue_name', DEFAULT_CONFIG['venue_name']))
        self.venue_label.setObjectName("venueLabel")
        self.venue_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_layout.addWidget(self.venue_label)
        logo_layout = QVBoxLayout() #Vertically center logo,
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(self.logo_label)
        welcome_layout.addLayout(logo_layout)
        left_section_layout.addLayout(welcome_layout)

        # Shadow Effect for the logo
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(10)
        shadow_effect.setColor(QColor(0, 0, 0, 150))  # Semi-transparent black
        self.logo_label.setGraphicsEffect(shadow_effect)

        left_section.setLayout(left_section_layout)

        # Vertical Separator Line
        separator_line = QFrame()
        separator_line.setFrameShadow(QFrame.Shadow.Plain)

        # Right Section
        right_section = QFrame()
        right_section.setObjectName("rightSection")
        right_section_layout = QVBoxLayout(right_section)
        right_section_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)  # Center Horizontally, Align Top

        # Centralize content using QVBoxLayout
        centralized_layout = QVBoxLayout()
        centralized_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)  # Center Horizontally, Align Top
        # Display Title
        self.display_title_label = QLabel(self.config.get('display_title', DEFAULT_CONFIG['display_title']))
        self.display_title_label.setObjectName("displayTitle")
        self.display_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        centralized_layout.addWidget(self.display_title_label)

        # Horizontal Line under Title
        title_separator_line = QFrame()
        title_separator_line.setFrameShape(QFrame.Shape.HLine)
        title_separator_line.setObjectName("titleSeparator")
        centralized_layout.addWidget(title_separator_line)

        # Current Performer Section
        current_performer_frame = QFrame()
        current_performer_frame.setObjectName("currentPerformerFrame")  # For styling purposes
        current_performer_layout = QVBoxLayout(current_performer_frame)
        current_performer_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        current_performer_frame.setFrameShape(QFrame.Shape.StyledPanel)
        current_performer_frame.setFrameShadow(QFrame.Shadow.Raised)

        # "On Stage" Heading
        on_stage_layout = QHBoxLayout()
        on_stage_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        on_stage_layout.addWidget(QLabel(""), 1)  # Left Spacer
        on_stage_heading_label = QLabel("On Stage")
        on_stage_heading_label.setObjectName("sectionHeading")
        on_stage_layout.addWidget(on_stage_heading_label)
        on_stage_layout.addWidget(QLabel(""), 1)  # Right Spacer
        current_performer_layout.addLayout(on_stage_layout)

        self.current_singer_label = QLabel("")
        self.current_singer_label.setObjectName("currentSingerName")
        current_performer_layout.addWidget(self.current_singer_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.singing_label = QLabel("Performing")
        self.singing_label.setObjectName("singingLabel")
        current_performer_layout.addWidget(self.singing_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.current_song_label = QLabel("")
        self.current_song_label.setObjectName("currentSongName")
        current_performer_layout.addWidget(self.current_song_label, alignment=Qt.AlignmentFlag.AlignCenter)

        centralized_layout.addWidget(current_performer_frame) #Add the current performer frame to the centralized layout

        # Up Next Section
        up_next_frame = QFrame()
        up_next_frame.setObjectName("upNextFrame")
        up_next_layout = QVBoxLayout(up_next_frame)
        up_next_frame.setFrameShape(QFrame.Shape.StyledPanel)
        up_next_frame.setFrameShadow(QFrame.Shadow.Raised)

        # "Coming Up" heading
        coming_up_layout = QHBoxLayout()
        coming_up_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        coming_up_layout.addWidget(QLabel(""), 1)  # Left Spacer
        coming_up_heading_label = QLabel("Coming Up")
        coming_up_heading_label.setObjectName("sectionHeading")
        coming_up_layout.addWidget(coming_up_heading_label)
        coming_up_layout.addWidget(QLabel(""), 1)  # Right Spacer
        up_next_layout.addLayout(coming_up_layout)

        # Uniform singer/song entries
        for i in range(self.config.get('num_singers', DEFAULT_NUM_SINGERS)):
            singer_song_widget = QWidget() #Container widget to apply a fixed layout to
            singer_song_layout = QVBoxLayout(singer_song_widget)
            singer_song_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)  # Align the name and song
            singer_song_layout.setContentsMargins(0, 0, 0, 0)  # Remove extra margins

            singer_label = QLabel("")
            singer_label.setObjectName("upNextSingerName")
            song_label = QLabel("")
            song_label.setObjectName("upNextSongName")

            self.singer_labels.append(singer_label)
            self.song_labels.append(song_label)

            singer_song_layout.addWidget(singer_label)
            singer_song_layout.addWidget(song_label)

            up_next_layout.addWidget(singer_song_widget) #Add the layout to the main frame

            if i < self.config.get('num_singers', DEFAULT_NUM_SINGERS) - 1: # Add separator line if not last entry
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFrameShadow(QFrame.Shadow.Raised)
                line.setObjectName("upNextSeparator")
                up_next_layout.addWidget(line)
        centralized_layout.addWidget(up_next_frame)
        right_section_layout.addLayout(centralized_layout)
        right_section.setLayout(right_section_layout)

        main_layout.addWidget(left_section, 35)
        main_layout.addWidget(separator_line)
        main_layout.addWidget(right_section, 65)

        # Message Overlay
        self.message_overlay_label = QLabel("")
        self.message_overlay_label.setObjectName("messageOverlay")
        self.message_overlay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_overlay_label.raise_()
        self.message_overlay_label.hide()
        self.message_overlay_label.setGeometry(central_widget.rect())
        self.message_overlay_label.setParent(central_widget)
        self.message_overlay_label.raise_()
        self.message_overlay_label.hide()


        self.setCentralWidget(central_widget)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.setObjectName("statusBar")

        # Initialize and add the clock to the status bar (left side)
        self.clock = Clock()
        self.clock.setObjectName("clock")
        self.status_bar.addWidget(self.clock)  # Use addWidget to align it to the left

        # Add a stretchable widget to push the next items to the right
        status_stretch = QWidget()
        status_stretch.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_bar.addWidget(status_stretch)  # Use addWidget to let it expand

        # Add the request label to the right
        self.requests_label = QLabel("Accepting Requests")
        self.requests_label.setObjectName("requestsLabel")
        self.status_bar.addPermanentWidget(self.requests_label)

        # Clean up the stylesheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #161619;
                color: #eee;
            }
            QLabel {
                color: #eee;
                font-size: 24px;
            }
            #leftSection {
                background-color: #161619;
            }
            #rightSection {
                background-color: #161619;
            }
            #venueLabel {
                font-size: 32px;
                font-weight: bold;
                margin-bottom: 10px;
                text-align: center;
            }
            #displayTitle {
                font-size: 48px;
                font-weight: bold;
                margin-bottom: 10px;
                text-align: center;
            }
            #titleSeparator {
                background-color: #cdceec;
                color: #cdceec;
                margin-bottom: 20px;
                height: 1px;
            }
            #sectionHeading {
                font-size: 32px;
                margin-bottom: 25px;
                text-align: center;
            }
            #currentSingerName {
                font-size: 38px;
                text-align: center;
            }
            #singingLabel {
                font-size: 18px;
                text-align: center;
                font-style: italic;
            }
            #currentSongName {
                font-size: 24px;
                text-align: center;
            }
            #upNextSingerName {
                font-size: 30px;
                font-weight: bold;
                margin-bottom: 5px;
                text-align: center;
            }
            #upNextSongName {
                font-size: 20px;
                font-style: italic;
                margin-bottom: 10px;
                text-align: center;
            }
             #upNextSeparator {
                background-color: #3b3c3c; /* Darker shade for subtle separation */
                color: 353738;
                height: 1px;  /* Thinner line */
                margin-top: 10px;
                margin-bottom: 10px;
             }
            #messageOverlay {
                background-color: rgba(0, 0, 0, 190); /* Semi-transparent black background */
                color: #fff;
                font-size: 72px;
                font-weight: bold; 
            }
            #requestsLabel {
                font-size: 36px;
                color: #00a800;
                margin-right: 10px;
            }
            #clock {
                font-size: 36px;
                color: #eee;
                margin-left: 10px;
            }
            #currentPerformerFrame, #upNextFrame {
               border: 1px solid #353738;
               border-radius: 2px;
               margin-bottom: 15px;
               padding: 10px;
            }
            #statusBar {
                background: transparent;
                border: 1px solid #656565;
                color: #eee;                
            }
        """)

    def resizeEvent(self, event):
        if hasattr(self, 'message_overlay_label') and self.message_overlay_label.parentWidget():
            self.message_overlay_label.setGeometry(self.centralWidget().rect())
        super().resizeEvent(event)

    def check_db_modified(self):
        if self.db_path and os.path.exists(self.db_path):
            current_modified_time = os.path.getmtime(self.db_path)
            if getattr(self, 'last_modified_time', None) is None:
                self.last_modified_time = current_modified_time
            elif current_modified_time > self.last_modified_time:
                self.last_modified_time = current_modified_time
                self.update_display()

    def update_display(self):
        # Update Display Title, Logo, and Venue from config
        self.display_title_label.setText(self.config.get('display_title', DEFAULT_CONFIG['display_title']))
        self.venue_label.setText("Welcome to " + self.config.get('venue_name', DEFAULT_CONFIG['venue_name']))
        logo_path = self.config.get('logo_path', DEFAULT_CONFIG['logo_path'])
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaled(self.logo_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(scaled_pixmap)
        else:
            self.logo_label.clear()

        db_path = self.config.get('db_path')
        num_up_next_singers = self.config.get('num_singers', DEFAULT_NUM_SINGERS)

        if not db_path or not os.path.exists(db_path):
            self.clear_display("Database configuration error.")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            num_singers_to_fetch = num_up_next_singers + 1
            cursor.execute("SELECT singerid, name, position FROM rotationSingers ORDER BY position ASC LIMIT ?", (num_singers_to_fetch,))
            singers_data = cursor.fetchall()

            if singers_data:
                current_singer_id, current_singer_name, _ = singers_data[0]
                self.current_singer_label.setText(current_singer_name)
                current_song_info = self.get_next_song_for_singer(cursor, current_singer_id)
                if current_song_info:
                    self.current_song_label.setText(current_song_info)
                else:
                    self.current_song_label.setText("No song queued.")
            else:
                self.current_singer_label.setText("")
                self.current_song_label.setText("No singers in rotation.")


            for i in range(num_up_next_singers):
                singer_index = i + 1
                if singer_index < len(singers_data):
                    singer_id, singer_name, _ = singers_data[singer_index]
                    self.singer_labels[i].setText(singer_name)
                    next_song_info = self.get_next_song_for_singer(cursor, singer_id)
                    if next_song_info:
                        self.song_labels[i].setText(f" - {next_song_info}")
                    else:
                        self.song_labels[i].setText("No song queued.")
                else:
                    self.singer_labels[i].setText("")
                    self.song_labels[i].setText("")

            conn.close()
            if self.file_watcher and self.db_path not in self.file_watcher.files():
                self.file_watcher.addPath(self.db_path)
                self.file_watcher.fileChanged.connect(self.update_display)

        except sqlite3.Error as e:
            self.clear_display(f"Database error: {e}")
            return

    def get_next_song_for_singer(self, cursor, singer_id):
        cursor.execute("""
            SELECT qs.song
            FROM queueSongs qs
            WHERE qs.singer = ? AND qs.played = 0
            ORDER BY qs.position ASC
            LIMIT 1
        """, (singer_id,))
        next_song_queue_data = cursor.fetchone()

        if next_song_queue_data:
            song_id = next_song_queue_data[0]
            cursor.execute("""
                SELECT ds.Title, ds.Artist
                FROM dbSongs ds
                WHERE ds.songid = ?
            """, (song_id,))
            song_data = cursor.fetchone()
            if song_data:
                title, artist = song_data
                return f"{title} by {artist}"
        return None

    def clear_display(self, message):
        self.current_singer_label.setText("")
        self.current_song_label.setText(message)
        self.current_song_label.setStyleSheet("color: red; font-size: 20px;")
        for i in range(len(self.singer_labels)):
            self.singer_labels[i].setText("")
            self.song_labels[i].setText("")

    def show_message_overlay(self, message):
        self.message_overlay_label.setText(message)
        self.message_overlay_label.show()
        QTimer.singleShot(5000, self.hide_message_overlay)

    def hide_message_overlay(self):
        self.message_overlay_label.hide()


class MainApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.config = load_config()
        self.config_window = None
        self.display_window = None

    def load_config_and_show_display(self):
        self.config = load_config()
        if not self.config.get('db_path') or not os.path.exists(self.config['db_path']):
            self.show_config_window()
        else:
            self.show_display_window()

    def show_config_window(self):
        if not self.config_window:
            self.config_window = ConfigWindow(self.config, self)
            self.config_window.config_updated.connect(self.load_config_and_show_display)
        self.config_window.show()

        if self.display_window:
            self.display_window.close()
            self.display_window = None

    def show_display_window(self):
        if not self.display_window:
            self.display_window = DisplayWindow(self.config)
        self.display_window.update_display()
        self.display_window.show()

        if self.config_window and self.config_window.isVisible():
            self.config_window.close()

        if self.display_window:
            QTimer.singleShot(1000, lambda: self.display_window.show_message_overlay("Welcome to Karaoke!"))

    def run(self):
        self.load_config_and_show_display()
        sys.exit(self.app.exec())


if __name__ == '__main__':
    main_app = MainApp()
    main_app.run()