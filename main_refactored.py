"""
Refactored ECG to Binary Converter - Modular Version
"""
import sys
import os
import numpy as np
import wfdb
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                            QPushButton, QHBoxLayout, QLabel, QComboBox, 
                            QCheckBox, QSlider, QSpinBox, QGridLayout, QGroupBox,
                            QMessageBox, QDoubleSpinBox)
from PyQt5.QtCore import QTimer, Qt
from datetime import datetime

# Import modular components
from models.ecg_data import ECGData, ECGMode, ConversionHistoryItem
from utils.esp32_converter import ESP32Converter
from utils.csv_exporter import CSVExporter
from ui.sidebar_panel import SidebarInfoPanel
from ui.plot_manager import PlotManager


class ECGToBinaryConverter(QMainWindow):
    """Main application class - now much cleaner with modular components"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize modular components
        self.ecg_data = ECGData()
        self.esp32_converter = ESP32Converter()
        self.csv_exporter = CSVExporter()
        self.plot_manager = PlotManager()
        
        # Application state
        self.ecg_mode = ECGMode.TWELVE_LEAD
        self.current_index = 0
        self.playing = False
        self.play_speed = 1.0
        self.window_size = 2000
        
        # Folder paths
        self.sample_folder = "sample"
        self.output_folder = "hasil"
        self.csv_output_folder = "hasilcsv"
        
        # Create output folders if not exist
        for folder in [self.output_folder, self.csv_output_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.update_plot)
        
        # Status bar
        self.statusBar().showMessage("Ready. Please select a record from the sample folder.")
        
        # Load available records
        self.load_available_records()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Window setup
        self.setWindowTitle("ECG PhysioNet to Binary Converter - 12/10 Lead Mode")
        self.setGeometry(100, 50, 1400, 900)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create UI components
        self.create_control_panel()
        self.create_channel_controls()
        self.create_plot_area()
    
    def create_control_panel(self):
        """Create the control panel"""
        self.control_group = QGroupBox("Controls")
        self.main_layout.addWidget(self.control_group)
        self.control_layout = QGridLayout(self.control_group)
        
        # Row 0: Record selection, Mode selection, Y-axis mode, convert buttons
        self.record_label = QLabel("Select Record:")
        self.control_layout.addWidget(self.record_label, 0, 0)
        
        self.record_combo = QComboBox()
        self.control_layout.addWidget(self.record_combo, 0, 1)
        
        # ECG Mode selector
        self.mode_label = QLabel("ECG Mode:")
        self.control_layout.addWidget(self.mode_label, 0, 2)
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["12-Lead Mode", "10-Lead Mode"])
        self.control_layout.addWidget(self.mode_combo, 0, 3)
        
        # Y-axis mode selector
        self.y_mode_label = QLabel("Y-Axis:")
        self.control_layout.addWidget(self.y_mode_label, 0, 4)
        
        self.y_mode_combo = QComboBox()
        self.y_mode_combo.addItems(self.csv_exporter.y_axis_modes)
        self.control_layout.addWidget(self.y_mode_combo, 0, 5)
        
        # Convert buttons
        self.convert_button = QPushButton("Convert to Binary")
        self.convert_button.setEnabled(False)
        self.control_layout.addWidget(self.convert_button, 0, 6)
        
        self.export_csv_button = QPushButton("Export to CSV")
        self.export_csv_button.setEnabled(False)
        self.export_csv_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        self.control_layout.addWidget(self.export_csv_button, 0, 7)
        
        # Info panel toggle
        self.info_toggle_btn = QPushButton("Info Panel")
        self.control_layout.addWidget(self.info_toggle_btn, 0, 8)
        
        # Guide lines toggle
        self.guide_toggle_btn = QPushButton("Guide: ON")
        self.guide_toggle_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.control_layout.addWidget(self.guide_toggle_btn, 0, 9)
        
        # Row 1: Play controls and speed
        self.play_button = QPushButton("Play")
        self.control_layout.addWidget(self.play_button, 1, 0)
        
        self.reset_button = QPushButton("Reset")
        self.control_layout.addWidget(self.reset_button, 1, 1)
        
        self.speed_label = QLabel("Speed:")
        self.control_layout.addWidget(self.speed_label, 1, 2)
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(50)
        self.speed_slider.setValue(10)
        self.control_layout.addWidget(self.speed_slider, 1, 3, 1, 2)
        
        self.speed_value = QLabel("1.0x")
        self.control_layout.addWidget(self.speed_value, 1, 5)
        
        # Conversion status label
        self.conversion_status_label = QLabel("")
        self.conversion_status_label.setStyleSheet("color: blue; font-weight: bold;")
        self.control_layout.addWidget(self.conversion_status_label, 1, 6, 1, 4)
        
        # Row 2: Window size, gain control, and ESP32 info
        self.window_label = QLabel("Window Size:")
        self.control_layout.addWidget(self.window_label, 2, 0)
        
        self.window_spinbox = QSpinBox()
        self.window_spinbox.setMinimum(100)
        self.window_spinbox.setMaximum(10000)
        self.window_spinbox.setSingleStep(100)
        self.window_spinbox.setValue(2000)
        self.control_layout.addWidget(self.window_spinbox, 2, 1)
        
        # Gain control
        self.gain_label = QLabel("Gain:")
        self.control_layout.addWidget(self.gain_label, 2, 2)
        
        self.gain_spinbox = QSpinBox()
        self.gain_spinbox.setMinimum(1)
        self.gain_spinbox.setMaximum(10000)
        self.gain_spinbox.setSingleStep(10)
        self.gain_spinbox.setValue(1000)
        self.control_layout.addWidget(self.gain_spinbox, 2, 3)
        
        self.sample_rate_label = QLabel("Sample Rate: -")
        self.control_layout.addWidget(self.sample_rate_label, 2, 4)
        
        self.duration_label = QLabel("Duration: -")
        self.control_layout.addWidget(self.duration_label, 2, 5)
        
        # Row 3: ESP32 info and gain warning
        self.esp32_info_label = QLabel(f"ESP32: Gain={self.esp32_converter.gain}x, ADC=12bit, VCC=3.3V")
        self.esp32_info_label.setStyleSheet("color: blue; font-weight: bold;")
        self.control_layout.addWidget(self.esp32_info_label, 3, 0, 1, 4)
        
        # Gain warning label
        self.gain_warning_label = QLabel("")
        self.gain_warning_label.setStyleSheet("color: #FF8C00; font-weight: bold;")
        self.gain_warning_label.setVisible(False)
        self.control_layout.addWidget(self.gain_warning_label, 3, 4, 1, 6)
        
        # Row 4: Trim controls
        self.trim_label = QLabel("Trim Signal:")
        self.control_layout.addWidget(self.trim_label, 4, 0)
        
        self.start_label = QLabel("Start (s):")
        self.control_layout.addWidget(self.start_label, 4, 1)
        
        self.start_spinbox = QDoubleSpinBox()
        self.start_spinbox.setMinimum(0.0)
        self.start_spinbox.setMaximum(9999.0)
        self.start_spinbox.setDecimals(2)
        self.start_spinbox.setSingleStep(0.1)
        self.control_layout.addWidget(self.start_spinbox, 4, 2)
        
        self.end_label = QLabel("End (s):")
        self.control_layout.addWidget(self.end_label, 4, 3)
        
        self.end_spinbox = QDoubleSpinBox()
        self.end_spinbox.setMinimum(0.0)
        self.end_spinbox.setMaximum(9999.0)
        self.end_spinbox.setDecimals(2)
        self.end_spinbox.setSingleStep(0.1)
        self.control_layout.addWidget(self.end_spinbox, 4, 4)
        
        self.trim_info_label = QLabel("Trimmed: - samples")
        self.control_layout.addWidget(self.trim_info_label, 4, 5)
    
    def create_channel_controls(self):
        """Create channel visibility controls"""
        self.channel_group = QGroupBox("Channel Visibility")
        self.main_layout.addWidget(self.channel_group)
        self.channel_layout = QGridLayout(self.channel_group)
        
        # Add Select All / Deselect All buttons
        self.select_all_btn = QPushButton("Select All")
        self.channel_layout.addWidget(self.select_all_btn, 0, 0, 1, 3)
        
        self.deselect_all_btn = QPushButton("Deselect All")
        self.channel_layout.addWidget(self.deselect_all_btn, 0, 3, 1, 3)
        
        self.channel_checkboxes = []
        for i in range(self.plot_manager.max_channels):
            label = self.ecg_data.CHANNELS_12LEAD[i] if i < len(self.ecg_data.CHANNELS_12LEAD) else f"Ch{i+1}"
            checkbox = QCheckBox(label)
            checkbox.setChecked(True)
            
            row = (i // 6) + 1
            col = i % 6
            self.channel_layout.addWidget(checkbox, row, col)
            self.channel_checkboxes.append(checkbox)
    
    def create_plot_area(self):
        """Create plot area with sidebar"""
        # Container for plot area with relative positioning
        self.plot_container = QWidget()
        self.plot_container_layout = QHBoxLayout(self.plot_container)
        self.plot_container_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_container_layout.setSpacing(0)
        self.main_layout.addWidget(self.plot_container)
        
        # Create sidebar (initially hidden)
        self.info_sidebar = SidebarInfoPanel(self.plot_container)
        
        # Create plot area using plot manager
        self.plot_manager.create_plot_area(self.plot_container_layout)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Record selection
        self.record_combo.currentTextChanged.connect(self.load_record)
        
        # Mode selection
        self.mode_combo.currentIndexChanged.connect(self.change_ecg_mode)
        
        # Y-axis mode
        self.y_mode_combo.currentIndexChanged.connect(self.change_y_mode)
        
        # Convert buttons
        self.convert_button.clicked.connect(self.convert_to_binary)
        self.export_csv_button.clicked.connect(self.export_to_csv)
        
        # Info panel toggle
        self.info_toggle_btn.clicked.connect(self.toggle_info_panel)
        
        # Guide lines toggle
        self.guide_toggle_btn.clicked.connect(self.toggle_guide_lines)
        
        # Play controls
        self.play_button.clicked.connect(self.toggle_play)
        self.reset_button.clicked.connect(self.reset_playback)
        self.speed_slider.valueChanged.connect(self.change_speed)
        
        # Window size
        self.window_spinbox.valueChanged.connect(self.change_window_size)
        
        # Gain control
        self.gain_spinbox.valueChanged.connect(self.change_gain)
        
        # Trim controls
        self.start_spinbox.valueChanged.connect(self.update_trim)
        self.end_spinbox.valueChanged.connect(self.update_trim)
        
        # Channel controls
        self.select_all_btn.clicked.connect(self.select_all_channels)
        self.deselect_all_btn.clicked.connect(self.deselect_all_channels)
        
        # Channel checkboxes
        for i, checkbox in enumerate(self.channel_checkboxes):
            checkbox.stateChanged.connect(lambda state, idx=i: self.toggle_channel(idx, state))
    
    def load_available_records(self):
        """Load available records from sample folder"""
        try:
            if not os.path.exists(self.sample_folder):
                os.makedirs(self.sample_folder)
                self.statusBar().showMessage("Sample folder created. Please add PhysioNet files.")
                return
            
            records = []
            for file in os.listdir(self.sample_folder):
                if file.endswith('.hea'):
                    record_name = file[:-4]
                    records.append(record_name)
            
            if records:
                self.record_combo.addItems(sorted(records))
            else:
                self.statusBar().showMessage("No records found in sample folder.")
        except Exception as e:
            self.statusBar().showMessage(f"Error loading records: {str(e)}")
    
    def load_record(self, record_name):
        """Load selected record"""
        if not record_name:
            return
            
        try:
            self.statusBar().showMessage(f"Loading record {record_name}...")
            
            # Load record
            record_path = os.path.join(self.sample_folder, record_name)
            self.ecg_data.record = wfdb.rdrecord(record_path)
            self.ecg_data.signal = self.ecg_data.record.p_signal
            self.ecg_data.sample_rate = self.ecg_data.record.fs
            
            # Create time array
            self.ecg_data.time = np.arange(len(self.ecg_data.signal)) / self.ecg_data.sample_rate
            
            # Reset trim parameters
            self.ecg_data.trim_start = 0.0
            self.ecg_data.trim_end = len(self.ecg_data.signal) / self.ecg_data.sample_rate
            
            # Update trim spinboxes
            self.start_spinbox.setMaximum(self.ecg_data.trim_end)
            self.end_spinbox.setMaximum(self.ecg_data.trim_end)
            self.end_spinbox.setValue(self.ecg_data.trim_end)
            
            # Apply initial trim
            self.update_trim()
            
            # If in 10-lead mode, convert immediately
            if self.ecg_mode == ECGMode.TEN_LEAD:
                self.ecg_data.convert_to_10lead()
            
            # Update UI
            self.current_index = 0
            self.update_record_info()
            self.update_plots()
            self.convert_button.setEnabled(True)
            self.export_csv_button.setEnabled(True)
            
            # Update info panel
            self.update_info_panel()
            
            self.statusBar().showMessage(f"Record {record_name} loaded successfully.")
            
        except Exception as e:
            self.statusBar().showMessage(f"Error loading record: {str(e)}")
            self.convert_button.setEnabled(False)
            self.export_csv_button.setEnabled(False)
    
    def update_trim(self):
        """Update signal trimming"""
        start_time = self.start_spinbox.value()
        end_time = self.end_spinbox.value()
        
        trimmed_samples = self.ecg_data.update_trim(start_time, end_time)
        
        # Update info
        self.trim_info_label.setText(f"Trimmed: {trimmed_samples:,} samples")
        
        # If in 10-lead mode, reconvert
        if self.ecg_mode == ECGMode.TEN_LEAD:
            self.ecg_data.convert_to_10lead()
        
        # Reset playback and update plots
        self.current_index = 0
        self.check_gain_warnings()
        self.update_plots()
    
    def update_record_info(self):
        """Update record information display"""
        if self.ecg_data.record is None:
            return
        
        # Update sample rate
        self.sample_rate_label.setText(f"Sample Rate: {self.ecg_data.sample_rate} Hz")
        
        # Update duration
        total_duration = self.ecg_data.get_total_duration()
        minutes = int(total_duration // 60)
        seconds = int(total_duration % 60)
        self.duration_label.setText(f"Duration: {minutes}:{seconds:02d}")
    
    def change_ecg_mode(self, index):
        """Change between 12-lead and 10-lead mode"""
        if index == 0:
            self.ecg_mode = ECGMode.TWELVE_LEAD
            self.conversion_status_label.setText("Mode: 12-Lead Standard")
            self.conversion_status_label.setStyleSheet("color: blue; font-weight: bold;")
        else:
            self.ecg_mode = ECGMode.TEN_LEAD
            self.conversion_status_label.setText("Mode: 10-Lead Raw Electrodes")
            self.conversion_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # Convert data if available
            if self.ecg_data.signal_trimmed is not None:
                self.ecg_data.convert_to_10lead()
        
        # Update channel display
        self.plot_manager.update_channel_display(
            self.ecg_mode.value, 
            self.ecg_data.CHANNELS_12LEAD, 
            self.ecg_data.CHANNELS_10LEAD
        )
        self.update_plot_layout()
        self.update_plots()
        
        # Update info panel
        self.update_info_panel()
    
    def change_y_mode(self, index):
        """Change Y-axis display mode"""
        self.plot_manager.change_y_mode(index)
        self.update_plots()
    
    def change_gain(self, value):
        """Change gain value and update display"""
        self.esp32_converter.set_gain(value)
        
        # Update ESP32 info label
        self.esp32_info_label.setText(f"ESP32: Gain={value}x, ADC=12bit, VCC=3.3V")
        
        # Check for gain warnings with actual data
        self.check_gain_warnings()
        
        # Update plots with new gain
        self.update_plots()
    
    def change_window_size(self, value):
        """Change display window size"""
        self.window_size = value
        self.update_plots()
    
    def change_speed(self, value):
        """Change playback speed"""
        self.play_speed = value / 10.0
        self.speed_value.setText(f"{self.play_speed:.1f}x")
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.playing:
            self.timer.stop()
            self.playing = False
            self.play_button.setText("Play")
        else:
            self.timer.start()
            self.playing = True
            self.play_button.setText("Pause")
    
    def reset_playback(self):
        """Reset to beginning"""
        self.current_index = 0
        self.update_plots()
    
    def update_plot(self):
        """Timer update for animation"""
        if self.ecg_data.signal_trimmed is None:
            return
        
        # Increment based on speed
        increment = int(self.window_size * 0.1 * self.play_speed)
        self.current_index += increment
        
        # Loop back to start
        if self.current_index >= len(self.ecg_data.signal_trimmed) - self.window_size:
            self.current_index = 0
        
        self.update_plots()
    
    def toggle_info_panel(self):
        """Toggle info sidebar"""
        self.info_sidebar.toggle()
    
    def toggle_guide_lines(self):
        """Toggle guide lines visibility"""
        is_on = self.plot_manager.toggle_guide_lines()
        
        # Update button appearance
        if is_on:
            self.guide_toggle_btn.setText("Guide: ON")
            self.guide_toggle_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        else:
            self.guide_toggle_btn.setText("Guide: OFF")
            self.guide_toggle_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
    
    def select_all_channels(self):
        """Select all channel checkboxes"""
        for checkbox in self.channel_checkboxes:
            if checkbox.isVisible():
                checkbox.setChecked(True)
    
    def deselect_all_channels(self):
        """Deselect all channel checkboxes"""
        for checkbox in self.channel_checkboxes:
            if checkbox.isVisible():
                checkbox.setChecked(False)
    
    def toggle_channel(self, channel, state):
        """Toggle channel visibility"""
        self.plot_manager.set_channel_visibility(channel, state)
        self.update_plot_layout()
        self.update_plots()
    
    def update_plot_layout(self):
        """Update plot layout based on visible channels"""
        self.plot_manager.update_plot_layout(self.ecg_mode.value)
    
    def update_plots(self):
        """Update all plots with current window"""
        if self.ecg_data.signal_trimmed is None:
            return
        
        # Get appropriate data based on mode
        if self.ecg_mode == ECGMode.TWELVE_LEAD:
            # 12-lead mode: use mapped signal
            display_signal = self.ecg_data.map_channels_to_standard()
        else:  # TEN_LEAD
            # 10-lead mode: use electrode data if available
            if self.ecg_data.electrode_data is not None:
                display_signal = self.ecg_data.electrode_data
            else:
                # Fallback to empty data
                display_signal = np.zeros((len(self.ecg_data.signal_trimmed), 10))
        
        self.plot_manager.update_plots(
            display_signal, 
            self.ecg_data.time_trimmed, 
            self.current_index, 
            self.window_size,
            self.ecg_mode.value,
            self.esp32_converter
        )
    
    def check_gain_warnings(self):
        """Check if current gain will cause signal clipping"""
        if self.ecg_data.signal_trimmed is None:
            self.gain_warning_label.setVisible(False)
            self.convert_button.setEnabled(False)
            self.export_csv_button.setEnabled(False)
            return
        
        # Get appropriate data based on mode
        if self.ecg_mode == ECGMode.TEN_LEAD and self.ecg_data.electrode_data is not None:
            signal_to_check = self.ecg_data.electrode_data
        else:
            signal_to_check = self.ecg_data.map_channels_to_standard()
        
        has_warning, warning_text = self.esp32_converter.check_gain_warnings(signal_to_check)
        
        if has_warning:
            warning_text += f" [Mode: {self.ecg_mode.value}]"
            self.gain_warning_label.setText(warning_text)
            self.gain_warning_label.setVisible(True)
            
            # Disable conversion when signal is out of range
            self.convert_button.setEnabled(False)
            self.convert_button.setText("Convert Disabled (Out of Range)")
            # CSV export can still work even if binary conversion is disabled
            self.export_csv_button.setEnabled(True)
        else:
            self.gain_warning_label.setVisible(False)
            
            # Enable conversion when signal is in acceptable range
            self.convert_button.setEnabled(True)
            self.convert_button.setText("Convert to Binary")
            self.export_csv_button.setEnabled(True)
    
    def get_active_channels_data(self):
        """Get data for only active (checked) channels based on current mode"""
        if self.ecg_data.signal_trimmed is None:
            return None, None, None
        
        # Get appropriate data and channel names based on mode
        if self.ecg_mode == ECGMode.TWELVE_LEAD:
            # 12-lead mode: use mapped signal
            all_data = self.ecg_data.map_channels_to_standard()
            all_channel_names = self.ecg_data.CHANNELS_12LEAD
            max_channels = 12
        else:  # TEN_LEAD
            # 10-lead mode: use electrode data if available
            if self.ecg_data.electrode_data is not None:
                all_data = self.ecg_data.electrode_data
                all_channel_names = self.ecg_data.CHANNELS_10LEAD
                max_channels = 10
            else:
                return None, None, None
        
        # Filter only active channels
        active_channels = []
        active_data_list = []
        active_names = []
        
        for i in range(max_channels):
            if self.plot_manager.show_channel[i]:  # Only include checked channels
                channel_data_mv = all_data[:, i]
                
                # Convert to display format based on Y-axis mode
                channel_data_display = self.esp32_converter.get_display_data(
                    channel_data_mv, self.plot_manager.current_y_mode
                )
                
                active_data_list.append(channel_data_display)
                active_names.append(all_channel_names[i])
                active_channels.append(i)
        
        if not active_data_list:
            return None, None, None
            
        # Convert to numpy array
        active_data = np.column_stack(active_data_list)
        
        # Create time array (relative from 0)
        relative_time = np.arange(len(active_data)) / self.ecg_data.sample_rate
        
        return active_data, active_names, relative_time
    
    def convert_to_binary(self):
        """Convert ECG data to binary format with ESP32 compatibility"""
        if self.ecg_data.signal_trimmed is None:
            return
        
        try:
            # Prepare data based on mode
            if self.ecg_mode == ECGMode.TWELVE_LEAD:
                # 12-lead mode: use mapped signal directly
                signal_data = self.ecg_data.map_channels_to_standard()
                mode = "12lead"
            else:  # ECGMode.TEN_LEAD
                # 10-lead mode: arrange as RA,LA,LL,RL,0,0,V1-V6
                if self.ecg_data.electrode_data is None:
                    QMessageBox.warning(self, "Error", "No 10-lead data available. Please reload the record.")
                    return
                
                # Create 12-channel array for 10-lead mode
                signal_data = np.zeros((len(self.ecg_data.electrode_data), 12))
                
                # Copy electrode data to first 4 channels
                signal_data[:, :4] = self.ecg_data.electrode_data[:, :4]
                
                # Channels 4 and 5 are padding (zeros)
                signal_data[:, 4:6] = 0
                
                # Copy chest electrodes (V1-V6) to channels 6-12
                signal_data[:, 6:12] = self.ecg_data.electrode_data[:, 4:10]
                
                mode = "10lead"
            
            # Create output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{self.record_combo.currentText()}_{mode}_{timestamp}.bin"
            output_path = os.path.join(self.output_folder, output_filename)
            
            # Convert using ESP32 converter
            result = self.esp32_converter.convert_to_binary(signal_data, output_path, mode)
            
            if result['success']:
                # Prepare conversion info
                conversion_info = f"--- ESP32 Conversion Results ---\n"
                conversion_info += f"Output file: {output_filename}\n"
                conversion_info += f"Mode: {self.ecg_mode.value}\n"
                conversion_info += f"Source record: {self.record_combo.currentText()}\n"
                conversion_info += f"Trimmed duration: {self.ecg_data.trim_start:.2f}s - {self.ecg_data.trim_end:.2f}s\n"
                conversion_info += f"Total duration: {self.ecg_data.trim_end - self.ecg_data.trim_start:.2f}s\n"
                conversion_info += f"Samples converted: {result['samples']:,}\n"
                conversion_info += f"File size: {result['file_size']:,} bytes\n"
                conversion_info += f"Expected size: {result['expected_size']:,} bytes\n"
                
                if self.ecg_mode == ECGMode.TEN_LEAD:
                    conversion_info += f"\n10-Lead Channel Mapping:\n"
                    conversion_info += f"Ch 1-4: RA, LA, LL, RL (electrodes)\n"
                    conversion_info += f"Ch 5-6: Padding (zeros)\n"
                    conversion_info += f"Ch 7-12: V1-V6\n"
                
                conversion_info += f"\nESP32 ADC Mapping:\n"
                conversion_info += f"- Gain applied: {self.esp32_converter.gain}x\n"
                conversion_info += f"- ADC range: {result['min_adc']} - {result['max_adc']} (0-{self.esp32_converter.adc_resolution})\n"
                conversion_info += f"- Voltage range: {result['min_voltage']:.3f}V - {result['max_voltage']:.3f}V (0-{self.esp32_converter.vcc}V)\n"
                conversion_info += f"- Zero level: {self.esp32_converter.offset_adc} ADC ({self.esp32_converter.offset_voltage}V)\n"
                
                # Add warnings
                if result['warnings']:
                    conversion_info += f"\n⚠️ WARNINGS:\n"
                    for warning in result['warnings']:
                        conversion_info += f"- {warning}\n"
                
                status = "Success" if result['file_size'] == result['expected_size'] else "Size mismatch"
                if result['warnings']:
                    status += " (with warnings)"
                
                conversion_info += f"\nStatus: {status}\n"
                
                # Update sidebar info
                current_info = self.info_sidebar.current_info.toPlainText()
                self.info_sidebar.set_current_info(current_info + "\n\n" + conversion_info)
                
                # Add to history
                history_item = ConversionHistoryItem(
                    filename=output_filename,
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    duration=self.ecg_data.trim_end - self.ecg_data.trim_start,
                    samples=result['samples'],
                    file_size=result['file_size'],
                    status=status,
                    mode=self.ecg_mode.value
                )
                self.info_sidebar.add_history_item(history_item)
                
                # Open sidebar to show results
                self.info_sidebar.open()
                
                # Show success message
                message = f"ESP32 Binary file created successfully!\n\n"
                message += f"Mode: {self.ecg_mode.value}\n"
                message += f"File: {output_filename}\n"
                message += f"Size: {result['file_size']:,} bytes\n"
                message += f"Duration: {self.ecg_data.trim_end - self.ecg_data.trim_start:.2f}s\n"
                message += f"ADC Range: {result['min_adc']}-{result['max_adc']}\n"
                message += f"Voltage Range: {result['min_voltage']:.3f}V-{result['max_voltage']:.3f}V\n"
                message += f"Location: {self.output_folder}\n"
                
                if result['warnings']:
                    message += f"\n⚠️ {len(result['warnings'])} warning(s) detected. Check info panel for details."
                    QMessageBox.warning(self, "Success with Warnings", message)
                else:
                    QMessageBox.information(self, "Success", message)
                
                # Update status bar
                self.statusBar().showMessage(f"Binary converted: {output_filename} ({result['samples']:,} samples)")
                
            else:
                QMessageBox.critical(self, "Error", f"Conversion failed: {result['error']}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Conversion failed: {str(e)}")
    
    def export_to_csv(self):
        """Export trimmed ECG data to CSV format"""
        if self.ecg_data.signal_trimmed is None:
            QMessageBox.warning(self, "Warning", "No data available for export.")
            return
        
        try:
            # Get active channels data
            active_data, active_names, relative_time = self.get_active_channels_data()
            
            if active_data is None or len(active_names) == 0:
                QMessageBox.warning(self, "Warning", "No active channels selected for export.")
                return
            
            # Export using CSV exporter
            result = self.csv_exporter.export_to_csv(
                active_data, active_names, relative_time,
                self.csv_output_folder, self.record_combo.currentText(),
                self.ecg_mode.value, self.plot_manager.current_y_mode,
                self.ecg_data.trim_start, self.ecg_data.trim_end
            )
            
            if result['success']:
                # Prepare export info
                export_info = self.csv_exporter.get_export_info(
                    result, self.record_combo.currentText(),
                    self.ecg_data.trim_start, self.ecg_data.trim_end
                )
                
                # Update info panel
                current_info = self.info_sidebar.current_info.toPlainText()
                self.info_sidebar.set_current_info(current_info + "\n\n" + export_info)
                
                # Add to history
                history_item = ConversionHistoryItem(
                    filename=result['filename'],
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    duration=result['duration'],
                    samples=result['samples'],
                    file_size=result['file_size'],
                    status="CSV Export Success",
                    mode=f"{result['mode']} ({result['unit_suffix']})"
                )
                self.info_sidebar.add_history_item(history_item)
                
                # Open sidebar to show results
                self.info_sidebar.open()
                
                # Show success message
                message = f"CSV Export completed successfully!\n\n"
                message += f"Mode: {result['mode']}\n"
                message += f"Y-axis: {result['y_mode']}\n"
                message += f"File: {result['filename']}\n"
                message += f"Size: {result['file_size']:,} bytes\n"
                message += f"Duration: {result['duration']:.2f}s\n"
                message += f"Channels: {result['channels']} active\n"
                message += f"Samples: {result['samples']:,}\n"
                message += f"Location: {self.csv_output_folder}\n"
                
                QMessageBox.information(self, "Export Success", message)
                
                # Update status bar
                self.statusBar().showMessage(f"CSV exported: {result['filename']} ({result['channels']} channels, {result['samples']:,} samples)")
                
            else:
                QMessageBox.critical(self, "Export Error", f"CSV export failed: {result['error']}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"CSV export failed: {str(e)}")
    
    def update_info_panel(self):
        """Update info panel with current mode information"""
        if self.ecg_data.record is None:
            return
            
        info_text = f"Record: {self.record_combo.currentText()}\n"
        info_text += f"Mode: {self.ecg_mode.value}\n"
        info_text += f"Channels available: {self.ecg_data.signal.shape[1] if len(self.ecg_data.signal.shape) > 1 else 1}\n"
        info_text += f"Sample rate: {self.ecg_data.sample_rate} Hz\n"
        info_text += f"Total samples: {len(self.ecg_data.signal):,}\n"
        
        if self.ecg_mode == ECGMode.TWELVE_LEAD:
            info_text += f"\nChannel names (12-lead):\n"
            info_text += f"{', '.join(self.ecg_data.CHANNELS_12LEAD)}\n"
        else:
            info_text += f"\nChannel names (10-lead electrodes):\n"
            info_text += f"{', '.join(self.ecg_data.CHANNELS_10LEAD)}\n"
            
            if self.ecg_data.conversion_errors:
                info_text += f"\n⚠️ Conversion Errors:\n"
                for lead, error in self.ecg_data.conversion_errors.items():
                    info_text += f"- {lead}: {error:.3f} mV\n"
        
        info_text += f"\nESP32 Configuration:\n"
        info_text += f"- Gain: {self.esp32_converter.gain}x\n"
        info_text += f"- ADC Resolution: {self.esp32_converter.adc_resolution + 1} levels\n"
        info_text += f"- VCC: {self.esp32_converter.vcc}V\n"
        info_text += f"- Offset: {self.esp32_converter.offset_voltage}V ({self.esp32_converter.offset_adc} ADC)\n"
        
        self.info_sidebar.set_current_info(info_text)
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.timer.isActive():
            self.timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = ECGToBinaryConverter()
    window.show()
    sys.exit(app.exec_()) 