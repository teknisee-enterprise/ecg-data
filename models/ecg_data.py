"""
ECG Data Models and Enums
"""
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from collections import deque
import numpy as np


class ECGMode(Enum):
    """ECG display modes"""
    TWELVE_LEAD = "12-lead"
    TEN_LEAD = "10-lead"


@dataclass
class ConversionHistoryItem:
    """Store conversion history data"""
    filename: str
    timestamp: str
    duration: float
    samples: int
    file_size: int
    status: str
    mode: str


class ECGData:
    """ECG data container with processing capabilities"""
    
    def __init__(self):
        # Channel configurations
        self.CHANNELS_12LEAD = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 
                               'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
        self.CHANNELS_10LEAD = ['RA', 'LA', 'LL', 'RL', 
                               'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
        
        # Data storage
        self.record_name = None
        self.record = None
        self.signal = None
        self.signal_trimmed = None
        self.time = None
        self.time_trimmed = None
        self.electrode_data = None
        
        # Trim parameters
        self.trim_start = 0.0
        self.trim_end = 0.0
        self.time_offset = 0.0
        
        # Sample rate
        self.sample_rate = 360
        
        # Conversion errors
        self.conversion_errors = {}
    
    def map_channels_to_standard(self):
        """Map available channels to standard 12-lead positions"""
        # Use trimmed signal if available
        signal_to_map = self.signal_trimmed if self.signal_trimmed is not None else self.signal
        
        # Create 12-channel array filled with zeros
        mapped_signal = np.zeros((len(signal_to_map), 12))
        
        if self.record is None or signal_to_map is None:
            return mapped_signal
        
        # Get available channel names
        available_channels = self.record.sig_name
        
        # Map each available channel to its standard position
        for i, ch_name in enumerate(available_channels):
            ch_normalized = ch_name.strip().upper()
            
            for j, std_ch in enumerate(self.CHANNELS_12LEAD):
                std_normalized = std_ch.upper()
                
                if (ch_normalized == std_normalized or 
                    ch_normalized == std_normalized.replace('A', '') or
                    (ch_normalized == 'MLII' and std_normalized == 'II') or
                    (ch_normalized == 'MLI' and std_normalized == 'I')):
                    
                    if len(signal_to_map.shape) > 1:
                        mapped_signal[:, j] = signal_to_map[:, i]
                    else:
                        mapped_signal[:, j] = signal_to_map[:]
                    break
        
        return mapped_signal
    
    def convert_to_10lead(self):
        """Convert 12-lead data to 10-lead raw electrodes"""
        if self.signal_trimmed is None:
            return None
        
        # Map channels to standard 12-lead positions
        mapped_signal = self.map_channels_to_standard()
        
        # Extract leads for conversion
        lead_I = mapped_signal[:, 0]
        lead_II = mapped_signal[:, 1]
        lead_III = mapped_signal[:, 2]
        
        # Calculate electrodes with RL = 0 and WCT = 0
        RA = -(lead_I + lead_II) / 3
        LA = (2 * lead_I - lead_II) / 3
        LL = (2 * lead_II - lead_I) / 3
        RL = np.zeros_like(RA)
        
        # Validate conversion
        lead_III_calc = LL - LA
        error = np.mean(np.abs(lead_III_calc - lead_III))
        
        if error > 0.05:  # 50 μV threshold
            self.conversion_errors['Lead III'] = error
        else:
            self.conversion_errors = {}
        
        # Create 10-lead electrode data
        self.electrode_data = np.zeros((len(mapped_signal), 10))
        self.electrode_data[:, 0] = RA
        self.electrode_data[:, 1] = LA
        self.electrode_data[:, 2] = LL
        self.electrode_data[:, 3] = RL
        self.electrode_data[:, 4:10] = mapped_signal[:, 6:12]  # V1-V6
        
        return error
    
    def update_trim(self, start_time, end_time):
        """Update signal trimming"""
        if self.signal is None:
            return
        
        # Ensure valid range
        if end_time <= start_time:
            end_time = start_time + 0.1
        
        # Calculate sample indices
        start_idx = int(start_time * self.sample_rate)
        end_idx = int(end_time * self.sample_rate)
        
        # Store time offset for x-axis display
        self.time_offset = start_time
        
        # Trim signal and time
        self.signal_trimmed = self.signal[start_idx:end_idx]
        self.time_trimmed = self.time[start_idx:end_idx]
        
        # Update trim parameters
        self.trim_start = start_time
        self.trim_end = end_time
        
        return len(self.signal_trimmed)
    
    def get_trimmed_samples_count(self):
        """Get number of trimmed samples"""
        return len(self.signal_trimmed) if self.signal_trimmed is not None else 0
    
    def get_total_duration(self):
        """Get total duration in seconds"""
        if self.signal is None:
            return 0
        return len(self.signal) / self.sample_rate 