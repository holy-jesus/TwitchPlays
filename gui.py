import sys
import os
import json
import threading
import psutil
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QGroupBox,
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt6.QtCore import pyqtSignal, QObject, Qt
from PyQt6.QtGui import QFont

# Add backend dir to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import Bot, Keys

CONFIG_FILE = "config.json"


class BotWorker(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, channel, process_name, command_mappings):
        super().__init__()
        self.channel = channel
        self.process_name = process_name
        self.command_mappings = command_mappings
        self.bot = None

    def run(self):
        try:
            self.bot = Bot(self.channel, self.process_name)

            # Register loaded commands
            for mapping in self.command_mappings:
                cmd = mapping["command"].split(",")
                cmd = [c.strip() for c in cmd]
                key = mapping["key"]
                duration = mapping["duration"]
                cooldown = mapping.get("cooldown", 0)

                # Use basic press_key. Advanced users might want mouse movement etc.,
                # but we'll map basic keys for now.
                self.bot.press_key(cmd, key, duration=duration, cooldown=cooldown)

            self.bot.run()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def stop(self):
        if self.bot and self.bot.loop:
            self.bot.loop.call_soon_threadsafe(self.bot.loop.stop)


class TwitchPlaysGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TwitchPlays Controller")
        self.setMinimumSize(800, 600)
        self.bot_thread = None
        self.bot_worker = None

        # Setup UI
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self._setup_settings_panel()
        self._setup_mappings_panel()
        self._setup_control_panel()

        self.load_settings()

    def _setup_settings_panel(self):
        group_box = QGroupBox("Bot Settings")
        layout = QVBoxLayout()

        # Channel Input
        channel_layout = QHBoxLayout()
        channel_label = QLabel("Twitch Channel:")
        self.channel_input = QLineEdit()
        self.channel_input.setPlaceholderText("Enter channel name...")
        channel_layout.addWidget(channel_label)
        channel_layout.addWidget(self.channel_input)

        # Process Selection
        process_layout = QHBoxLayout()
        process_label = QLabel("Target Process:")
        self.process_combo = QComboBox()
        self.process_combo.setEditable(True)
        self.refresh_processes_btn = QPushButton("Refresh")
        self.refresh_processes_btn.clicked.connect(self.populate_processes)

        process_layout.addWidget(process_label)
        process_layout.addWidget(self.process_combo)
        process_layout.addWidget(self.refresh_processes_btn)

        layout.addLayout(channel_layout)
        layout.addLayout(process_layout)
        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)
        self.populate_processes()

    def _setup_mappings_panel(self):
        group_box = QGroupBox("Command Mappings")
        layout = QVBoxLayout()

        # Controls to add new mapping
        add_layout = QHBoxLayout()
        self.new_cmd_input = QLineEdit()
        self.new_cmd_input.setPlaceholderText("Chat cmd (e.g. q, й)")

        self.new_key_input = QComboBox()
        self.new_key_input.addItems(
            [
                "a",
                "b",
                "c",
                "d",
                "e",
                "f",
                "g",
                "h",
                "i",
                "j",
                "k",
                "l",
                "m",
                "n",
                "o",
                "p",
                "q",
                "r",
                "s",
                "t",
                "u",
                "v",
                "w",
                "x",
                "y",
                "z",
                "0",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "space",
                "enter",
                "shift",
                "ctrl",
                "alt",
                "tab",
                "esc",
                "backspace",
                Keys.LMB,
                Keys.RMB,
            ]
        )

        self.new_duration_input = QDoubleSpinBox()
        self.new_duration_input.setToolTip("Duration (seconds). 0 for tap.")
        self.new_duration_input.setSuffix(" s")
        self.new_duration_input.setMaximum(100.0)
        self.new_duration_input.setSingleStep(0.1)

        self.new_cooldown_input = QSpinBox()
        self.new_cooldown_input.setToolTip("Cooldown (seconds)")
        self.new_cooldown_input.setSuffix(" s")
        self.new_cooldown_input.setMaximum(9999)

        add_btn = QPushButton("Add Mapping")
        add_btn.clicked.connect(self.add_mapping)

        add_layout.addWidget(QLabel("Cmds:"))
        add_layout.addWidget(self.new_cmd_input)
        add_layout.addWidget(QLabel("Key:"))
        add_layout.addWidget(self.new_key_input)
        add_layout.addWidget(QLabel("Dur:"))
        add_layout.addWidget(self.new_duration_input)
        add_layout.addWidget(QLabel("CD:"))
        add_layout.addWidget(self.new_cooldown_input)
        add_layout.addWidget(add_btn)

        # Table
        self.mapping_table = QTableWidget(0, 5)
        self.mapping_table.setHorizontalHeaderLabels(
            ["Chat Commands", "Key", "Duration (s)", "Cooldown (s)", "Action"]
        )
        header = self.mapping_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addLayout(add_layout)
        layout.addWidget(self.mapping_table)
        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def _setup_control_panel(self):
        layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Bot")
        self.start_btn.setMinimumHeight(40)
        font = self.start_btn.font()
        font.setBold(True)
        self.start_btn.setFont(font)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.start_btn.clicked.connect(self.start_bot)

        self.stop_btn = QPushButton("Stop Bot")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setFont(font)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_bot)

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setMinimumHeight(40)
        self.save_btn.clicked.connect(self.save_settings)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.save_btn)

        self.main_layout.addLayout(layout)

    def populate_processes(self):
        current_text = self.process_combo.currentText()
        self.process_combo.clear()

        processes = set()
        for p in psutil.process_iter(["name"]):
            name = p.info["name"]
            if name and name.endswith(".exe"):
                processes.add(name)

        self.process_combo.addItems(sorted(list(processes)))

        if current_text:
            self.process_combo.setCurrentText(current_text)

    def add_mapping(self):
        cmds = self.new_cmd_input.text().strip()
        if not cmds:
            QMessageBox.warning(
                self, "Validation Error", "Please enter at least one chat command."
            )
            return

        key = self.new_key_input.currentText()
        duration = self.new_duration_input.value()
        cooldown = self.new_cooldown_input.value()

        self._add_mapping_row(cmds, key, duration, cooldown)
        self.new_cmd_input.clear()

    def _add_mapping_row(self, cmds, key, duration, cooldown):
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)

        self.mapping_table.setItem(row, 0, QTableWidgetItem(cmds))
        self.mapping_table.setItem(row, 1, QTableWidgetItem(key))
        self.mapping_table.setItem(row, 2, QTableWidgetItem(str(duration)))
        self.mapping_table.setItem(row, 3, QTableWidgetItem(str(cooldown)))

        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda _, r=row: self._remove_mapping(r))
        self.mapping_table.setCellWidget(row, 4, remove_btn)

    def _remove_mapping(self, row):
        self.mapping_table.removeRow(row)
        # Re-bind remove buttons to fix row indices
        for i in range(self.mapping_table.rowCount()):
            btn = self.mapping_table.cellWidget(i, 4)
            if btn:
                # Disconnect all previous connections
                try:
                    btn.clicked.disconnect()
                except TypeError:
                    pass
                btn.clicked.connect(lambda _, r=i: self._remove_mapping(r))

    def get_all_mappings(self):
        mappings = []
        for i in range(self.mapping_table.rowCount()):
            mappings.append(
                {
                    "command": self.mapping_table.item(i, 0).text(),
                    "key": self.mapping_table.item(i, 1).text(),
                    "duration": float(self.mapping_table.item(i, 2).text()),
                    "cooldown": int(self.mapping_table.item(i, 3).text()),
                }
            )
        return mappings

    def save_settings(self):
        data = {
            "channel": self.channel_input.text(),
            "process": self.process_combo.currentText(),
            "mappings": self.get_all_mappings(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Success", "Settings saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def load_settings(self):
        if not os.path.exists(CONFIG_FILE):
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

            if "channel" in data:
                self.channel_input.setText(data["channel"])
            if "process" in data:
                self.process_combo.setCurrentText(data["process"])

            if "mappings" in data:
                for item in data["mappings"]:
                    self._add_mapping_row(
                        item["command"],
                        item["key"],
                        item.get("duration", 0.0),
                        item.get("cooldown", 0),
                    )
        except Exception as e:
            print(f"Failed to load settings: {e}")

    def start_bot(self):
        channel = self.channel_input.text().strip()
        process = self.process_combo.currentText().strip()

        if not channel:
            QMessageBox.warning(self, "Error", "Please enter a Twitch channel name.")
            return

        if not process:
            QMessageBox.warning(self, "Error", "Please select a target process.")
            return

        mappings = self.get_all_mappings()
        if not mappings:
            reply = QMessageBox.question(
                self,
                "Warning",
                "No commands mapped! Start anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_settings()

        self.bot_thread = threading.Thread(
            target=self._run_bot_thread, args=(channel, process, mappings)
        )
        self.bot_thread.daemon = True
        self.bot_thread.start()

    def _run_bot_thread(self, channel, process, mappings):
        self.bot_worker = BotWorker(channel, process, mappings)
        self.bot_worker.error.connect(self.on_bot_error)
        self.bot_worker.finished.connect(self.on_bot_finished)
        self.bot_worker.run()

    def stop_bot(self):
        if self.bot_worker:
            self.bot_worker.stop()
        self.stop_btn.setEnabled(False)

    def on_bot_error(self, err_msg):
        QMessageBox.critical(self, "Bot Error", f"An error occurred:\n{err_msg}")

    def on_bot_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.bot_thread = None
        self.bot_worker = None


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Modern styling
    app.setStyle("Fusion")

    window = TwitchPlaysGUI()
    window.show()
    sys.exit(app.exec())
