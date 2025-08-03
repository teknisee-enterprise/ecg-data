import wfdb
import numpy as np
import os
from typing import Dict, List, Tuple, Optional
from enum import Enum

class DataMode(Enum):
    """Data display modes"""
    RAW = "raw"
    PROCESSED = "processed"

class ECGDataLoader:
    """Data loader for sampleRaw ECG files"""
    
    def __init__(self, sample_folder: str = "sampleRaw"):
        self.sample_folder = sample_folder
        self.available_records = []
        self.current_record = None
        self.current_data = None
        self.current_mode = DataMode.PROCESSED
        
        # Channel configurations
        self.raw_channels = [
            'I-Raw', 'II-Raw', 'III-Raw', 'V1-Raw', 'V2-Raw', 'V3-Raw',
            'V4-Raw', 'V5-Raw', 'V6-Raw', 'LA-Raw', 'RA-Raw', 'LL-Raw'
        ]
        
        self.processed_channels = [
            'I', 'II', 'III', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'LA', 'RA', 'LL'
        ]
        
        # Load available records
        self.load_available_records()
    
    def load_available_records(self) -> List[str]:
        """Load available records from sampleRaw folder"""
        try:
            if not os.path.exists(self.sample_folder):
                os.makedirs(self.sample_folder)
                return []
            
            records = []
            for file in os.listdir(self.sample_folder):
                if file.endswith('.hea'):
                    record_name = file[:-4]
                    records.append(record_name)
            
            self.available_records = sorted(records)
            return self.available_records
            
        except Exception as e:
            print(f"Error loading records: {str(e)}")
            return []
    
    def load_record(self, record_name: str) -> bool:
        """Load selected record"""
        if not record_name or record_name not in self.available_records:
            return False
            
        try:
            # Load record using wfdb
            record_path = os.path.join(self.sample_folder, record_name)
            record = wfdb.rdrecord(record_path)
            
            self.current_record = record
            self.current_data = record.p_signal
            self.sample_rate = record.fs
            
            return True
            
        except Exception as e:
            print(f"Error loading record {record_name}: {str(e)}")
            return False
    
    def get_channel_names(self, mode: DataMode) -> List[str]:
        """Get channel names based on mode"""
        if mode == DataMode.RAW:
            return self.raw_channels
        else:
            return self.processed_channels
    
    def get_channel_data(self, mode: DataMode) -> Optional[np.ndarray]:
        """Get channel data based on mode"""
        if self.current_data is None:
            return None
        
        if mode == DataMode.RAW:
            return self._extract_raw_channels()
        else:
            return self._extract_processed_channels()
    
    def _extract_raw_channels(self) -> np.ndarray:
        """Extract raw channel data (excluding unipolar channels)"""
        if self.current_record is None:
            return np.array([])
        
        # Get available channel names
        available_channels = self.current_record.sig_name
        
        # Create 12-channel array for raw data
        raw_data = np.zeros((len(self.current_data), 12))
        
        # Map raw channels (excluding unipolar)
        for i, ch_name in enumerate(available_channels):
            ch_normalized = ch_name.strip()
            
            # Skip unipolar channels (those with 'U' prefix)
            if ch_normalized.startswith('U'):
                continue
            
            # Map to raw channel positions
            for j, raw_ch in enumerate(self.raw_channels):
                if ch_normalized == raw_ch:
                    raw_data[:, j] = self.current_data[:, i]
                    break
        
        return raw_data
    
    def _extract_processed_channels(self) -> np.ndarray:
        """Extract processed channel data (excluding unipolar channels)"""
        if self.current_record is None:
            return np.array([])
        
        # Get available channel names
        available_channels = self.current_record.sig_name
        
        # Create 12-channel array for processed data
        processed_data = np.zeros((len(self.current_data), 12))
        
        # Map processed channels (excluding unipolar)
        for i, ch_name in enumerate(available_channels):
            ch_normalized = ch_name.strip()
            
            # Skip unipolar channels (those with 'U' prefix)
            if ch_normalized.startswith('U'):
                continue
            
            # Map to processed channel positions
            for j, proc_ch in enumerate(self.processed_channels):
                if ch_normalized == proc_ch:
                    processed_data[:, j] = self.current_data[:, i]
                    break
        
        return processed_data
    
    def get_record_info(self) -> Dict:
        """Get current record information"""
        if self.current_record is None:
            return {}
        
        return {
            'name': self.current_record.record_name,
            'sample_rate': self.sample_rate,
            'duration': len(self.current_data) / self.sample_rate,
            'total_samples': len(self.current_data),
            'channels': len(self.current_record.sig_name),
            'available_channels': self.current_record.sig_name
        }
    
    def get_time_array(self) -> np.ndarray:
        """Get time array for current data"""
        if self.current_data is None:
            return np.array([])
        
        return np.arange(len(self.current_data)) / self.sample_rate
    
    def set_mode(self, mode: DataMode):
        """Set current data mode"""
        self.current_mode = mode
    
    def get_current_mode(self) -> DataMode:
        """Get current data mode"""
        return self.current_mode
    
    def get_available_records(self) -> List[str]:
        """Get list of available records"""
        return self.available_records.copy() 