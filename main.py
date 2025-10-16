import sys
import os
import json
import sqlite3
import datetime
import platform
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QFileDialog, QMessageBox, QSpinBox, QHBoxLayout, QPushButton,
    QSizePolicy, QFrame, QLineEdit, QStatusBar, QGraphicsDropShadowEffect, QMenu,
    QFormLayout, QCheckBox, QComboBox, QGroupBox, QFontComboBox, QColorDialog,
    QScrollArea, QGridLayout, QTabWidget, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QFileSystemWatcher, QTimer, pyqtSignal, QTime, QEvent
from PyQt6.QtGui import QFont, QPixmap, QColor, QAction, QCursor, QMovie

def get_app_data_dir():
    """Get the OS-specific application data directory"""
    system = platform.system()
    if system == "Darwin":  # macOS
        app_dir = Path.home() / "Library" / "Application Support" / "OpenKJ-Next-Singer-Display"
    elif system == "Windows":
        app_dir = Path(os.environ.get('APPDATA', Path.home())) / "OpenKJ-Next-Singer-Display"
    else:  # Linux and others
        app_dir = Path.home() / ".local" / "share" / "OpenKJ-Next-Singer-Display"
    
    # Create directory if it doesn't exist
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

# Get app data directory and config file path
APP_DATA_DIR = get_app_data_dir()
CONFIG_FILE = APP_DATA_DIR / 'config.json'
MEDIA_DIR = APP_DATA_DIR / 'media'

# Create media directory if it doesn't exist
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_NUM_SINGERS = 5
DEFAULT_CONFIG = {
    'db_path': None,
    'num_singers': DEFAULT_NUM_SINGERS,
    'display_title': 'Karaoke Singer Rotation',
    'logo_path': None,
    'venue_name': "Harry's Bar",
    'refresh_interval': 5,
    'accepting_requests': True,
    # Background settings
    'background_color': '#161619',
    'background_image': None,
    'background_type': 'color',  # 'color', 'image', 'gradient'
    'gradient_start_color': '#161619',
    'gradient_end_color': '#2a2a2d',
    'gradient_direction': 'vertical',  # 'vertical', 'horizontal', 'diagonal'
    # Font settings
    'font_display_title': {'family': 'Arial', 'size': 48, 'bold': True, 'italic': False},
    'font_venue_name': {'family': 'Arial', 'size': 32, 'bold': True, 'italic': False},
    'font_current_singer': {'family': 'Arial', 'size': 38, 'bold': False, 'italic': False},
    'font_current_song': {'family': 'Arial', 'size': 24, 'bold': False, 'italic': False},
    'font_up_next_singer': {'family': 'Arial', 'size': 30, 'bold': True, 'italic': False},
    'font_up_next_song': {'family': 'Arial', 'size': 20, 'bold': False, 'italic': True},
    # Overlay settings
    'overlay_enabled': True,
    'overlay_duration': 20  # seconds
}

def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                config_with_defaults = DEFAULT_CONFIG.copy()
                
                # Deep merge for font configurations
                for key in config:
                    if key.startswith('font_') and isinstance(config[key], dict):
                        # Merge font config with defaults
                        default_font = DEFAULT_CONFIG.get(key, {}).copy()
                        default_font.update(config[key])
                        config_with_defaults[key] = default_font
                    else:
                        config_with_defaults[key] = config[key]
                
                return config_with_defaults
        except (json.JSONDecodeError, Exception):
            # Config is corrupted, return defaults
            return DEFAULT_CONFIG.copy()
    else:
        return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


class ConfigWindow(QDialog):
    config_updated = pyqtSignal()

    def __init__(self, config, main_app):
        super().__init__()
        self.config = config
        self.main_app = main_app
        self.setWindowTitle("Configuration")
        self.setMinimumSize(700, 600)
        
        # Store current config values
        self.db_path = config.get('db_path')
        self.num_singers = config.get('num_singers', DEFAULT_NUM_SINGERS)
        self.display_title = config.get('display_title', DEFAULT_CONFIG['display_title'])
        self.logo_path = config.get('logo_path', DEFAULT_CONFIG['logo_path'])
        self.venue_name = config.get('venue_name', DEFAULT_CONFIG['venue_name'])
        self.refresh_interval = config.get('refresh_interval', DEFAULT_CONFIG['refresh_interval'])
        self.accepting_requests = config.get('accepting_requests', DEFAULT_CONFIG['accepting_requests'])
        
        # Background settings
        self.background_color = config.get('background_color', DEFAULT_CONFIG['background_color'])
        self.background_image = config.get('background_image', DEFAULT_CONFIG['background_image'])
        self.background_type = config.get('background_type', DEFAULT_CONFIG['background_type'])
        self.gradient_start_color = config.get('gradient_start_color', DEFAULT_CONFIG['gradient_start_color'])
        self.gradient_end_color = config.get('gradient_end_color', DEFAULT_CONFIG['gradient_end_color'])
        self.gradient_direction = config.get('gradient_direction', DEFAULT_CONFIG['gradient_direction'])
        
        # Font settings
        self.font_display_title = config.get('font_display_title', DEFAULT_CONFIG['font_display_title'].copy())
        self.font_venue_name = config.get('font_venue_name', DEFAULT_CONFIG['font_venue_name'].copy())
        self.font_current_singer = config.get('font_current_singer', DEFAULT_CONFIG['font_current_singer'].copy())
        self.font_current_song = config.get('font_current_song', DEFAULT_CONFIG['font_current_song'].copy())
        self.font_up_next_singer = config.get('font_up_next_singer', DEFAULT_CONFIG['font_up_next_singer'].copy())
        self.font_up_next_song = config.get('font_up_next_song', DEFAULT_CONFIG['font_up_next_song'].copy())
        
        # Overlay settings
        self.overlay_enabled = config.get('overlay_enabled', DEFAULT_CONFIG['overlay_enabled'])
        self.overlay_duration = config.get('overlay_duration', DEFAULT_CONFIG['overlay_duration'])

        self.initUI()

    def initUI(self):
        # Main layout for dialog
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a scroll area for the main content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_widget = QWidget()
        content_layout = QVBoxLayout(scroll_widget)
        
        # Create tab widget
        tabs = QTabWidget()
        
        # Tab 1: General Settings
        general_tab = self.create_general_tab()
        tabs.addTab(general_tab, "General")
        
        # Tab 2: Background Settings
        background_tab = self.create_background_tab()
        tabs.addTab(background_tab, "Background")
        
        # Tab 3: Font Settings
        font_tab = self.create_font_tab()
        tabs.addTab(font_tab, "Fonts")
        
        # Tab 4: Overlay Settings
        overlay_tab = self.create_overlay_tab()
        tabs.addTab(overlay_tab, "Singer Change Overlay")
        
        content_layout.addWidget(tabs)
        scroll.setWidget(scroll_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll)
        
        # Create standard dialog button box
        button_box = QDialogButtonBox()
        
        # Add "Reset To Defaults" button on the left
        reset_button = button_box.addButton("Reset To Defaults", QDialogButtonBox.ButtonRole.ResetRole)
        reset_button.clicked.connect(self.reset_to_default)
        
        # Add "Discard Changes" button (Reject role)
        discard_button = button_box.addButton("Discard Changes", QDialogButtonBox.ButtonRole.RejectRole)
        discard_button.clicked.connect(self.reject)
        
        # Add "Save Changes" button (Accept role)
        save_button = button_box.addButton("Save Changes", QDialogButtonBox.ButtonRole.AcceptRole)
        save_button.clicked.connect(self.save_config)
        save_button.setDefault(True)
        
        main_layout.addWidget(button_box)
        
        # Load and apply the style.qss stylesheet to this dialog only
        try:
            qss_path = Path(__file__).parent / 'style.qss'
            if qss_path.exists():
                with open(qss_path, 'r') as f:
                    stylesheet = f.read()
                    self.setStyleSheet(stylesheet)
        except Exception as e:
            print(f"Warning: Could not load style.qss: {e}")
    
    def create_general_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Basic Settings Group
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QFormLayout()
        basic_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        basic_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Rotation Title Configuration
        self.title_input = QLineEdit(self.display_title)
        self.title_input.setMinimumWidth(300)
        basic_layout.addRow("Rotation Title:", self.title_input)
        
        # Venue Name Configuration
        self.venue_name_input = QLineEdit(self.venue_name)
        self.venue_name_input.setMinimumWidth(300)
        basic_layout.addRow("Venue Name:", self.venue_name_input)
        
        # Number of Up Next Configuration
        self.num_singers_spinbox = QSpinBox()
        self.num_singers_spinbox.setValue(self.num_singers)
        self.num_singers_spinbox.setMinimum(1)
        self.num_singers_spinbox.setMaximum(6)
        self.num_singers_spinbox.setMinimumWidth(100)
        basic_layout.addRow("Number of Up Next:", self.num_singers_spinbox)
        
        # Refresh Interval Configuration
        self.refresh_interval_spinbox = QSpinBox()
        self.refresh_interval_spinbox.setValue(self.refresh_interval)
        self.refresh_interval_spinbox.setMinimum(5)
        self.refresh_interval_spinbox.setMaximum(20)
        self.refresh_interval_spinbox.setMinimumWidth(100)
        basic_layout.addRow("Refresh Interval (seconds):", self.refresh_interval_spinbox)
        
        # Accepting Requests Configuration
        self.accepting_requests_checkbox = QCheckBox()
        self.accepting_requests_checkbox.setChecked(self.accepting_requests)
        basic_layout.addRow("Accepting Requests:", self.accepting_requests_checkbox)
        
        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)
        
        # Database Settings Group
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout()
        db_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        db_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Database Path Configuration
        db_widget = QWidget()
        db_hlayout = QHBoxLayout(db_widget)
        db_hlayout.setContentsMargins(0, 0, 0, 0)
        self.db_path_label_display = QLabel(self.db_path if self.db_path else "No database selected")
        self.db_path_label_display.setWordWrap(True)
        self.db_path_label_display.setMinimumWidth(200)
        locate_db_button = QPushButton("Locate OpenKJ DB")
        locate_db_button.clicked.connect(self.locate_db)
        db_hlayout.addWidget(self.db_path_label_display, 1)
        db_hlayout.addWidget(locate_db_button)
        db_layout.addRow("OpenKJ Database:", db_widget)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # Logo Settings Group
        logo_group = QGroupBox("Logo Settings")
        logo_layout = QFormLayout()
        logo_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        logo_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Logo Path Configuration
        logo_widget = QWidget()
        logo_hlayout = QHBoxLayout(logo_widget)
        logo_hlayout.setContentsMargins(0, 0, 0, 0)
        self.logo_path_label_display = QLabel(os.path.basename(self.logo_path) if self.logo_path else "No logo selected")
        self.logo_path_label_display.setMinimumWidth(200)
        logo_button = QPushButton("Browse")
        logo_button.clicked.connect(self.browse_logo)
        logo_hlayout.addWidget(self.logo_path_label_display, 1)
        logo_hlayout.addWidget(logo_button)
        logo_layout.addRow("Logo:", logo_widget)
        
        logo_group.setLayout(logo_layout)
        layout.addWidget(logo_group)
        
        layout.addStretch()
        return tab
    
    def create_background_tab(self):
        """Create the background settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        bg_group = QGroupBox("Background Settings")
        bg_layout = QFormLayout()
        bg_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        bg_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Background Type
        self.bg_type_combo = QComboBox()
        self.bg_type_combo.addItems(['Solid Color', 'Image', 'Gradient'])
        type_map = {'color': 0, 'image': 1, 'gradient': 2}
        self.bg_type_combo.setCurrentIndex(type_map.get(self.background_type, 0))
        self.bg_type_combo.currentIndexChanged.connect(self.on_background_type_changed)
        bg_layout.addRow("Background Type:", self.bg_type_combo)
        
        # Solid Color
        self.bg_color_widget = QWidget()
        bg_color_layout = QHBoxLayout(self.bg_color_widget)
        bg_color_layout.setContentsMargins(0, 0, 0, 0)
        self.bg_color_display = QLabel()
        self.bg_color_display.setFixedSize(100, 30)
        self.bg_color_display.setStyleSheet(f"background-color: {self.background_color}; border: 1px solid #ccc;")
        bg_color_button = QPushButton("Choose Color")
        bg_color_button.clicked.connect(self.choose_bg_color)
        bg_color_layout.addWidget(self.bg_color_display)
        bg_color_layout.addWidget(bg_color_button)
        bg_color_layout.addStretch()
        bg_layout.addRow("Background Color:", self.bg_color_widget)
        
        # Background Image
        self.bg_image_widget = QWidget()
        bg_image_layout = QHBoxLayout(self.bg_image_widget)
        bg_image_layout.setContentsMargins(0, 0, 0, 0)
        self.bg_image_display = QLabel(os.path.basename(self.background_image) if self.background_image else "No image selected")
        self.bg_image_display.setMinimumWidth(200)
        self.bg_image_display.setWordWrap(True)
        bg_image_button = QPushButton("Browse")
        bg_image_button.clicked.connect(self.browse_bg_image)
        bg_image_layout.addWidget(self.bg_image_display, 1)
        bg_image_layout.addWidget(bg_image_button)
        bg_layout.addRow("Background Image:", self.bg_image_widget)
        
        # Gradient Settings
        self.gradient_widget = QWidget()
        gradient_layout = QVBoxLayout(self.gradient_widget)
        gradient_layout.setContentsMargins(0, 0, 0, 0)
        
        # Gradient Start Color
        gradient_start_layout = QHBoxLayout()
        self.gradient_start_display = QLabel()
        self.gradient_start_display.setFixedSize(100, 30)
        self.gradient_start_display.setStyleSheet(f"background-color: {self.gradient_start_color}; border: 1px solid #ccc;")
        gradient_start_button = QPushButton("Choose Start Color")
        gradient_start_button.clicked.connect(self.choose_gradient_start)
        gradient_start_layout.addWidget(self.gradient_start_display)
        gradient_start_layout.addWidget(gradient_start_button)
        gradient_start_layout.addStretch()
        
        # Gradient End Color
        gradient_end_layout = QHBoxLayout()
        self.gradient_end_display = QLabel()
        self.gradient_end_display.setFixedSize(100, 30)
        self.gradient_end_display.setStyleSheet(f"background-color: {self.gradient_end_color}; border: 1px solid #ccc;")
        gradient_end_button = QPushButton("Choose End Color")
        gradient_end_button.clicked.connect(self.choose_gradient_end)
        gradient_end_layout.addWidget(self.gradient_end_display)
        gradient_end_layout.addWidget(gradient_end_button)
        gradient_end_layout.addStretch()
        
        # Gradient Direction
        gradient_dir_layout = QHBoxLayout()
        self.gradient_direction_combo = QComboBox()
        self.gradient_direction_combo.addItems(['Vertical', 'Horizontal', 'Diagonal'])
        dir_map = {'vertical': 0, 'horizontal': 1, 'diagonal': 2}
        self.gradient_direction_combo.setCurrentIndex(dir_map.get(self.gradient_direction, 0))
        gradient_dir_layout.addWidget(QLabel("Direction:"))
        gradient_dir_layout.addWidget(self.gradient_direction_combo)
        gradient_dir_layout.addStretch()
        
        gradient_layout.addLayout(gradient_start_layout)
        gradient_layout.addLayout(gradient_end_layout)
        gradient_layout.addLayout(gradient_dir_layout)
        
        bg_layout.addRow("Gradient Settings:", self.gradient_widget)
        
        bg_group.setLayout(bg_layout)
        layout.addWidget(bg_group)
        layout.addStretch()
        
        # Update visibility based on current type
        self.on_background_type_changed()
        
        return tab
    
    def create_font_tab(self):
        """Create the font settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create font settings for each element
        font_configs = [
            ("Display Title", "font_display_title"),
            ("Venue Name", "font_venue_name"),
            ("Current Singer Name", "font_current_singer"),
            ("Current Song", "font_current_song"),
            ("Up Next Singer Name", "font_up_next_singer"),
            ("Up Next Song", "font_up_next_song")
        ]
        
        self.font_widgets = {}
        
        for label, attr in font_configs:
            group = QGroupBox(label)
            group_layout = QFormLayout()
            group_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
            group_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            font_data = getattr(self, attr)
            
            # Font Family
            font_family = QFontComboBox()
            font_family.setCurrentFont(QFont(font_data.get('family', 'Arial')))
            
            # Font Size
            font_size = QSpinBox()
            font_size.setValue(font_data.get('size', 24))
            font_size.setMinimum(8)
            font_size.setMaximum(144)
            
            # Bold Checkbox
            font_bold = QCheckBox("Bold")
            font_bold.setChecked(font_data.get('bold', False))
            
            # Italic Checkbox
            font_italic = QCheckBox("Italic")
            font_italic.setChecked(font_data.get('italic', False))
            
            group_layout.addRow("Font Family:", font_family)
            group_layout.addRow("Font Size:", font_size)
            
            style_layout = QHBoxLayout()
            style_layout.addWidget(font_bold)
            style_layout.addWidget(font_italic)
            style_layout.addStretch()
            group_layout.addRow("Font Style:", style_layout)
            
            group.setLayout(group_layout)
            layout.addWidget(group)
            
            # Store references
            self.font_widgets[attr] = {
                'family': font_family,
                'size': font_size,
                'bold': font_bold,
                'italic': font_italic
            }
        
        layout.addStretch()
        return tab
    
    def create_overlay_tab(self):
        """Create the singer change overlay settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        overlay_group = QGroupBox("Singer Change Overlay Settings")
        overlay_layout = QFormLayout()
        overlay_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        overlay_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Enable Overlay
        self.overlay_enabled_checkbox = QCheckBox()
        self.overlay_enabled_checkbox.setChecked(self.overlay_enabled)
        overlay_layout.addRow("Enable Singer Change Overlay:", self.overlay_enabled_checkbox)
        
        # Overlay Duration
        self.overlay_duration_spinbox = QSpinBox()
        self.overlay_duration_spinbox.setValue(self.overlay_duration)
        self.overlay_duration_spinbox.setMinimum(5)
        self.overlay_duration_spinbox.setMaximum(60)
        self.overlay_duration_spinbox.setSuffix(" seconds")
        overlay_layout.addRow("Overlay Duration:", self.overlay_duration_spinbox)
        
        # Description
        desc_label = QLabel(
            "When enabled, a full-screen overlay will be displayed when the current singer changes.\n"
            "The overlay shows:\n"
            '  • "The next performer is" centered at the top\n'
            "  • New singer name centered below (slightly larger)\n"
            "  • New song title and artist\n\n"
            "The overlay will automatically hide after the specified duration."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        overlay_layout.addRow(desc_label)
        
        overlay_group.setLayout(overlay_layout)
        layout.addWidget(overlay_group)
        layout.addStretch()
        
        return tab
    
    def on_background_type_changed(self):
        """Show/hide background settings based on selected type"""
        bg_type = self.bg_type_combo.currentIndex()
        
        # 0 = color, 1 = image, 2 = gradient
        self.bg_color_widget.setVisible(bg_type == 0)
        self.bg_image_widget.setVisible(bg_type == 1)
        self.gradient_widget.setVisible(bg_type == 2)
    
    def choose_bg_color(self):
        """Open color picker for background color"""
        color = QColorDialog.getColor(QColor(self.background_color), self)
        if color.isValid():
            self.background_color = color.name()
            self.bg_color_display.setStyleSheet(f"background-color: {self.background_color}; border: 1px solid #ccc;")
    
    def browse_bg_image(self):
        """Browse for background image and copy it to app directory"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "Select Background Image", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            try:
                # Copy file to media directory
                file_name = Path(file_path).name
                dest_path = MEDIA_DIR / f"bg_image_{file_name}"
                shutil.copy2(file_path, dest_path)
                
                self.background_image = str(dest_path)
                self.bg_image_display.setText(os.path.basename(file_path))
                QMessageBox.information(
                    self, 
                    "Success", 
                    f"Background image copied to application directory."
                )
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Failed to copy image: {str(e)}"
                )
    
    def choose_gradient_start(self):
        """Open color picker for gradient start color"""
        color = QColorDialog.getColor(QColor(self.gradient_start_color), self)
        if color.isValid():
            self.gradient_start_color = color.name()
            self.gradient_start_display.setStyleSheet(f"background-color: {self.gradient_start_color}; border: 1px solid #ccc;")
    
    def choose_gradient_end(self):
        """Open color picker for gradient end color"""
        color = QColorDialog.getColor(QColor(self.gradient_end_color), self)
        if color.isValid():
            self.gradient_end_color = color.name()
            self.gradient_end_display.setStyleSheet(f"background-color: {self.gradient_end_color}; border: 1px solid #ccc;")

    def browse_db(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Select openkj.sqlite Database", "", "SQLite Database (*.sqlite *.db)")
        if file_path:
            self.db_path = file_path
            self.db_path_label_display.setText(self.db_path)

    def browse_logo(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "Select Logo Image", 
            "", 
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            try:
                # Copy file to media directory
                file_name = Path(file_path).name
                dest_path = MEDIA_DIR / f"logo_{file_name}"
                shutil.copy2(file_path, dest_path)
                
                self.logo_path = str(dest_path)
                self.logo_path_label_display.setText(os.path.basename(file_path))
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Failed to copy logo: {str(e)}"
                )

    def locate_db(self):
        """Attempt to automatically locate the OpenKJ database based on OS"""
        system = platform.system()
        potential_path = None
        
        if system == "Darwin":  # macOS
            potential_path = os.path.expanduser("~/Library/Application Support/OpenKJ/OpenKJ/openkj.sqlite")
        elif system == "Windows":
            potential_path = os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\OpenKJ\OpenKJ\openkj.sqlite")
        
        if potential_path and os.path.exists(potential_path):
            self.db_path = potential_path
            self.db_path_label_display.setText(self.db_path)
            QMessageBox.information(self, "Success", f"Database found at:\n{potential_path}")
        else:
            # Database not found, show browse dialog
            QMessageBox.information(self, "Not Found", 
                                  "Could not automatically locate the OpenKJ database.\n"
                                  "Please select it manually.")
            file_dialog = QFileDialog()
            file_path, _ = file_dialog.getOpenFileName(self, "Select openkj.sqlite Database", "", 
                                                       "SQLite Database (*.sqlite *.db)")
            if file_path:
                self.db_path = file_path
                self.db_path_label_display.setText(self.db_path)
    
    def reset_to_default(self):
        """Reset all settings to default values"""
        reply = QMessageBox.question(
            self, 
            "Reset to Default", 
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Reset all values to defaults (except db_path)
            self.title_input.setText(DEFAULT_CONFIG['display_title'])
            self.venue_name_input.setText(DEFAULT_CONFIG['venue_name'])
            self.num_singers_spinbox.setValue(DEFAULT_CONFIG['num_singers'])
            self.refresh_interval_spinbox.setValue(DEFAULT_CONFIG['refresh_interval'])
            self.accepting_requests_checkbox.setChecked(DEFAULT_CONFIG['accepting_requests'])
            
            # Reset background settings
            self.background_color = DEFAULT_CONFIG['background_color']
            self.background_image = DEFAULT_CONFIG['background_image']
            self.background_type = DEFAULT_CONFIG['background_type']
            self.gradient_start_color = DEFAULT_CONFIG['gradient_start_color']
            self.gradient_end_color = DEFAULT_CONFIG['gradient_end_color']
            self.gradient_direction = DEFAULT_CONFIG['gradient_direction']
            
            type_map = {'color': 0, 'image': 1, 'gradient': 2}
            self.bg_type_combo.setCurrentIndex(type_map.get(self.background_type, 0))
            self.bg_color_display.setStyleSheet(f"background-color: {self.background_color}; border: 1px solid #ccc;")
            self.bg_image_display.setText("No image selected")
            self.gradient_start_display.setStyleSheet(f"background-color: {self.gradient_start_color}; border: 1px solid #ccc;")
            self.gradient_end_display.setStyleSheet(f"background-color: {self.gradient_end_color}; border: 1px solid #ccc;")
            dir_map = {'vertical': 0, 'horizontal': 1, 'diagonal': 2}
            self.gradient_direction_combo.setCurrentIndex(dir_map.get(self.gradient_direction, 0))
            
            # Reset font settings
            for attr in ['font_display_title', 'font_venue_name', 'font_current_singer', 
                        'font_current_song', 'font_up_next_singer', 'font_up_next_song']:
                default_font = DEFAULT_CONFIG[attr].copy()
                widgets = self.font_widgets[attr]
                widgets['family'].setCurrentFont(QFont(default_font['family']))
                widgets['size'].setValue(default_font['size'])
                widgets['bold'].setChecked(default_font['bold'])
                widgets['italic'].setChecked(default_font['italic'])
            
            # Reset overlay settings
            self.overlay_enabled_checkbox.setChecked(DEFAULT_CONFIG['overlay_enabled'])
            self.overlay_duration_spinbox.setValue(DEFAULT_CONFIG['overlay_duration'])
            
            QMessageBox.information(self, "Success", "Settings have been reset to default values.")

    def save_config(self):
        if not self.db_path:
            QMessageBox.warning(self, "Warning", "Please select a database file.")
            return

        self.num_singers = self.num_singers_spinbox.value()
        self.display_title = self.title_input.text()
        self.venue_name = self.venue_name_input.text()
        self.refresh_interval = self.refresh_interval_spinbox.value()
        self.accepting_requests = self.accepting_requests_checkbox.isChecked()
        
        # Background settings
        bg_type_map = {0: 'color', 1: 'image', 2: 'gradient'}
        self.background_type = bg_type_map[self.bg_type_combo.currentIndex()]
        
        dir_map = {0: 'vertical', 1: 'horizontal', 2: 'diagonal'}
        self.gradient_direction = dir_map[self.gradient_direction_combo.currentIndex()]
        
        # Font settings
        for attr, widgets in self.font_widgets.items():
            font_config = {
                'family': widgets['family'].currentFont().family(),
                'size': widgets['size'].value(),
                'bold': widgets['bold'].isChecked(),
                'italic': widgets['italic'].isChecked()
            }
            setattr(self, attr, font_config)
        
        # Overlay settings
        self.overlay_enabled = self.overlay_enabled_checkbox.isChecked()
        self.overlay_duration = self.overlay_duration_spinbox.value()
        
        # Update config dict
        self.config['db_path'] = self.db_path
        self.config['num_singers'] = self.num_singers
        self.config['display_title'] = self.display_title
        self.config['logo_path'] = self.logo_path
        self.config['venue_name'] = self.venue_name
        self.config['refresh_interval'] = self.refresh_interval
        self.config['accepting_requests'] = self.accepting_requests
        self.config['background_color'] = self.background_color
        self.config['background_image'] = self.background_image
        self.config['background_type'] = self.background_type
        self.config['gradient_start_color'] = self.gradient_start_color
        self.config['gradient_end_color'] = self.gradient_end_color
        self.config['gradient_direction'] = self.gradient_direction
        self.config['font_display_title'] = self.font_display_title
        self.config['font_venue_name'] = self.font_venue_name
        self.config['font_current_singer'] = self.font_current_singer
        self.config['font_current_song'] = self.font_current_song
        self.config['font_up_next_singer'] = self.font_up_next_singer
        self.config['font_up_next_song'] = self.font_up_next_song
        self.config['overlay_enabled'] = self.overlay_enabled
        self.config['overlay_duration'] = self.overlay_duration

        save_config(self.config)
        QMessageBox.information(self, "Success", "Configuration saved successfully.")
        self.config_updated.emit()
        self.accept()


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
        self.main_app = None  # Will be set by MainApp
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
        
        # Track previous singer for overlay detection
        self.previous_singer_id = None
        self.previous_singer_name = None
        
        # Fullscreen toggle button
        self.fullscreen_button = QPushButton("")
        self.fullscreen_button.setFixedSize(200, 50)
        self.fullscreen_button.hide()
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        
        # Track mouse for fullscreen button
        self.setMouseTracking(True)

        self.initUI()
        self.update_display()
        
        # Use refresh_interval from config (in milliseconds)
        refresh_interval_ms = self.config.get('refresh_interval', 5) * 1000
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.check_db_modified)
        self.refresh_timer.start(refresh_interval_ms)

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
        
        # Add fullscreen toggle button (floating)
        self.fullscreen_button.setParent(central_widget)
        self.fullscreen_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                border: 2px solid #555;
                border-radius: 5px;
                font-size: 16px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgba(50, 50, 50, 200);
            }
        """)
        self.update_fullscreen_button_text()
        self.position_fullscreen_button()

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
        accepting_requests = self.config.get('accepting_requests', DEFAULT_CONFIG['accepting_requests'])
        requests_text = "Accepting Requests" if accepting_requests else "Not Accepting Requests"
        self.requests_label = QLabel(requests_text)
        self.requests_label.setObjectName("requestsLabel")
        self.status_bar.addPermanentWidget(self.requests_label)

        # Apply styles dynamically from config
        self.apply_styles()
    
    def apply_styles(self):
        """Apply dynamic styles based on configuration"""
        # Get background settings
        bg_type = self.config.get('background_type', 'color')
        bg_color = self.config.get('background_color', '#161619')
        bg_image = self.config.get('background_image')
        gradient_start = self.config.get('gradient_start_color', '#161619')
        gradient_end = self.config.get('gradient_end_color', '#2a2a2d')
        gradient_dir = self.config.get('gradient_direction', 'vertical')
        
        # Build background style
        if bg_type == 'color':
            background_style = f"background-color: {bg_color};"
        elif bg_type == 'image' and bg_image and os.path.exists(bg_image):
            # Handle GIF animations with QMovie or regular images
            if bg_image.lower().endswith('.gif'):
                # For GIFs, we'll use transparent background and let QMovie handle it
                background_style = f"background-color: {bg_color};"
            else:
                # Add a semi-transparent dark overlay for better text readability
                background_style = f"""
                    background-image: url({bg_image}); 
                    background-position: center; 
                    background-repeat: no-repeat; 
                    background-attachment: fixed;
                """
        elif bg_type == 'gradient':
            if gradient_dir == 'vertical':
                gradient_style = f"qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {gradient_start}, stop:1 {gradient_end})"
            elif gradient_dir == 'horizontal':
                gradient_style = f"qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {gradient_start}, stop:1 {gradient_end})"
            else:  # diagonal
                gradient_style = f"qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {gradient_start}, stop:1 {gradient_end})"
            background_style = f"background: {gradient_style};"
        else:
            background_style = f"background-color: {bg_color};"
        
        # Get font settings
        font_display_title = self.config.get('font_display_title', DEFAULT_CONFIG['font_display_title'])
        font_venue_name = self.config.get('font_venue_name', DEFAULT_CONFIG['font_venue_name'])
        font_current_singer = self.config.get('font_current_singer', DEFAULT_CONFIG['font_current_singer'])
        font_current_song = self.config.get('font_current_song', DEFAULT_CONFIG['font_current_song'])
        font_up_next_singer = self.config.get('font_up_next_singer', DEFAULT_CONFIG['font_up_next_singer'])
        font_up_next_song = self.config.get('font_up_next_song', DEFAULT_CONFIG['font_up_next_song'])
        
        # Helper function to create font style string
        def font_style(font_config):
            family = font_config.get('family', 'Arial')
            size = font_config.get('size', 24)
            bold = 'bold' if font_config.get('bold', False) else 'normal'
            italic = 'italic' if font_config.get('italic', False) else 'normal'
            return f"font-family: '{family}'; font-size: {size}px; font-weight: {bold}; font-style: {italic};"
        
        # Add semi-transparent overlay styling for sections when using image background
        section_background = "background: transparent;"
        if bg_type == 'image' and bg_image and os.path.exists(bg_image):
            # Add semi-transparent dark background to sections for better readability
            section_background = "background: rgba(0, 0, 0, 0.6);"
        
        # Build complete stylesheet
        stylesheet = f"""
            QMainWindow {{
                {background_style}
                color: #eee;
            }}
            QLabel {{
                color: #eee;
                font-size: 24px;
            }}
            #leftSection {{
                {section_background}
            }}
            #rightSection {{
                {section_background}
            }}
            #venueLabel {{
                {font_style(font_venue_name)}
                margin-bottom: 10px;
                text-align: center;
            }}
            #displayTitle {{
                {font_style(font_display_title)}
                margin-bottom: 10px;
                text-align: center;
            }}
            #titleSeparator {{
                background-color: #cdceec;
                color: #cdceec;
                margin-bottom: 20px;
                height: 1px;
            }}
            #sectionHeading {{
                font-size: 32px;
                margin-bottom: 25px;
                text-align: center;
            }}
            #currentSingerName {{
                {font_style(font_current_singer)}
                text-align: center;
            }}
            #singingLabel {{
                font-size: 18px;
                text-align: center;
                font-style: italic;
            }}
            #currentSongName {{
                {font_style(font_current_song)}
                text-align: center;
            }}
            #upNextSingerName {{
                {font_style(font_up_next_singer)}
                margin-bottom: 5px;
                text-align: center;
            }}
            #upNextSongName {{
                {font_style(font_up_next_song)}
                margin-bottom: 10px;
                text-align: center;
            }}
             #upNextSeparator {{
                background-color: #3b3c3c;
                color: 353738;
                height: 1px;
                margin-top: 10px;
                margin-bottom: 10px;
             }}
            #messageOverlay {{
                background-color: rgba(0, 0, 0, 190);
                color: #fff;
                font-size: 72px;
                font-weight: bold; 
            }}
            #requestsLabel {{
                font-size: 36px;
                color: #00a800;
                margin-right: 10px;
            }}
            #clock {{
                font-size: 36px;
                color: #eee;
                margin-left: 10px;
            }}
            #currentPerformerFrame, #upNextFrame {{
               border: 1px solid #353738;
               border-radius: 2px;
               margin-bottom: 15px;
               padding: 10px;
            }}
            #statusBar {{
                background: transparent;
                border: 1px solid #656565;
                color: #eee;                
            }}
        """
        
        self.setStyleSheet(stylesheet)

    def resizeEvent(self, event):
        if hasattr(self, 'message_overlay_label') and self.message_overlay_label.parentWidget():
            self.message_overlay_label.setGeometry(self.centralWidget().rect())
        if hasattr(self, 'fullscreen_button'):
            self.position_fullscreen_button()
        super().resizeEvent(event)
    
    def position_fullscreen_button(self):
        """Position the fullscreen button at the bottom center"""
        if self.centralWidget():
            button_x = (self.centralWidget().width() - self.fullscreen_button.width()) // 2
            button_y = self.centralWidget().height() - self.fullscreen_button.height() - 20
            self.fullscreen_button.move(button_x, button_y)
            self.fullscreen_button.raise_()
    
    def update_fullscreen_button_text(self):
        """Update button text based on fullscreen state"""
        if self.isFullScreen():
            self.fullscreen_button.setText("Make Windowed")
        else:
            self.fullscreen_button.setText("Make Fullscreen")
    
    def toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode"""
        if self.isFullScreen():
            self.showNormal()
            self.showMaximized()
        else:
            self.showFullScreen()
        self.update_fullscreen_button_text()
    
    def mouseMoveEvent(self, event):
        """Show/hide fullscreen button on mouse hover"""
        if hasattr(self, 'fullscreen_button'):
            self.fullscreen_button.show()
            # Hide after 3 seconds of no movement
            if hasattr(self, 'hide_button_timer'):
                self.hide_button_timer.stop()
            else:
                self.hide_button_timer = QTimer()
                self.hide_button_timer.timeout.connect(self.fullscreen_button.hide)
            self.hide_button_timer.start(3000)
        super().mouseMoveEvent(event)
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click"""
        context_menu = QMenu(self)
        
        # Fullscreen/Windowed toggle
        if self.isFullScreen():
            fullscreen_action = QAction("Make Windowed", self)
        else:
            fullscreen_action = QAction("Make Fullscreen", self)
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        context_menu.addAction(fullscreen_action)
        
        # Show Config
        config_action = QAction("Show Config", self)
        config_action.triggered.connect(self.show_config)
        context_menu.addAction(config_action)
        
        # Close
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        context_menu.addAction(close_action)
        
        context_menu.exec(event.globalPos())
    
    def show_config(self):
        """Show the configuration window"""
        if self.main_app:
            self.main_app.show_config_window()

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
        
        # Update requests label based on config
        accepting_requests = self.config.get('accepting_requests', DEFAULT_CONFIG['accepting_requests'])
        requests_text = "Accepting Requests" if accepting_requests else "Not Accepting Requests"
        self.requests_label.setText(requests_text)
        
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
                
                # Check if singer has changed and overlay is enabled
                overlay_enabled = self.config.get('overlay_enabled', DEFAULT_CONFIG['overlay_enabled'])
                if overlay_enabled and self.previous_singer_id is not None and self.previous_singer_id != current_singer_id:
                    # Singer has changed, show overlay
                    current_song_info = self.get_next_song_for_singer(cursor, current_singer_id)
                    self.show_singer_change_overlay(current_singer_name, current_song_info)
                
                # Update previous singer tracking
                self.previous_singer_id = current_singer_id
                self.previous_singer_name = current_singer_name
                
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
    
    def show_singer_change_overlay(self, singer_name, song_info):
        """Show overlay when singer changes"""
        overlay_duration = self.config.get('overlay_duration', DEFAULT_CONFIG['overlay_duration'])
        
        # Build overlay text
        overlay_text = f"The next performer is\n\n{singer_name}"
        if song_info:
            overlay_text += f"\n\nPerforming\n{song_info}"
        
        self.message_overlay_label.setText(overlay_text)
        self.message_overlay_label.show()
        
        # Hide overlay after duration
        QTimer.singleShot(overlay_duration * 1000, self.hide_message_overlay)

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
            self.display_window.main_app = self  # Set reference to MainApp
        else:
            # Reload config and apply new styles
            self.display_window.config = self.config
            self.display_window.apply_styles()
        self.display_window.update_display()
        self.display_window.show()

        if self.config_window and self.config_window.isVisible():
            self.config_window.close()

    def run(self):
        self.load_config_and_show_display()
        sys.exit(self.app.exec())


if __name__ == '__main__':
    main_app = MainApp()
    main_app.run()