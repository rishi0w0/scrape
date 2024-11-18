import sys
import os
import time
import threading
import ctypes
import logging
from typing import List, Tuple, Optional
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QLineEdit, QPushButton, QListWidget, QTabWidget, 
                            QListWidgetItem, QMessageBox, QFormLayout, QFrame)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('website_blocker.log'),
        logging.StreamHandler()
    ]
)

class BlockerException(Exception):
    """Custom exception for website blocker specific errors"""
    pass

class HostsFileManager:
    """Manages operations on the hosts file"""
    def __init__(self):
        self.hosts_path = "/etc/hosts" if os.name != 'nt' else r"C:\Windows\System32\drivers\etc\hosts"
        self.redirect = "127.0.0.1"
        self._lock = threading.Lock()

    def validate_website(self, website: str) -> bool:
        """Validate website format"""
        website = website.strip()
        if not website:
            return False
        # Basic domain validation
        return all(char in '.-_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789' for char in website)

    def add_websites(self, websites: List[str]) -> None:
        """Add websites to hosts file"""
        try:
            with self._lock:
                with open(self.hosts_path, "a") as file:
                    for website in websites:
                        if self.validate_website(website):
                            entry = f"{self.redirect} {website.strip()}\n"
                            file.write(entry)
                            logging.info(f"Added website to hosts file: {website}")
                        else:
                            raise BlockerException(f"Invalid website format: {website}")
        except PermissionError:
            logging.error("Permission denied while accessing hosts file")
            raise BlockerException("Permission denied. Please run as administrator.")
        except IOError as e:
            logging.error(f"IO Error while accessing hosts file: {e}")
            raise BlockerException(f"Error accessing hosts file: {e}")

    def remove_websites(self, websites: List[str]) -> None:
        """Remove websites from hosts file"""
        try:
            with self._lock:
                with open(self.hosts_path, "r") as file:
                    lines = file.readlines()
                
                with open(self.hosts_path, "w") as file:
                    for line in lines:
                        if not any(website in line for website in websites):
                            file.write(line)
                logging.info(f"Removed websites from hosts file: {websites}")
        except Exception as e:
            logging.error(f"Error removing websites from hosts file: {e}")
            raise BlockerException(f"Error removing websites: {e}")

class BlockingManager(QObject):
    """Manages the blocking/unblocking of websites"""
    website_blocked = pyqtSignal(str, int)
    website_unblocked = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.hosts_manager = HostsFileManager()
        self.active_blocks: List[Tuple[str, int, threading.Timer]] = []
        self._lock = threading.Lock()

    def block_websites(self, websites: List[str], duration: int) -> None:
        """Block websites for specified duration"""
        try:
            cleaned_websites = [w.strip() for w in websites if self.hosts_manager.validate_website(w.strip())]
            if not cleaned_websites:
                raise BlockerException("No valid websites provided")

            with self._lock:
                self.hosts_manager.add_websites(cleaned_websites)
                
                for website in cleaned_websites:
                    # Cancel existing timer if website is already blocked
                    self.cancel_existing_block(website)
                    
                    # Create new timer
                    timer = threading.Timer(duration, self.unblock_websites, args=([website],))
                    timer.daemon = True
                    timer.start()
                    
                    self.active_blocks.append((website, duration, timer))
                    self.website_blocked.emit(website, duration)
                    logging.info(f"Blocked website: {website} for {duration} seconds")
                    
        except BlockerException as e:
            logging.error(f"Error in block_websites: {e}")
            self.error_occurred.emit(str(e))
        except Exception as e:
            logging.error(f"Unexpected error in block_websites: {e}")
            self.error_occurred.emit(f"Unexpected error: {e}")

    def unblock_websites(self, websites: List[str]) -> None:
        """Unblock specified websites"""
        try:
            with self._lock:
                self.hosts_manager.remove_websites(websites)
                
                # Remove from active blocks and cancel timers
                new_active_blocks = []
                for website, duration, timer in self.active_blocks:
                    if website not in websites:
                        new_active_blocks.append((website, duration, timer))
                    else:
                        timer.cancel()
                        self.website_unblocked.emit(website)
                        logging.info(f"Unblocked website: {website}")
                
                self.active_blocks = new_active_blocks
                
        except Exception as e:
            logging.error(f"Error in unblock_websites: {e}")
            self.error_occurred.emit(f"Error unblocking websites: {e}")

    def cancel_existing_block(self, website: str) -> None:
        """Cancel existing block for a website"""
        for _, _, timer in self.active_blocks:
            if website in timer.args[0]:
                timer.cancel()

class BlockerApp(QWidget):
    """Main application window"""
    def __init__(self):
        super().__init__()
        self.blocking_manager = BlockingManager()
        self.history_manager = set()
        self.setup_ui()
        self.setup_connections()

    def setup_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Website Blocker")
        self.setGeometry(100, 100, 800, 600)
        self.setup_stylesheet()
        
        layout = QVBoxLayout()
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.block_tab = QWidget()
        self.history_tab = QWidget()
        
        self.tab_widget.addTab(self.block_tab, "Block Websites")
        self.tab_widget.addTab(self.history_tab, "History")
        
        self.init_block_tab()
        self.init_history_tab()
        
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def setup_stylesheet(self):
        """Set up the application's stylesheet"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: Arial;
                font-size: 14px;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QLineEdit, QListWidget {
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QLabel {
                font-weight: bold;
            }
            .error {
                color: #ff0000;
            }
        """)

    def init_block_tab(self):
        """Initialize the blocking tab"""
        layout = QVBoxLayout()

        # Input fields
        form_layout = QFormLayout()
        self.websites_input = QLineEdit()
        self.websites_input.setPlaceholderText("example.com, another.com")
        self.duration_input = QLineEdit()
        self.duration_input.setPlaceholderText("Enter duration in minutes")
        
        form_layout.addRow("Websites (comma separated):", self.websites_input)
        form_layout.addRow("Duration (minutes):", self.duration_input)
        
        # Block button
        self.block_button = QPushButton("Block Websites")
        
        # Active blocks list
        self.active_blocks_frame = QFrame()
        self.active_blocks_layout = QVBoxLayout()
        self.active_blocks_frame.setLayout(self.active_blocks_layout)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.block_button)
        layout.addWidget(QLabel("Currently Blocked Websites:"))
        layout.addWidget(self.active_blocks_frame)
        
        self.block_tab.setLayout(layout)

    def init_history_tab(self):
        """Initialize the history tab"""
        layout = QVBoxLayout()
        
        self.history_list = QListWidget()
        self.history_duration_input = QLineEdit()
        self.reblock_button = QPushButton("Re-block Selected")
        
        layout.addWidget(QLabel("Previously Blocked Websites:"))
        layout.addWidget(self.history_list)
        layout.addWidget(QLabel("Duration (minutes):"))
        layout.addWidget(self.history_duration_input)
        layout.addWidget(self.reblock_button)
        
        self.history_tab.setLayout(layout)

    def setup_connections(self):
        """Set up signal/slot connections"""
        self.block_button.clicked.connect(self.handle_block_request)
        self.reblock_button.clicked.connect(self.handle_reblock_request)
        
        # Connect blocking manager signals
        self.blocking_manager.website_blocked.connect(self.handle_website_blocked)
        self.blocking_manager.website_unblocked.connect(self.handle_website_unblocked)
        self.blocking_manager.error_occurred.connect(self.show_error)

    def handle_block_request(self):
        """Handle website blocking request"""
        try:
            websites = [w.strip() for w in self.websites_input.text().split(",")]
            duration_text = self.duration_input.text()
            
            if not websites or not duration_text:
                raise BlockerException("Please enter websites and duration")
                
            if not duration_text.isdigit():
                raise BlockerException("Duration must be a positive number")
                
            duration = int(duration_text) * 60  # Convert to seconds
            self.blocking_manager.block_websites(websites, duration)
            
        except BlockerException as e:
            self.show_error(str(e))
        except Exception as e:
            logging.error(f"Unexpected error in handle_block_request: {e}")
            self.show_error(f"Unexpected error: {e}")

    def handle_reblock_request(self):
        """Handle website reblocking request from history"""
        try:
            selected_item = self.history_list.currentItem()
            if not selected_item:
                raise BlockerException("Please select a website from history")
                
            website = selected_item.text()
            duration_text = self.history_duration_input.text()
            
            if not duration_text.isdigit():
                raise BlockerException("Please enter a valid duration")
                
            duration = int(duration_text) * 60
            self.blocking_manager.block_websites([website], duration)
            
        except BlockerException as e:
            self.show_error(str(e))
        except Exception as e:
            logging.error(f"Unexpected error in handle_reblock_request: {e}")
            self.show_error(f"Unexpected error: {e}")

    def handle_website_blocked(self, website: str, duration: int):
        """Handle website blocked event"""
        self.update_active_blocks_ui()
        self.add_to_history(website)
        self.websites_input.clear()
        self.duration_input.clear()

    def handle_website_unblocked(self, website: str):
        """Handle website unblocked event"""
        self.update_active_blocks_ui()

    def update_active_blocks_ui(self):
        """Update the UI display of active blocks"""
        # Clear existing layouts
        while self.active_blocks_layout.count():
            item = self.active_blocks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add current blocks
        for website, duration, _ in self.blocking_manager.active_blocks:
            block_widget = QFrame()
            block_layout = QHBoxLayout()
            
            label = QLabel(f"{website} - {duration//60}:{duration%60:02d} remaining")
            unblock_button = QPushButton("Unblock")
            unblock_button.clicked.connect(lambda checked, w=website: 
                                        self.blocking_manager.unblock_websites([w]))
            
            block_layout.addWidget(label)
            block_layout.addWidget(unblock_button)
            block_widget.setLayout(block_layout)
            
            self.active_blocks_layout.addWidget(block_widget)

    def add_to_history(self, website: str):
        """Add website to history"""
        if website not in self.history_manager:
            self.history_manager.add(website)
            self.history_list.addItem(website)

    def show_error(self, message: str):
        """Show error message to user"""
        QMessageBox.critical(self, "Error", message)
        logging.error(f"Error displayed to user: {message}")

def is_admin() -> bool:
    """Check if the application is running with admin privileges"""
    try:
        return os.name != 'nt' or ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"Error checking admin status: {e}")
        return False

def run_as_admin():
    """Run the application with admin privileges"""
    if is_admin():
        main()
    else:
        try:
            if os.name == 'nt':  # Windows
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, 
                                                  os.path.abspath(__file__), None, 1)
            else:  # Unix-like
                logging.warning("Application requires root privileges")
                QMessageBox.warning(None, "Warning", 
                                  "Please run this application with sudo")
                sys.exit(1)
        except Exception as e:
            logging.error(f"Error elevating privileges: {e}")
            QMessageBox.critical(None, "Error", 
                               "Failed to obtain administrator privileges")
            sys.exit(1)

def main():
    """Main application entry point"""
    try:
        app = QApplication(sys.argv)
        blocker = BlockerApp()
        blocker.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.critical(f"Critical application error: {e}")
        QMessageBox.critical(None, "Critical Error", 
                           f"Application failed to start: {str(e)}")
        sys.exit(1)

class BlockerTimer(QObject):
    """Timer class for handling block durations"""
    
    timeout = pyqtSignal(str)

    def __init__(self, website: str, duration: int):
        super().__init__()
        self.website = website
        self.duration = duration
        self.remaining = duration
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        
    def start(self):
        """Start the timer"""
        self.timer.start(1000)  # Update every second
        
    def stop(self):
        """Stop the timer"""
        self.timer.stop()
        
    def _tick(self):
        """Handle timer tick"""
        self.remaining -= 1
        if self.remaining <= 0:
            self.stop()
            self.timeout.emit(self.website)
            
    def get_remaining_time(self) -> Tuple[int, int]:
        """Get remaining time in minutes and seconds"""
        minutes = self.remaining // 60
        seconds = self.remaining % 60
        return minutes, seconds

class Configuration:
    """Configuration management class"""
    
    def __init__(self):
        self.config_file = "blocker_config.json"
        self.default_config = {
            "auto_start": False,
            "show_notifications": True,
            "default_duration": 30,
            "backup_hosts": True
        }
        self.current_config = self.load_config()

    def load_config(self) -> dict:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            return self.default_config.copy()
        except Exception as e:
            logging.error(f"Error loading configuration: {e}")
            return self.default_config.copy()

    def save_config(self) -> None:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.current_config, f, indent=4)
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            raise BlockerException(f"Could not save configuration: {e}")

class HostsBackup:
    """Handles backup and restoration of hosts file"""
    
    def __init__(self):
        self.backup_dir = "hosts_backups"
        self.ensure_backup_dir()
        
    def ensure_backup_dir(self) -> None:
        """Ensure backup directory exists"""
        try:
            if not os.path.exists(self.backup_dir):
                os.makedirs(self.backup_dir)
        except Exception as e:
            logging.error(f"Error creating backup directory: {e}")
            raise BlockerException(f"Could not create backup directory: {e}")
            
    def create_backup(self) -> None:
        """Create a backup of the hosts file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"hosts_backup_{timestamp}")
            
            with open(HostsFileManager().hosts_path, 'r') as source:
                with open(backup_path, 'w') as target:
                    target.write(source.read())
                    
            logging.info(f"Created hosts file backup: {backup_path}")
        except Exception as e:
            logging.error(f"Error creating hosts backup: {e}")
            raise BlockerException(f"Could not create hosts backup: {e}")
            
    def restore_backup(self, backup_file: str) -> None:
        """Restore hosts file from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_file)
            
            if not os.path.exists(backup_path):
                raise BlockerException("Backup file does not exist")
                
            with open(backup_path, 'r') as source:
                with open(HostsFileManager().hosts_path, 'w') as target:
                    target.write(source.read())
                    
            logging.info(f"Restored hosts file from backup: {backup_path}")
        except Exception as e:
            logging.error(f"Error restoring hosts backup: {e}")
            raise BlockerException(f"Could not restore hosts backup: {e}")

class SettingsDialog(QDialog):
    """Settings dialog for the application"""
    
    def __init__(self, config: Configuration, parent=None):
        super().__init__(parent)
        self.config = config
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the settings dialog UI"""
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()
        
        # Create settings options
        self.auto_start = QCheckBox("Start with system")
        self.auto_start.setChecked(self.config.current_config["auto_start"])
        
        self.show_notifications = QCheckBox("Show notifications")
        self.show_notifications.setChecked(self.config.current_config["show_notifications"])
        
        self.default_duration = QSpinBox()
        self.default_duration.setRange(1, 1440)  # 1 minute to 24 hours
        self.default_duration.setValue(self.config.current_config["default_duration"])
        
        self.backup_hosts = QCheckBox("Backup hosts file before modifications")
        self.backup_hosts.setChecked(self.config.current_config["backup_hosts"])
        
        # Add widgets to layout
        layout.addWidget(self.auto_start)
        layout.addWidget(self.show_notifications)
        layout.addWidget(QLabel("Default duration (minutes):"))
        layout.addWidget(self.default_duration)
        layout.addWidget(self.backup_hosts)
        
        # Add buttons
        buttons = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        save_button.clicked.connect(self.save_settings)
        cancel_button.clicked.connect(self.reject)
        
        buttons.addWidget(save_button)
        buttons.addWidget(cancel_button)
        
        layout.addLayout(buttons)
        self.setLayout(layout)
        
    def save_settings(self):
        """Save the settings"""
        try:
            self.config.current_config.update({
                "auto_start": self.auto_start.isChecked(),
                "show_notifications": self.show_notifications.isChecked(),
                "default_duration": self.default_duration.value(),
                "backup_hosts": self.backup_hosts.isChecked()
            })
            self.config.save_config()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save settings: {str(e)}")

if __name__ == "__main__":
    try:
        run_as_admin()
    except Exception as e:
        logging.critical(f"Failed to start application: {e}")
        QMessageBox.critical(None, "Critical Error", 
                           f"Application failed to start: {str(e)}")
        sys.exit(1)