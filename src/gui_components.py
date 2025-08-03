import pyqtgraph as pg
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QComboBox, QCheckBox, QSlider, 
                            QSpinBox, QGridLayout, QGroupBox, QScrollArea,
                            QDoubleSpinBox, QFrame, QTextEdit, QListWidget,
                            QListWidgetItem, QSplitter, QButtonGroup, QRadioButton)
from PyQt5.QtCore import Qt, QPropertyAnimation, QRect, pyqtSignal
from PyQt5.QtGui import QFont
from typing import List, Dict, Callable
from enum import Enum
import numpy as np

class YAxisMode(Enum):
    """Y-axis display modes"""
    ORIGINAL_MV = 0
    ADC_12BIT = 1
    VOLTAGE = 2

class DataMode(Enum):
    """Data display modes"""
    RAW = "raw"
    PROCESSED = "processed"

class ControlPanel(QGroupBox):
    """Control panel component"""
    
    def __init__(self, parent=None):
        super().__init__("Controls", parent)
        self.layout = QGridLayout(self)
        
        # Control elements
        self.record_combo = QComboBox()
        self.mode_combo = QComboBox()
        self.y_mode_combo = QComboBox()
        self.convert_button = QPushButton("Convert to Binary")
        self.export_csv_button = QPushButton("Export to CSV")
        self.info_toggle_btn = QPushButton("Info Panel")
        self.guide_toggle_btn = QPushButton("Guide: ON")
        
        # Playback controls
        self.play_button = QPushButton("Play")
        self.reset_button = QPushButton("Reset")
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_value = QLabel("1.0x")
        
        # Processing controls
        self.window_spinbox = QSpinBox()
        self.gain_spinbox = QSpinBox()
        self.sample_rate_label = QLabel("Sample Rate: -")
        self.duration_label = QLabel("Duration: -")
        
        # ESP32 info
        self.esp32_info_label = QLabel("ESP32: Gain=1000x, ADC=12bit, VCC=3.3V")
        self.gain_warning_label = QLabel("")
        
        # Trim controls
        self.start_spinbox = QDoubleSpinBox()
        self.end_spinbox = QDoubleSpinBox()
        self.trim_info_label = QLabel("Trimmed: - samples")
        
        # Status
        self.conversion_status_label = QLabel("")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup control panel UI"""
        # Row 0: Record selection, Mode selection, Y-axis mode, convert buttons
        self.layout.addWidget(QLabel("Select Record:"), 0, 0)
        self.layout.addWidget(self.record_combo, 0, 1)
        
        self.layout.addWidget(QLabel("Data Mode:"), 0, 2)
        self.mode_combo.addItems(["Processed", "Raw"])
        self.layout.addWidget(self.mode_combo, 0, 3)
        
        self.layout.addWidget(QLabel("Y-Axis:"), 0, 4)
        self.y_mode_combo.addItems(["Original (mV)", "ADC (12bit)", "Voltage (V)"])
        self.layout.addWidget(self.y_mode_combo, 0, 5)
        
        self.convert_button.setEnabled(False)
        self.layout.addWidget(self.convert_button, 0, 6)
        
        self.export_csv_button.setEnabled(False)
        self.export_csv_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")
        self.layout.addWidget(self.export_csv_button, 0, 7)
        
        self.layout.addWidget(self.info_toggle_btn, 0, 8)
        
        self.guide_toggle_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        self.layout.addWidget(self.guide_toggle_btn, 0, 9)
        
        # Row 1: Play controls and speed
        self.layout.addWidget(self.play_button, 1, 0)
        self.layout.addWidget(self.reset_button, 1, 1)
        
        self.layout.addWidget(QLabel("Speed:"), 1, 2)
        self.speed_slider.setMinimum(1)
        self.speed_slider.setMaximum(50)
        self.speed_slider.setValue(10)
        self.layout.addWidget(self.speed_slider, 1, 3, 1, 2)
        self.layout.addWidget(self.speed_value, 1, 5)
        
        self.conversion_status_label.setStyleSheet("color: blue; font-weight: bold;")
        self.layout.addWidget(self.conversion_status_label, 1, 6, 1, 4)
        
        # Row 2: Window size, gain control, and ESP32 info
        self.layout.addWidget(QLabel("Window Size:"), 2, 0)
        self.window_spinbox.setMinimum(100)
        self.window_spinbox.setMaximum(10000)
        self.window_spinbox.setSingleStep(100)
        self.window_spinbox.setValue(2000)
        self.layout.addWidget(self.window_spinbox, 2, 1)
        
        self.layout.addWidget(QLabel("Gain:"), 2, 2)
        self.gain_spinbox.setMinimum(1)
        self.gain_spinbox.setMaximum(10000)
        self.gain_spinbox.setSingleStep(10)
        self.gain_spinbox.setValue(1000)
        self.layout.addWidget(self.gain_spinbox, 2, 3)
        
        self.layout.addWidget(self.sample_rate_label, 2, 4)
        self.layout.addWidget(self.duration_label, 2, 5)
        
        # Row 3: ESP32 info and gain warning
        self.esp32_info_label.setStyleSheet("color: blue; font-weight: bold;")
        self.layout.addWidget(self.esp32_info_label, 3, 0, 1, 4)
        
        self.gain_warning_label.setStyleSheet("color: #FF8C00; font-weight: bold;")
        self.gain_warning_label.setVisible(False)
        self.layout.addWidget(self.gain_warning_label, 3, 4, 1, 6)
        
        # Row 4: Trim controls
        self.layout.addWidget(QLabel("Trim Signal:"), 4, 0)
        self.layout.addWidget(QLabel("Start (s):"), 4, 1)
        
        self.start_spinbox.setMinimum(0.0)
        self.start_spinbox.setMaximum(9999.0)
        self.start_spinbox.setDecimals(2)
        self.start_spinbox.setSingleStep(0.1)
        self.layout.addWidget(self.start_spinbox, 4, 2)
        
        self.layout.addWidget(QLabel("End (s):"), 4, 3)
        
        self.end_spinbox.setMinimum(0.0)
        self.end_spinbox.setMaximum(9999.0)
        self.end_spinbox.setDecimals(2)
        self.end_spinbox.setSingleStep(0.1)
        self.layout.addWidget(self.end_spinbox, 4, 4)
        
        self.layout.addWidget(self.trim_info_label, 4, 5)

class ChannelControlPanel(QGroupBox):
    """Channel control panel component"""
    
    def __init__(self, parent=None):
        super().__init__("Channel Visibility", parent)
        self.layout = QGridLayout(self)
        
        # Channel checkboxes
        self.channel_checkboxes = []
        self.max_channels = 12
        
        # Buttons
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup channel control UI"""
        # Add Select All / Deselect All buttons
        self.layout.addWidget(self.select_all_btn, 0, 0, 1, 3)
        self.layout.addWidget(self.deselect_all_btn, 0, 3, 1, 3)
        
        # Create channel checkboxes
        for i in range(self.max_channels):
            checkbox = QCheckBox(f"Ch{i+1}")
            checkbox.setChecked(True)
            
            row = (i // 6) + 1  # Start from row 1 due to buttons
            col = i % 6
            self.layout.addWidget(checkbox, row, col)
            self.channel_checkboxes.append(checkbox)
    
    def update_channel_labels(self, channel_names: List[str]):
        """Update channel labels"""
        for i, checkbox in enumerate(self.channel_checkboxes):
            if i < len(channel_names):
                checkbox.setText(channel_names[i])
                checkbox.setVisible(True)
                checkbox.setEnabled(True)
            else:
                checkbox.setVisible(False)
                checkbox.setEnabled(False)
    
    def get_visible_channels(self) -> List[bool]:
        """Get list of visible channels"""
        return [checkbox.isChecked() for checkbox in self.channel_checkboxes]

class InfoPanel(QFrame):
    """Collapsible info panel component"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_collapsed = True
        self.animation_duration = 200
        self.panel_width = 400
        
        # Style
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
                border: 1px solid #ccc;
                border-left: none;
            }
        """)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Header
        self.header = QFrame()
        self.header.setFixedHeight(40)
        self.header.setStyleSheet("""
            QFrame {
                background-color: #e0e0e0;
                border-bottom: 1px solid #ccc;
            }
        """)
        
        self.header_layout = QHBoxLayout(self.header)
        self.title_label = QLabel("Conversion Information")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Content area with splitter
        self.content_splitter = QSplitter(Qt.Vertical)
        
        # Current conversion info
        self.current_group = QGroupBox("Current Conversion")
        self.current_layout = QVBoxLayout(self.current_group)
        self.current_info = QTextEdit()
        self.current_info.setReadOnly(True)
        self.current_layout.addWidget(self.current_info)
        
        # History
        self.history_group = QGroupBox("Conversion History (Last 10)")
        self.history_layout = QVBoxLayout(self.history_group)
        
        # History list
        self.history_list = QListWidget()
        self.history_list.setAlternatingRowColors(True)
        self.history_layout.addWidget(self.history_list)
        
        # Clear history button
        self.clear_history_btn = QPushButton("Clear History")
        self.history_layout.addWidget(self.clear_history_btn)
        
        # Add to splitter
        self.content_splitter.addWidget(self.current_group)
        self.content_splitter.addWidget(self.history_group)
        self.content_splitter.setSizes([200, 400])
        
        # Add to main layout
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.content_splitter)
        
        # Animation
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(self.animation_duration)
        
        # Initially collapsed
        self.setFixedWidth(0)
    
    def toggle(self):
        """Toggle panel visibility"""
        self.is_collapsed = not self.is_collapsed
        
        parent_rect = self.parent().rect()
        
        if self.is_collapsed:
            start_rect = QRect(0, 0, self.panel_width, parent_rect.height())
            end_rect = QRect(-self.panel_width, 0, self.panel_width, parent_rect.height())
        else:
            start_rect = QRect(-self.panel_width, 0, self.panel_width, parent_rect.height())
            end_rect = QRect(0, 0, self.panel_width, parent_rect.height())
            self.raise_()
        
        self.setFixedWidth(self.panel_width)
        self.animation.setStartValue(start_rect)
        self.animation.setEndValue(end_rect)
        self.animation.start()
    
    def set_current_info(self, text: str):
        """Update current conversion info"""
        self.current_info.setText(text)
    
    def add_history_item(self, item: Dict):
        """Add item to history"""
        text = f"{item.get('timestamp', '')} - {item.get('filename', '')}\n"
        text += f"Mode: {item.get('mode', '')}, Status: {item.get('status', '')}"
        
        list_item = QListWidgetItem(text)
        if item.get('status', '') != "Success":
            list_item.setForeground(Qt.red)
        
        self.history_list.addItem(list_item)
        
        # Keep only last 10 items
        while self.history_list.count() > 10:
            self.history_list.takeItem(0)

class PlotArea(QWidget):
    """Plot area component"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Scroll area for plots
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.layout.addWidget(self.scroll_area)
        
        # Container for plots
        self.plots_widget = QWidget()
        self.plots_layout = QVBoxLayout(self.plots_widget)
        self.plots_layout.setSpacing(2)
        self.scroll_area.setWidget(self.plots_widget)
        
        # Message label for no channels
        self.no_channel_label = QLabel("No channels selected")
        self.no_channel_label.setAlignment(Qt.AlignCenter)
        self.no_channel_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: #666;
                padding: 50px;
            }
        """)
        self.no_channel_label.hide()
        self.plots_layout.addWidget(self.no_channel_label)
        
        # Create plot widgets
        self.plot_widgets = []
        self.plot_lines = []
        self.guide_lines_x = []
        self.guide_lines_y_zero = []
        self.guide_lines_y_offset = []
        
        self.max_channels = 12
        self.channel_colors = [
            (255, 0, 0), (0, 0, 255), (0, 128, 0), (128, 0, 128),
            (255, 165, 0), (0, 128, 128), (128, 0, 0), (0, 0, 128),
            (128, 128, 0), (255, 0, 255), (0, 0, 0), (64, 64, 64)
        ]
        
        self.create_plot_widgets()
    
    def create_plot_widgets(self):
        """Create plot widgets"""
        for i in range(self.max_channels):
            # Create plot widget
            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.setLabel('left', f"Ch{i+1}")
            
            # Always show x-axis values for all plots, but only label the last one
            plot_widget.getAxis('bottom').setStyle(showValues=True)
            
            # Plot line for data
            pen = pg.mkPen(color=self.channel_colors[i], width=2)
            plot_line = plot_widget.plot(pen=pen)
            
            # Guide lines
            # X-axis guide line (time = 0, solid black)
            pen_x_guide = pg.mkPen(color='black', width=1, style=1)
            guide_line_x = plot_widget.addLine(x=0, pen=pen_x_guide)
            
            # Y-axis guide line (value = 0, solid black)
            pen_y_zero_guide = pg.mkPen(color='black', width=1, style=1)
            guide_line_y_zero = plot_widget.addLine(y=0, pen=pen_y_zero_guide)
            
            # Y-axis offset guide line (dashed black)
            pen_y_offset_guide = pg.mkPen(color='black', width=1, style=2)
            guide_line_y_offset = plot_widget.addLine(y=2048, pen=pen_y_offset_guide)
            
            self.plots_layout.addWidget(plot_widget)
            self.plot_widgets.append(plot_widget)
            self.plot_lines.append(plot_line)
            self.guide_lines_x.append(guide_line_x)
            self.guide_lines_y_zero.append(guide_line_y_zero)
            self.guide_lines_y_offset.append(guide_line_y_offset)
            
            plot_widget.setVisible(False)
        
        # Link X axes
        for i in range(1, self.max_channels):
            self.plot_widgets[i].setXLink(self.plot_widgets[0])
    
    def update_plot_layout(self, visible_channels: List[bool]):
        """Update plot layout based on visible channels"""
        visible_count = sum(visible_channels)
        
        if visible_count == 0:
            # Hide all plots and show message
            for plot in self.plot_widgets:
                plot.hide()
            self.no_channel_label.show()
            return
        else:
            self.no_channel_label.hide()
        
        # Calculate height for each plot
        available_height = self.scroll_area.height()
        if visible_count <= 3:
            plot_height = available_height // visible_count
        else:
            plot_height = available_height // 3  # Minimum 1/3 height
        
        # Update plot visibility and height
        visible_idx = 0
        last_visible_idx = -1
        
        # First, find the last visible channel
        for i in range(self.max_channels):
            if visible_channels[i]:
                last_visible_idx = i
        
        for i, plot in enumerate(self.plot_widgets):
            if i < len(visible_channels) and visible_channels[i]:
                plot.setMinimumHeight(plot_height)
                plot.setMaximumHeight(plot_height if visible_count <= 3 else 16777215)
                
                # Show x-axis label only for the last visible plot
                if i == last_visible_idx:
                    plot.setLabel('bottom', 'Time (seconds)')
                else:
                    plot.setLabel('bottom', '')
                
                plot.show()
                visible_idx += 1
            else:
                plot.hide()
    
    def update_plots(self, time_data: np.ndarray, signal_data: np.ndarray, 
                    visible_channels: List[bool], y_mode: YAxisMode):
        """Update all plots with current data"""
        if signal_data is None or len(signal_data) == 0:
            return
        
        # Update each channel
        for i in range(self.max_channels):
            if i < len(visible_channels) and visible_channels[i]:
                # Get channel data
                channel_data = signal_data[:, i]
                
                # Update plot
                self.plot_lines[i].setData(time_data, channel_data)
                
                # Auto-scale based on current mode
                if len(channel_data) > 0 and np.any(channel_data != 0):
                    min_val = np.min(channel_data)
                    max_val = np.max(channel_data)
                    padding = (max_val - min_val) * 0.1 if max_val != min_val else 0.1
                    self.plot_widgets[i].setYRange(min_val - padding, max_val + padding)
                else:
                    # Set default range based on mode
                    if y_mode == YAxisMode.ORIGINAL_MV:
                        self.plot_widgets[i].setYRange(-6, 6)
                    elif y_mode == YAxisMode.ADC_12BIT:
                        self.plot_widgets[i].setYRange(0, 4095)
                    else:  # VOLTAGE
                        self.plot_widgets[i].setYRange(0, 3.3)
        
        # Update x range with actual time values
        if len(time_data) > 0:
            self.plot_widgets[0].setXRange(time_data[0], time_data[-1])
    
    def update_channel_labels(self, channel_names: List[str]):
        """Update channel labels"""
        for i, plot in enumerate(self.plot_widgets):
            if i < len(channel_names):
                plot.setTitle(channel_names[i])
                plot.setLabel('left', channel_names[i])
    
    def update_guide_lines(self, show_guides: bool, y_mode: YAxisMode):
        """Update guide lines visibility"""
        for i in range(self.max_channels):
            # X-axis guide line (time = 0)
            self.guide_lines_x[i].setVisible(show_guides)
            
            # Y-axis guide line (value = 0)
            self.guide_lines_y_zero[i].setVisible(show_guides)
            
            # Y-axis offset guide line
            if show_guides:
                if y_mode == YAxisMode.ORIGINAL_MV:
                    self.guide_lines_y_offset[i].setVisible(False)
                elif y_mode == YAxisMode.ADC_12BIT:
                    self.guide_lines_y_offset[i].setValue(2048)
                    self.guide_lines_y_offset[i].setVisible(True)
                elif y_mode == YAxisMode.VOLTAGE:
                    self.guide_lines_y_offset[i].setValue(1.65)
                    self.guide_lines_y_offset[i].setVisible(True)
            else:
                self.guide_lines_y_offset[i].setVisible(False) 