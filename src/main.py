import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import os

# Import our modules
from data_loader import ECGDataLoader, DataMode
from signal_processor import ECGSignalProcessor, YAxisMode
from gui_components import ControlPanel, ChannelControlPanel, InfoPanel, PlotArea
from converter import ECGConverter

class ECGConverterApp(QMainWindow):
    """Main ECG Converter Application"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize modules
        self.data_loader = ECGDataLoader()
        self.signal_processor = ECGSignalProcessor()
        self.converter = ECGConverter()
        
        # Application state
        self.current_data = None
        self.current_time = None
        self.current_channel_names = []
        self.current_mode = DataMode.PROCESSED
        self.current_y_mode = YAxisMode.ORIGINAL_MV
        self.show_guide_lines = True
        
        # Playback state
        self.playing = False
        self.play_speed = 1.0
        self.current_index = 0
        self.window_size = 2000
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.setInterval(25)
        self.timer.timeout.connect(self.update_plot)
        
        # Setup UI
        self.setup_ui()
        self.setup_connections()
        
        # Load initial data
        self.load_available_records()
        
        # Status bar
        self.statusBar().showMessage("Ready. Please select a record from sampleRaw folder.")
    
    def setup_ui(self):
        """Setup main UI"""
        self.setWindowTitle("ECG Converter - Modular Version")
        self.setGeometry(100, 50, 1400, 900)
        
        # Main widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # Create UI components
        self.control_panel = ControlPanel()
        self.channel_panel = ChannelControlPanel()
        self.plot_area = PlotArea()
        
        # Create info panel (initially hidden)
        self.info_panel = InfoPanel(self.plot_area)
        
        # Add components to layout
        self.main_layout.addWidget(self.control_panel)
        self.main_layout.addWidget(self.channel_panel)
        self.main_layout.addWidget(self.plot_area)
    
    def setup_connections(self):
        """Setup signal connections"""
        # Control panel connections
        self.control_panel.record_combo.currentTextChanged.connect(self.load_record)
        self.control_panel.mode_combo.currentIndexChanged.connect(self.change_data_mode)
        self.control_panel.y_mode_combo.currentIndexChanged.connect(self.change_y_mode)
        self.control_panel.convert_button.clicked.connect(self.convert_to_binary)
        self.control_panel.export_csv_button.clicked.connect(self.export_to_csv)
        self.control_panel.info_toggle_btn.clicked.connect(self.toggle_info_panel)
        self.control_panel.guide_toggle_btn.clicked.connect(self.toggle_guide_lines)
        
        # Playback controls
        self.control_panel.play_button.clicked.connect(self.toggle_play)
        self.control_panel.reset_button.clicked.connect(self.reset_playback)
        self.control_panel.speed_slider.valueChanged.connect(self.change_speed)
        
        # Processing controls
        self.control_panel.window_spinbox.valueChanged.connect(self.change_window_size)
        self.control_panel.gain_spinbox.valueChanged.connect(self.change_gain)
        self.control_panel.start_spinbox.valueChanged.connect(self.update_trim)
        self.control_panel.end_spinbox.valueChanged.connect(self.update_trim)
        
        # Channel controls
        self.channel_panel.select_all_btn.clicked.connect(self.select_all_channels)
        self.channel_panel.deselect_all_btn.clicked.connect(self.deselect_all_channels)
        
        # Connect channel checkboxes
        for checkbox in self.channel_panel.channel_checkboxes:
            checkbox.stateChanged.connect(self.update_plot_layout)
    
    def load_available_records(self):
        """Load available records into combo box"""
        records = self.data_loader.get_available_records()
        if records:
            self.control_panel.record_combo.addItems(records)
        else:
            self.statusBar().showMessage("No records found in sampleRaw folder.")
    
    def load_record(self, record_name: str):
        """Load selected record"""
        if not record_name:
            return
        
        try:
            self.statusBar().showMessage(f"Loading record {record_name}...")
            
            # Load record
            if self.data_loader.load_record(record_name):
                # Get record info
                record_info = self.data_loader.get_record_info()
                
                # Update UI with record info
                self.control_panel.sample_rate_label.setText(f"Sample Rate: {record_info['sample_rate']} Hz")
                
                duration = record_info['duration']
                minutes = int(duration // 60)
                seconds = int(duration % 60)
                self.control_panel.duration_label.setText(f"Duration: {minutes}:{seconds:02d}")
                
                # Set trim range
                self.control_panel.start_spinbox.setMaximum(duration)
                self.control_panel.end_spinbox.setMaximum(duration)
                self.control_panel.end_spinbox.setValue(duration)
                
                # Update processor
                self.signal_processor.set_sample_rate(record_info['sample_rate'])
                
                # Load initial data
                self.load_current_data()
                
                # Enable controls
                self.control_panel.convert_button.setEnabled(True)
                self.control_panel.export_csv_button.setEnabled(True)
                
                self.statusBar().showMessage(f"Record {record_name} loaded successfully.")
            else:
                self.statusBar().showMessage(f"Error loading record {record_name}")
                
        except Exception as e:
            self.statusBar().showMessage(f"Error loading record: {str(e)}")
    
    def load_current_data(self):
        """Load current data based on mode"""
        # Get data based on current mode
        self.current_data = self.data_loader.get_channel_data(self.current_mode)
        self.current_time = self.data_loader.get_time_array()
        self.current_channel_names = self.data_loader.get_channel_names(self.current_mode)
        
        # Update channel labels
        self.channel_panel.update_channel_labels(self.current_channel_names)
        self.plot_area.update_channel_labels(self.current_channel_names)
        
        # Update trim range
        if self.current_data is not None and len(self.current_data) > 0:
            duration = len(self.current_data) / self.signal_processor.sample_rate
            self.control_panel.end_spinbox.setValue(duration)
            
            # Apply initial trim
            self.update_trim()
    
    def change_data_mode(self, index: int):
        """Change between raw and processed data mode"""
        if index == 0:
            self.current_mode = DataMode.PROCESSED
            self.control_panel.conversion_status_label.setText("Mode: Processed Data")
            self.control_panel.conversion_status_label.setStyleSheet("color: blue; font-weight: bold;")
        else:
            self.current_mode = DataMode.RAW
            self.control_panel.conversion_status_label.setText("Mode: Raw Data")
            self.control_panel.conversion_status_label.setStyleSheet("color: green; font-weight: bold;")
        
        # Reload data with new mode
        self.load_current_data()
        
        # Update plots
        self.update_plots()
    
    def change_y_mode(self, index: int):
        """Change Y-axis display mode"""
        self.current_y_mode = YAxisMode(index)
        
        # Update plots
        self.update_plots()
        
        # Update guide lines
        self.plot_area.update_guide_lines(self.show_guide_lines, self.current_y_mode)
    
    def change_gain(self, value: int):
        """Change gain value"""
        self.signal_processor.set_gain(value)
        
        # Update ESP32 info label
        self.control_panel.esp32_info_label.setText(f"ESP32: Gain={value}x, ADC=12bit, VCC=3.3V")
        
        # Check for warnings
        self.check_gain_warnings()
        
        # Update plots
        self.update_plots()
    
    def check_gain_warnings(self):
        """Check for gain warnings"""
        if self.current_data is None:
            self.control_panel.gain_warning_label.setVisible(False)
            return
        
        # Check warnings for each channel
        for i in range(self.current_data.shape[1]):
            if np.any(self.current_data[:, i] != 0):
                warning = self.signal_processor.check_gain_warnings(self.current_data[:, i])
                if warning['warning']:
                    self.control_panel.gain_warning_label.setText(warning['message'])
                    self.control_panel.gain_warning_label.setVisible(True)
                    self.control_panel.convert_button.setEnabled(False)
                    return
        
        # No warnings
        self.control_panel.gain_warning_label.setVisible(False)
        self.control_panel.convert_button.setEnabled(True)
    
    def update_trim(self):
        """Update signal trimming"""
        if self.current_data is None:
            return
        
        # Get trim values
        start_time = self.control_panel.start_spinbox.value()
        end_time = self.control_panel.end_spinbox.value()
        
        # Ensure valid range
        if end_time <= start_time:
            end_time = start_time + 0.1
            self.control_panel.end_spinbox.setValue(end_time)
        
        # Set trim range in processor
        self.signal_processor.set_trim_range(start_time, end_time)
        
        # Trim data
        trimmed_data, trimmed_time = self.signal_processor.trim_signal(self.current_data, self.current_time)
        
        # Update current data
        self.current_data = trimmed_data
        self.current_time = trimmed_time
        
        # Update info
        trimmed_samples = len(self.current_data)
        self.control_panel.trim_info_label.setText(f"Trimmed: {trimmed_samples:,} samples")
        
        # Reset playback
        self.current_index = 0
        
        # Check warnings
        self.check_gain_warnings()
        
        # Update plots
        self.update_plots()
    
    def change_window_size(self, value: int):
        """Change display window size"""
        self.window_size = value
        self.update_plots()
    
    def change_speed(self, value: int):
        """Change playback speed"""
        self.play_speed = value / 10.0
        self.control_panel.speed_value.setText(f"{self.play_speed:.1f}x")
    
    def toggle_play(self):
        """Toggle play/pause"""
        if self.playing:
            self.timer.stop()
            self.playing = False
            self.control_panel.play_button.setText("Play")
        else:
            self.timer.start()
            self.playing = True
            self.control_panel.play_button.setText("Pause")
    
    def reset_playback(self):
        """Reset to beginning"""
        self.current_index = 0
        self.update_plots()
    
    def update_plot(self):
        """Timer update for animation"""
        if self.current_data is None:
            return
        
        # Increment based on speed
        increment = int(self.window_size * 0.1 * self.play_speed)
        self.current_index += increment
        
        # Loop back to start
        if self.current_index >= len(self.current_data) - self.window_size:
            self.current_index = 0
        
        self.update_plots()
    
    def update_plots(self):
        """Update all plots"""
        if self.current_data is None:
            return
        
        # Get visible channels
        visible_channels = self.channel_panel.get_visible_channels()
        
        # Update plot layout
        self.plot_area.update_plot_layout(visible_channels)
        
        # Get current window data
        end_idx = min(self.current_index + self.window_size, len(self.current_data))
        window_data = self.current_data[self.current_index:end_idx]
        window_time = self.current_time[self.current_index:end_idx]
        
        # Convert data for display
        display_data = np.zeros_like(window_data)
        for i in range(window_data.shape[1]):
            display_data[:, i] = self.signal_processor.get_display_data(window_data[:, i], self.current_y_mode)
        
        # Update plots
        self.plot_area.update_plots(window_time, display_data, visible_channels, self.current_y_mode)
    
    def update_plot_layout(self):
        """Update plot layout when channels change"""
        self.update_plots()
    
    def select_all_channels(self):
        """Select all channel checkboxes"""
        for checkbox in self.channel_panel.channel_checkboxes:
            if checkbox.isVisible():
                checkbox.setChecked(True)
    
    def deselect_all_channels(self):
        """Deselect all channel checkboxes"""
        for checkbox in self.channel_panel.channel_checkboxes:
            if checkbox.isVisible():
                checkbox.setChecked(False)
    
    def toggle_guide_lines(self):
        """Toggle guide lines visibility"""
        self.show_guide_lines = not self.show_guide_lines
        
        # Update button appearance
        if self.show_guide_lines:
            self.control_panel.guide_toggle_btn.setText("Guide: ON")
            self.control_panel.guide_toggle_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        else:
            self.control_panel.guide_toggle_btn.setText("Guide: OFF")
            self.control_panel.guide_toggle_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        
        # Update guide lines
        self.plot_area.update_guide_lines(self.show_guide_lines, self.current_y_mode)
    
    def toggle_info_panel(self):
        """Toggle info panel"""
        self.info_panel.toggle()
    
    def convert_to_binary(self):
        """Convert current data to binary format"""
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "No data available for conversion.")
            return
        
        try:
            # Get current record name
            record_name = self.control_panel.record_combo.currentText()
            
            # Convert to binary
            result = self.converter.convert_to_binary(
                self.current_data, record_name, self.current_mode, self.signal_processor
            )
            
            if result['success']:
                # Update info panel
                self.info_panel.set_current_info(result['conversion_info'])
                
                # Add to history
                history_item = self.converter.create_history_item(result, self.current_mode)
                self.info_panel.add_history_item(history_item)
                
                # Show info panel
                self.info_panel.toggle()
                
                # Show success message
                message = f"Binary file created successfully!\n\n"
                message += f"File: {result['filename']}\n"
                message += f"Size: {result['file_size']:,} bytes\n"
                message += f"Samples: {result['samples']:,}\n"
                message += f"ADC Range: {result['min_adc']}-{result['max_adc']}\n"
                message += f"Voltage Range: {result['min_voltage']:.3f}V-{result['max_voltage']:.3f}V"
                
                if result['warnings']:
                    message += f"\n\n⚠️ {len(result['warnings'])} warning(s) detected."
                    QMessageBox.warning(self, "Success with Warnings", message)
                else:
                    QMessageBox.information(self, "Success", message)
                
                self.statusBar().showMessage(f"Binary exported: {result['filename']}")
            else:
                QMessageBox.critical(self, "Error", f"Conversion failed: {result['error']}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Conversion failed: {str(e)}")
    
    def export_to_csv(self):
        """Export current data to CSV format"""
        if self.current_data is None:
            QMessageBox.warning(self, "Warning", "No data available for export.")
            return
        
        try:
            # Get current record name
            record_name = self.control_panel.record_combo.currentText()
            
            # Get visible channels
            visible_channels = self.channel_panel.get_visible_channels()
            visible_channel_names = [name for i, name in enumerate(self.current_channel_names) if visible_channels[i]]
            
            # Export to CSV
            result = self.converter.export_to_csv(
                self.current_data, self.current_time, visible_channel_names,
                record_name, self.current_mode, self.current_y_mode, self.signal_processor
            )
            
            if result['success']:
                # Update info panel
                self.info_panel.set_current_info(result['export_info'])
                
                # Add to history
                history_item = self.converter.create_history_item(result, self.current_mode)
                self.info_panel.add_history_item(history_item)
                
                # Show info panel
                self.info_panel.toggle()
                
                # Show success message
                message = f"CSV Export completed successfully!\n\n"
                message += f"File: {result['filename']}\n"
                message += f"Size: {result['file_size']:,} bytes\n"
                message += f"Samples: {result['samples']:,}\n"
                message += f"Channels: {result['channels']}\n"
                message += f"Unit: {result['unit']}"
                
                QMessageBox.information(self, "Export Success", message)
                
                self.statusBar().showMessage(f"CSV exported: {result['filename']}")
            else:
                QMessageBox.critical(self, "Error", f"Export failed: {result['error']}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.timer.isActive():
            self.timer.stop()
        event.accept()

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Set application font
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    # Create and show main window
    window = ECGConverterApp()
    window.show()
    
    # Start application
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 