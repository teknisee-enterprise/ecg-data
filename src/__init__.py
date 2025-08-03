# ECG Converter Package
# Modular ECG data processing and conversion application

__version__ = "1.0.0"
__author__ = "ECG Converter Team"

from .data_loader import ECGDataLoader, DataMode
from .signal_processor import ECGSignalProcessor, YAxisMode
from .gui_components import ControlPanel, ChannelControlPanel, InfoPanel, PlotArea
from .converter import ECGConverter
from .main import ECGConverterApp, main

__all__ = [
    'ECGDataLoader',
    'DataMode', 
    'ECGSignalProcessor',
    'YAxisMode',
    'ControlPanel',
    'ChannelControlPanel',
    'InfoPanel',
    'PlotArea',
    'ECGConverter',
    'ECGConverterApp',
    'main'
] 