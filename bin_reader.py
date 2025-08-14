import sys
import os
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QPushButton, QLabel, QSpinBox, QSlider, QFileDialog, QScrollArea,
    QCheckBox
)
from PyQt5.QtCore import Qt


class BinReaderApp(QMainWindow):
    """Simple 12-channel BIN reader and viewer (single file).

    Features:
    - Open and read 12-channel .bin (uint16, little-endian)
    - Set sample frequency
    - Show 12 signals with simple scrolling window
    - Select channels with checkboxes (Select All / Deselect All)
    """

    def __init__(self):
        super().__init__()

        # Data state
        self.file_path = None
        self.data_adc = None  # shape: (num_samples, 12) uint16
        self.time_axis = None

        # Display state
        self.sample_rate = 360
        self.window_size = 2000
        self.position_index = 0
        self.max_channels = 12
        self.show_channel = [True] * self.max_channels

        # UI
        self.setWindowTitle("BIN Reader - Simple 12-channel Viewer")
        self.setGeometry(120, 80, 1200, 800)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # Controls group
        self.controls_group = QGroupBox("Controls")
        main_layout.addWidget(self.controls_group)
        ctrl_layout = QGridLayout(self.controls_group)

        # Row 0: Open file, path label
        self.open_btn = QPushButton("Open BIN…")
        ctrl_layout.addWidget(self.open_btn, 0, 0)

        self.file_label = QLabel("No file loaded")
        self.file_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ctrl_layout.addWidget(self.file_label, 0, 1, 1, 5)

        # Row 1: Sample rate, window size, position slider
        ctrl_layout.addWidget(QLabel("Freq (Hz):"), 1, 0)
        self.freq_spin = QSpinBox()
        self.freq_spin.setRange(1, 10000)
        self.freq_spin.setValue(self.sample_rate)
        self.freq_spin.setSingleStep(10)
        ctrl_layout.addWidget(self.freq_spin, 1, 1)

        ctrl_layout.addWidget(QLabel("Window (samples):"), 1, 2)
        self.window_spin = QSpinBox()
        self.window_spin.setRange(100, 1000000)
        self.window_spin.setValue(self.window_size)
        self.window_spin.setSingleStep(100)
        ctrl_layout.addWidget(self.window_spin, 1, 3)

        ctrl_layout.addWidget(QLabel("Position:"), 1, 4)
        self.pos_slider = QSlider(Qt.Horizontal)
        self.pos_slider.setRange(0, 0)
        ctrl_layout.addWidget(self.pos_slider, 1, 5)

        # Row 2: Select all / Deselect all
        self.select_all_btn = QPushButton("Select All")
        self.deselect_all_btn = QPushButton("Deselect All")
        ctrl_layout.addWidget(self.select_all_btn, 2, 0, 1, 3)
        ctrl_layout.addWidget(self.deselect_all_btn, 2, 3, 1, 3)

        # Channel checkboxes
        self.channels_group = QGroupBox("Channels")
        main_layout.addWidget(self.channels_group)
        ch_layout = QGridLayout(self.channels_group)
        self.channel_checkboxes = []
        default_labels = [
            'RA', 'LA', 'LL', 'RL', 'B1', 'B2', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6'
        ]
        for i in range(self.max_channels):
            cb = QCheckBox(default_labels[i] if i < len(default_labels) else f"Ch{i+1}")
            cb.setChecked(True)
            row = (i // 6)
            col = i % 6
            ch_layout.addWidget(cb, row, col)
            self.channel_checkboxes.append(cb)

        # Plot area within a scroll area (always scrollable)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        main_layout.addWidget(self.scroll_area)

        self.plots_container = QWidget()
        self.scroll_area.setWidget(self.plots_container)
        self.plots_layout = QVBoxLayout(self.plots_container)
        self.plots_layout.setContentsMargins(0, 0, 0, 0)
        self.plots_layout.setSpacing(4)

        self.plot_widgets = []
        self.plot_lines = []
        channel_colors = [
            (255, 0, 0), (0, 0, 255), (0, 128, 0), (128, 0, 128),
            (255, 165, 0), (0, 128, 128), (128, 0, 0), (0, 0, 128),
            (128, 128, 0), (255, 0, 255), (0, 0, 0), (64, 64, 64)
        ]

        for i in range(self.max_channels):
            pw = pg.PlotWidget()
            pw.setBackground('w')
            pw.showGrid(x=True, y=True, alpha=0.3)
            pw.setLabel('left', default_labels[i] if i < len(default_labels) else f"Ch{i+1}")
            pw.getAxis('bottom').setStyle(showValues=True)
            pen = pg.mkPen(color=channel_colors[i], width=2)
            line = pw.plot(pen=pen)
            self.plots_layout.addWidget(pw)
            self.plot_widgets.append(pw)
            self.plot_lines.append(line)

        # Link X axes
        for i in range(1, self.max_channels):
            self.plot_widgets[i].setXLink(self.plot_widgets[0])

        # Footer info
        footer = QHBoxLayout()
        main_layout.addLayout(footer)
        self.status_label = QLabel("")
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        footer.addWidget(self.status_label)

        # Initial state
        self._update_channel_visibility()
        self._update_status()

    def _connect_signals(self):
        self.open_btn.clicked.connect(self._open_file)
        self.freq_spin.valueChanged.connect(self._on_freq_changed)
        self.window_spin.valueChanged.connect(self._on_window_changed)
        self.pos_slider.valueChanged.connect(self._on_position_changed)
        self.select_all_btn.clicked.connect(self._select_all_channels)
        self.deselect_all_btn.clicked.connect(self._deselect_all_channels)
        for idx, cb in enumerate(self.channel_checkboxes):
            cb.stateChanged.connect(self._on_channel_toggled)

    # --- File handling ---
    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open BIN file", os.getcwd(), "BIN Files (*.bin)")
        if not path:
            return
        try:
            file_size = os.path.getsize(path)
            if file_size % 24 != 0:  # 12 channels * 2 bytes
                self.status_label.setText(f"Invalid file size ({file_size} bytes). Must be multiple of 24.")
                return

            with open(path, 'rb') as f:
                raw = np.frombuffer(f.read(), dtype='<u2')  # little-endian uint16
            num_samples = raw.size // 12
            data = raw.reshape((num_samples, 12))

            self.file_path = path
            self.data_adc = data
            self._rebuild_time_axis()

            # Reset navigation
            self.position_index = 0
            self._update_slider_range()
            self._update_plots()

            self.file_label.setText(os.path.basename(path))
            self._update_status()
        except Exception as e:
            self.status_label.setText(f"Error reading file: {e}")

    # --- Controls handlers ---
    def _on_freq_changed(self, value: int):
        self.sample_rate = int(value)
        self._rebuild_time_axis()
        self._update_plots()
        self._update_status()

    def _on_window_changed(self, value: int):
        self.window_size = int(value)
        self._update_slider_range()
        self._update_plots()
        self._update_status()

    def _on_position_changed(self, value: int):
        self.position_index = int(value)
        self._update_plots()

    def _select_all_channels(self):
        for cb in self.channel_checkboxes:
            cb.setChecked(True)
        self._update_channel_visibility()
        self._update_plots()

    def _deselect_all_channels(self):
        for cb in self.channel_checkboxes:
            cb.setChecked(False)
        self._update_channel_visibility()
        self._update_plots()

    def _on_channel_toggled(self, state):
        self._update_channel_visibility()
        self._update_plots()

    # --- Helpers ---
    def _rebuild_time_axis(self):
        if self.data_adc is None:
            self.time_axis = None
            return
        n = self.data_adc.shape[0]
        # Use relative time (seconds)
        if self.sample_rate <= 0:
            self.sample_rate = 1
        self.time_axis = np.arange(n) / float(self.sample_rate)

    def _update_slider_range(self):
        if self.data_adc is None:
            self.pos_slider.setRange(0, 0)
            self.pos_slider.setValue(0)
            return
        n = self.data_adc.shape[0]
        if n <= self.window_size:
            self.pos_slider.setRange(0, 0)
            self.position_index = 0
            self.pos_slider.setValue(0)
        else:
            self.pos_slider.setRange(0, n - self.window_size)
            self.pos_slider.setValue(min(self.position_index, n - self.window_size))

    def _update_channel_visibility(self):
        for i, cb in enumerate(self.channel_checkboxes):
            self.show_channel[i] = cb.isChecked()
            self.plot_widgets[i].setVisible(self.show_channel[i])

    def _update_status(self):
        if self.data_adc is None:
            self.status_label.setText("")
            return
        n = self.data_adc.shape[0]
        dur = n / float(self.sample_rate) if self.sample_rate > 0 else 0
        vis = sum(self.show_channel)
        self.status_label.setText(
            f"Samples: {n:,} | Freq: {self.sample_rate} Hz | Duration: {dur:.2f}s | Window: {self.window_size} | Visible: {vis}/12"
        )

    def _update_plots(self):
        if self.data_adc is None or self.time_axis is None:
            return

        n = self.data_adc.shape[0]
        if self.window_size >= n:
            start = 0
            end = n
        else:
            start = min(self.position_index, max(0, n - self.window_size))
            end = start + self.window_size

        t = self.time_axis[start:end]
        for i in range(self.max_channels):
            if not self.show_channel[i]:
                continue
            y = self.data_adc[start:end, i]
            self.plot_lines[i].setData(t, y)
            # Default ADC range
            try:
                if y.size > 0:
                    ymin = max(0, np.min(y))
                    ymax = max(1, np.max(y))
                    pad = max(1, int((ymax - ymin) * 0.05))
                    self.plot_widgets[i].setYRange(ymin - pad, ymax + pad)
            except Exception:
                # Fallback fixed range
                self.plot_widgets[i].setYRange(0, 4095)


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = BinReaderApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()


