import sys
import os
import json
import sqlite3
import logging
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
import time
from threading import Thread
import pystray
from PIL import Image, ImageDraw
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QSpinBox, QHBoxLayout, QPushButton,
    QLineEdit, QStatusBar, QDialog, QComboBox, QFormLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

# Configuration
CONFIG_FILE = 'config.json'
DEFAULT_CONFIG = {
    'db_path': 'openkj.sqlite',
    'num_up_next': 5,
    'server_port': 5000,
    'log_level': 'INFO',
    'display_title': 'Singer Rotation',
    'venue_name': "Harry's Bar",
    'refresh_interval': 5,  # Seconds between database refreshes
    'log_file': 'rotation_server.log',
}

# Logging Setup
# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create a file handler and set the logging format
log_file = DEFAULT_CONFIG['log_file']
file_handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)

# Create a stream handler for console output (optional)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def load_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all keys from DEFAULT_CONFIG are present
                full_config = DEFAULT_CONFIG.copy()
                full_config.update(config)
                return full_config
        else:
            return DEFAULT_CONFIG
    except Exception as e:
        logger.error(f"Error loading config: {e}, using defaults.")
        return DEFAULT_CONFIG


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info("Configuration saved successfully.")
    except Exception as e:
        logger.error(f"Error saving config: {e}")


config = load_config()

# Flask App
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)  # Disable SocketIO's default logger


# Override Logging Level
logger.setLevel(config['log_level'].upper())
app.logger.setLevel(config['log_level'].upper())


# Database Helper Functions (Same as before, but using config)
def get_db_connection():
    try:
        conn = sqlite3.connect(config['db_path'])
        conn.row_factory = sqlite3.Row  # Access columns by name
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        return None  # Critical:  Return None if the connection fails.


def get_current_singer_and_song():
    conn = get_db_connection()
    if not conn:
        return None  # Handle connection failure

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT singerid, name, position FROM rotationSingers ORDER BY position ASC LIMIT 1")
        current_singer_data = cursor.fetchone()

        if current_singer_data:
            singer_id = current_singer_data['singerid']  # Access by column name
            singer_name = current_singer_data['name']

            song_info = get_next_song_for_singer(conn, singer_id)

            return {
                'singer_id': singer_id,
                'singer_name': singer_name,
                'song': song_info
            }
        else:
            return None

    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        return None

    finally:
        conn.close()


def get_up_next_singers_and_songs():
    conn = get_db_connection()
    if not conn:
        return []  # Handle connection failure

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT singerid, name, position FROM rotationSingers ORDER BY position ASC LIMIT 1, ?",
                       (config['num_up_next'],))  # Skip current singer
        singers_data = cursor.fetchall()

        up_next = []
        for singer_data in singers_data:
            singer_id = singer_data['singerid']  # Access by column name
            singer_name = singer_data['name']
            song_info = get_next_song_for_singer(conn, singer_id)

            up_next.append({
                'singer_id': singer_id,
                'singer_name': singer_name,
                'song': song_info
            })

        return up_next

    except sqlite3.Error as e:
        logger.error(f"Database query error: {e}")
        return []

    finally:
        conn.close()


def get_next_song_for_singer(conn, singer_id):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT qs.song
            FROM queueSongs qs
            WHERE qs.singer = ? AND qs.played = 0
            ORDER BY qs.position ASC
            LIMIT 1
        """, (singer_id,))
        next_song_queue_data = cursor.fetchone()

        if next_song_queue_data:
            song_id = next_song_queue_data['song']  # Access by column name
            return get_song_details(conn, song_id)
        else:
            return None

    except sqlite3.Error as e:
        logger.error(f"Database error in get_next_song_for_singer: {e}")
        return None  # Return none in the event of a failure


def get_song_details(conn, song_id):
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ds.Title, ds.Artist
            FROM dbSongs ds
            WHERE ds.songid = ?
        """, (song_id,))
        song_data = cursor.fetchone()

        if song_data:
            return {
                'title': song_data['Title'],  # Access by column name
                'artist': song_data['Artist']  # Access by column name
            }
        else:
            return None

    except sqlite3.Error as e:
        logger.error(f"Database error in get_song_details: {e}")
        return None  # Return none in the event of a failure


# API Endpoints (Same as before)
@app.route('/')
def index():
    return render_template('index.html')  # Create a basic index.html


@app.route('/api/rotation')
def get_rotation():
    current = get_current_singer_and_song()
    up_next = get_up_next_singers_and_songs()

    return jsonify({
        'display_title': config['display_title'],
        'venue_name': config['venue_name'],
        'current': current,
        'up_next': up_next
    })


@socketio.on('connect')
def test_connect(auth):
    print('Client connected')
    emit_rotation_data()


def emit_rotation_data():
    current = get_current_singer_and_song()
    up_next = get_up_next_singers_and_songs()
    socketio.emit('rotation_update', {
        'display_title': config['display_title'],
        'venue_name': config['venue_name'],
        'current': current,
        'up_next': up_next
    })


def update_rotation_data():
    while True:
        emit_rotation_data()
        time.sleep(config['refresh_interval'])  # Use configured refresh interval


# Configuration GUI (PyQt6)
class ConfigWindow(QMainWindow):
    config_updated = pyqtSignal()

    def __init__(self, current_config):
        super().__init__()
        self.config = current_config
        self.setWindowTitle("OpenKJ Rotation Server Configuration")

        self.db_path_label_display = None
        self.num_up_next_spinbox = None
        self.server_port_spinbox = None
        self.log_level_combo = None
        self.display_title_input = None
        self.venue_name_input = None
        self.refresh_interval_spinbox = None

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.initUI()

    def initUI(self):
        # Use QFormLayout for uniform label and field alignment
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Display Title
        self.display_title_input = QLineEdit(self.config['display_title'])
        self.display_title_input.setMinimumWidth(300)
        form_layout.addRow("Display Title:", self.display_title_input)

        # Venue Name
        self.venue_name_input = QLineEdit(self.config['venue_name'])
        self.venue_name_input.setMinimumWidth(300)
        form_layout.addRow("Venue Name:", self.venue_name_input)

        # Database Path
        db_widget = QWidget()
        db_layout = QHBoxLayout(db_widget)
        db_layout.setContentsMargins(0, 0, 0, 0)
        self.db_path_label_display = QLineEdit(self.config['db_path'])
        self.db_path_label_display.setMinimumWidth(250)
        db_button = QPushButton("Browse")
        db_button.clicked.connect(self.browse_db)
        db_layout.addWidget(self.db_path_label_display, 1)
        db_layout.addWidget(db_button)
        form_layout.addRow("Database Path:", db_widget)

        # Number of Up Next Singers
        self.num_up_next_spinbox = QSpinBox()
        self.num_up_next_spinbox.setValue(self.config['num_up_next'])
        self.num_up_next_spinbox.setMinimum(1)
        self.num_up_next_spinbox.setMinimumWidth(100)
        form_layout.addRow("Number of 'Up Next' Singers:", self.num_up_next_spinbox)

        # Server Port
        self.server_port_spinbox = QSpinBox()
        self.server_port_spinbox.setValue(self.config['server_port'])
        self.server_port_spinbox.setMinimum(1024)  # Ports below 1024 require root
        self.server_port_spinbox.setMaximum(65535)
        self.server_port_spinbox.setMinimumWidth(100)
        form_layout.addRow("Server Port:", self.server_port_spinbox)

        # Refresh Interval
        self.refresh_interval_spinbox = QSpinBox()
        self.refresh_interval_spinbox.setValue(self.config['refresh_interval'])
        self.refresh_interval_spinbox.setMinimum(1)
        self.refresh_interval_spinbox.setMaximum(60)
        self.refresh_interval_spinbox.setMinimumWidth(100)
        form_layout.addRow("Refresh Interval (seconds):", self.refresh_interval_spinbox)

        # Log Level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        self.log_level_combo.setCurrentText(self.config['log_level'])
        self.log_level_combo.setMinimumWidth(150)
        form_layout.addRow("Log Level:", self.log_level_combo)

        self.layout.addLayout(form_layout)

        # Save Button
        save_button = QPushButton("Save Configuration")
        save_button.clicked.connect(self.save_config)
        self.layout.addWidget(save_button)

    def browse_db(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select openkj.sqlite Database", "",
                                                   "SQLite Database (*.sqlite *.db)")
        if file_path:
            self.db_path_label_display.setText(file_path)

    def save_config(self):
        new_config = {
            'db_path': self.db_path_label_display.text(),
            'num_up_next': self.num_up_next_spinbox.value(),
            'server_port': self.server_port_spinbox.value(),
            'log_level': self.log_level_combo.currentText(),
            'display_title': self.display_title_input.text(),
            'venue_name': self.venue_name_input.text(),
            'refresh_interval': self.refresh_interval_spinbox.value()
        }

        # Validate Configuration
        if not os.path.exists(new_config['db_path']):
            QMessageBox.warning(self, "Warning", "Invalid database path.")
            return

        try:
            int(new_config['server_port'])  # Ensure port is an integer
        except ValueError:
            QMessageBox.warning(self, "Warning", "Invalid server port.")
            return

        if new_config['log_level'].upper() not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            QMessageBox.warning(self, "Warning", "Invalid log level.")
            return

        save_config(new_config)
        global config
        config = load_config()  # Reload the config

        # Reconfigure Logging
        logger.setLevel(config['log_level'].upper())
        app.logger.setLevel(config['log_level'].upper())

        QMessageBox.information(self, "Success", "Configuration saved successfully.")
        self.config_updated.emit()
        self.close()


# System Tray Icon
def create_tray_icon(config_window):
    image = Image.new("RGB", (64, 64), color=(0, 0, 0))
    dc = ImageDraw.Draw(image)
    dc.text((10, 20), "KJ", fill=(255, 255, 255))

    def show_config(icon, item):
        config_window.show()
        config_window.raise_()
        config_window.activateWindow()

    def exit_action(icon, item):
        icon.stop()
        os._exit(0)

    icon = pystray.Icon("OpenKJ Rotation", image, "OpenKJ Rotation", menu=pystray.Menu(
        pystray.MenuItem("Show Config", show_config),
        pystray.MenuItem("Exit", exit_action)
    ))
    return icon


# Main Function (Modified)
if __name__ == '__main__':
    # Flask Portion

    # PyQt Portion
    app_pyqt = QApplication(sys.argv)
    config_window = ConfigWindow(load_config())
    config_window.hide()  # Initially Hide the window

    # Tray Icon
    tray_icon = create_tray_icon(config_window)
    tray_thread = Thread(target=tray_icon.run)
    tray_thread.daemon = True
    tray_thread.start()

    # Run the flask app in another thread
    def run_flask():
        try:
            socketio.run(app, debug=False, host='0.0.0.0', port=config['server_port'], allow_unsafe_werkzeug=True)
        except Exception as e:
            logger.error(f"Flask application error: {e}")
            tray_icon.stop()
            os._exit(1)  # Exit if Flask fails to start

    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Start the data updater thread *after* Flask is running
    time.sleep(1)  # Give Flask a moment to start
    updater_thread = Thread(target=update_rotation_data)
    updater_thread.daemon = True
    updater_thread.start()

    exit_code = app_pyqt.exec()

    tray_icon.stop()
    sys.exit(exit_code)