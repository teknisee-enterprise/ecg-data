"""
Plot Management UI Component
"""
import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QLabel)
from PyQt5.QtCore import Qt


class PlotManager:
    """Manages ECG plot widgets and display"""
    
    def __init__(self, max_channels=12):
        self.max_channels = max_channels
        
        # Channel colors
        self.channel_colors = [
            (255, 0, 0), (0, 0, 255), (0, 128, 0), (128, 0, 128),
            (255, 165, 0), (0, 128, 128), (128, 0, 0), (0, 0, 128),
            (128, 128, 0), (255, 0, 255), (0, 0, 0), (64, 64, 64)
        ]
        
        # Plot components
        self.plot_widgets = []
        self.plot_lines = []
        self.guide_lines_x = []  # X-axis guide lines (time = 0)
        self.guide_lines_y_zero = []  # Y-axis guide lines (value = 0)
        self.guide_lines_y_offset = []  # Y-axis guide lines (offset values)
        
        # Display state
        self.show_guide_lines = True
        self.current_y_mode = 0
        self.y_axis_modes = [
            "Asli (mV)",
            "Hasil (12bit)", 
            "Tegangan Hasil (V)"
        ]
        
        # Channel visibility
        self.show_channel = [True] * self.max_channels
        
        # ESP32 configuration for display
        self.adc_resolution = 4095
        self.vcc = 3.3
    
    def create_plot_area(self, parent_layout):
        """Create plot area with scrollable plots"""
        # Container for plot area
        self.plot_container = QWidget()
        self.plot_container_layout = QVBoxLayout(self.plot_container)
        self.plot_container_layout.setContentsMargins(0, 0, 0, 0)
        self.plot_container_layout.setSpacing(0)
        parent_layout.addWidget(self.plot_container)
        
        # Scroll area for plots
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.plot_container_layout.addWidget(self.scroll_area)
        
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
        self._create_plot_widgets()
    
    def _create_plot_widgets(self):
        """Create individual plot widgets"""
        for i in range(self.max_channels):
            # Create plot widget
            plot_widget = pg.PlotWidget()
            plot_widget.setBackground('w')
            plot_widget.showGrid(x=True, y=True, alpha=0.3)
            plot_widget.setLabel('left', self._get_y_label(i))
            
            # Always show x-axis values for all plots, but only label the last one
            plot_widget.getAxis('bottom').setStyle(showValues=True)
            
            # Set initial title
            channels_12lead = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 
                             'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
            if i < len(channels_12lead):
                plot_widget.setTitle(channels_12lead[i])
            
            # Plot line for data
            pen = pg.mkPen(color=self.channel_colors[i], width=2)
            plot_line = plot_widget.plot(pen=pen)
            
            # Guide lines
            # X-axis guide line (time = 0, solid black)
            pen_x_guide = pg.mkPen(color='black', width=1, style=1)  # solid
            guide_line_x = plot_widget.addLine(x=0, pen=pen_x_guide)
            
            # Y-axis guide line (value = 0, solid black)
            pen_y_zero_guide = pg.mkPen(color='black', width=1, style=1)  # solid
            guide_line_y_zero = plot_widget.addLine(y=0, pen=pen_y_zero_guide)
            
            # Y-axis offset guide line (dashed black)
            pen_y_offset_guide = pg.mkPen(color='black', width=1, style=2)  # dashed
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
    
    def _get_y_label(self, channel_idx):
        """Get Y-axis label based on current mode"""
        channels_12lead = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 
                         'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
        channels_10lead = ['RA', 'LA', 'LL', 'RL', 
                         'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
        
        if channel_idx < len(channels_12lead):
            channel = channels_12lead[channel_idx]
        else:
            channel = f"Ch{channel_idx+1}"
            
        mode = self.y_axis_modes[self.current_y_mode]
        return f"{channel}\n({mode})"
    
    def update_channel_display(self, ecg_mode, channels_12lead, channels_10lead):
        """Update channel labels and visibility based on mode"""
        if ecg_mode == "12-lead":
            # 12-lead mode: show all 12 channels
            channels = channels_12lead
            max_visible = 12
        else:
            # 10-lead mode: show only 10 channels
            channels = channels_10lead
            max_visible = 10
        
        # Update checkboxes and plot titles
        for i in range(self.max_channels):
            if i < len(channels):
                self.plot_widgets[i].setTitle(channels[i])
                self.plot_widgets[i].setLabel('left', self._get_y_label(i))
                self.plot_widgets[i].setVisible(True)
            else:
                self.plot_widgets[i].setVisible(False)
                self.show_channel[i] = False
    
    def update_plot_layout(self, ecg_mode):
        """Update plot layout based on visible channels"""
        # Count visible channels based on mode
        if ecg_mode == "10-lead":
            max_channels = 10
        else:
            max_channels = 12
        
        visible_count = sum(self.show_channel[:max_channels])
        
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
        for i in range(max_channels):
            if self.show_channel[i]:
                last_visible_idx = i
        
        for i, plot in enumerate(self.plot_widgets):
            if i < max_channels and self.show_channel[i]:
                plot.setMinimumHeight(plot_height)
                plot.setMaximumHeight(plot_height if visible_count <= 3 else 16777215)
                
                # Show x-axis label only for the last visible plot
                if i == last_visible_idx:
                    plot.setLabel('bottom', 'Waktu (detik)')
                else:
                    plot.setLabel('bottom', '')
                
                plot.show()
                visible_idx += 1
            else:
                plot.hide()
        
        # Update guide lines visibility
        self.update_guide_lines()
    
    def update_guide_lines(self):
        """Update guide lines based on current mode and toggle state"""
        for i in range(self.max_channels):
            if not self.show_channel[i]:
                continue
                
            # X-axis guide line (time = 0) - always shown if guide lines enabled
            self.guide_lines_x[i].setVisible(self.show_guide_lines)
            
            # Y-axis guide line (value = 0) - always shown if guide lines enabled
            self.guide_lines_y_zero[i].setVisible(self.show_guide_lines)
            
            # Y-axis offset guide line - depends on mode
            if self.show_guide_lines:
                if self.current_y_mode == 0:  # Asli (mV) - no offset line
                    self.guide_lines_y_offset[i].setVisible(False)
                elif self.current_y_mode == 1:  # Hasil (12bit) - line at 2048
                    self.guide_lines_y_offset[i].setValue(2048)
                    self.guide_lines_y_offset[i].setVisible(True)
                elif self.current_y_mode == 2:  # Tegangan Hasil (V) - line at 1.65
                    self.guide_lines_y_offset[i].setValue(1.65)
                    self.guide_lines_y_offset[i].setVisible(True)
            else:
                self.guide_lines_y_offset[i].setVisible(False)
    
    def toggle_guide_lines(self):
        """Toggle guide lines visibility"""
        self.show_guide_lines = not self.show_guide_lines
        self.update_guide_lines()
        return self.show_guide_lines
    
    def update_plots(self, signal_data, time_data, current_index, window_size, 
                    ecg_mode, esp32_converter):
        """Update all plots with current window"""
        if signal_data is None:
            return
        
        end_idx = min(current_index + window_size, len(signal_data))
        visible_time = time_data[current_index:end_idx]
        
        # Update each channel
        for i in range(self.max_channels):
            if i < len(signal_data[0]) and self.show_channel[i]:
                # Get raw data in mV
                raw_data = signal_data[current_index:end_idx, i]
                
                # Convert to display format based on Y-axis mode
                visible_data = esp32_converter.get_display_data(raw_data, self.current_y_mode)
                
                # Update plot - time axis shows actual time with offset
                self.plot_lines[i].setData(visible_time, visible_data)
                
                # Auto-scale based on current mode
                if len(visible_data) > 0 and np.any(visible_data != 0):
                    min_val = np.min(visible_data)
                    max_val = np.max(visible_data)
                    padding = (max_val - min_val) * 0.1 if max_val != min_val else 0.1
                    self.plot_widgets[i].setYRange(min_val - padding, max_val + padding)
                else:
                    # Set default range based on mode
                    if self.current_y_mode == 0:  # mV
                        self.plot_widgets[i].setYRange(-6, 6)
                    elif self.current_y_mode == 1:  # 12bit
                        self.plot_widgets[i].setYRange(0, self.adc_resolution)
                    else:  # Voltage
                        self.plot_widgets[i].setYRange(0, self.vcc)
        
        # Update x range with actual time values
        if len(visible_time) > 0:
            self.plot_widgets[0].setXRange(visible_time[0], visible_time[-1])
    
    def set_channel_visibility(self, channel, state):
        """Set channel visibility"""
        self.show_channel[channel] = state > 0
    
    def change_y_mode(self, y_mode):
        """Change Y-axis display mode"""
        self.current_y_mode = y_mode
        
        # Update all plot labels
        for i in range(self.max_channels):
            self.plot_widgets[i].setLabel('left', self._get_y_label(i))
        
        # Update guide lines for new mode
        self.update_guide_lines()
    
    def get_plot_container(self):
        """Get the plot container widget"""
        return self.plot_container 