import numpy as np
import struct
import csv
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from enum import Enum

class YAxisMode(Enum):
    """Y-axis display modes"""
    ORIGINAL_MV = 0
    ADC_12BIT = 1
    VOLTAGE = 2

class ECGSignalProcessor:
    """Signal processor for ECG data conversion"""
    
    def __init__(self):
        # ESP32 Configuration
        self.adc_resolution = 4095  # 12-bit ADC (0-4095)
        self.vcc = 3.3  # ESP32 VCC voltage
        self.gain = 1000  # Signal gain (default)
        self.offset_voltage = 1.65  # Offset voltage (VCC/2)
        self.offset_adc = 2048  # Offset in ADC counts (4095/2)
        
        # Processing parameters
        self.trim_start = 0.0
        self.trim_end = 0.0
        self.sample_rate = 800  # Default sample rate
        
        # Warning tracking
        self.clipping_warnings = []
        self.conversion_errors = {}
    
    def set_gain(self, gain: int):
        """Set gain value"""
        self.gain = gain
    
    def set_trim_range(self, start: float, end: float):
        """Set trim range in seconds"""
        self.trim_start = start
        self.trim_end = end
    
    def set_sample_rate(self, sample_rate: int):
        """Set sample rate"""
        self.sample_rate = sample_rate
    
    def trim_signal(self, signal: np.ndarray, time_array: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Trim signal based on time range"""
        if signal is None or len(signal) == 0:
            return np.array([]), np.array([])
        
        # Calculate sample indices
        start_idx = int(self.trim_start * self.sample_rate)
        end_idx = int(self.trim_end * self.sample_rate)
        
        # Ensure valid range
        start_idx = max(0, min(start_idx, len(signal) - 1))
        end_idx = max(start_idx + 1, min(end_idx, len(signal)))
        
        # Trim signal and time
        trimmed_signal = signal[start_idx:end_idx]
        trimmed_time = time_array[start_idx:end_idx]
        
        return trimmed_signal, trimmed_time
    
    def convert_mv_to_adc(self, signal_mv: np.ndarray, apply_clipping: bool = True) -> np.ndarray:
        """Convert mV signal to ESP32 ADC values"""
        # Apply gain (gain value)
        signal_gained = signal_mv * self.gain / 1000.0  # Convert mV to V and apply gain
        
        # Add offset (1.65V)
        signal_offset = signal_gained + self.offset_voltage
        
        # Convert to ADC counts
        adc_values = signal_offset * self.adc_resolution / self.vcc
        
        # Apply clipping only if requested
        if apply_clipping:
            # Check for clipping and track warnings
            clipped_low = np.sum(adc_values < 0)
            clipped_high = np.sum(adc_values > self.adc_resolution)
            
            if clipped_low > 0 or clipped_high > 0:
                warning = f"Clipping detected: {clipped_low} samples < 0, {clipped_high} samples > {self.adc_resolution}"
                if warning not in self.clipping_warnings:
                    self.clipping_warnings.append(warning)
            
            # Clip values to valid range
            adc_values = np.clip(adc_values, 0, self.adc_resolution)
        
        return adc_values
    
    def convert_adc_to_voltage(self, adc_values: np.ndarray) -> np.ndarray:
        """Convert ADC values back to voltage"""
        return adc_values * self.vcc / self.adc_resolution
    
    def get_display_data(self, signal_mv: np.ndarray, y_mode: YAxisMode) -> np.ndarray:
        """Get data for display based on Y-axis mode"""
        if y_mode == YAxisMode.ORIGINAL_MV:
            return signal_mv
        elif y_mode == YAxisMode.ADC_12BIT:
            # For display, don't apply clipping - show actual calculated values
            return self.convert_mv_to_adc(signal_mv, apply_clipping=False)
        else:  # VOLTAGE
            adc_values = self.convert_mv_to_adc(signal_mv, apply_clipping=False)
            return self.convert_adc_to_voltage(adc_values)
    
    def check_gain_warnings(self, signal_mv: np.ndarray) -> Dict:
        """Check if current gain will cause signal clipping"""
        if signal_mv is None or len(signal_mv) == 0:
            return {'warning': False, 'message': ''}
        
        # Check if there's any actual signal data (non-zero)
        has_data = np.any(signal_mv != 0)
        if not has_data:
            return {'warning': False, 'message': ''}
        
        # Find min/max of actual signal data
        non_zero_data = signal_mv[signal_mv != 0]
        if len(non_zero_data) == 0:
            return {'warning': False, 'message': ''}
            
        min_signal = np.min(non_zero_data)
        max_signal = np.max(non_zero_data)
        
        # Apply gain and calculate voltage range
        min_voltage_after_gain = (min_signal * self.gain / 1000.0) + self.offset_voltage
        max_voltage_after_gain = (max_signal * self.gain / 1000.0) + self.offset_voltage
        
        # Check if signal will exceed ESP32 limits
        voltage_overflow = max_voltage_after_gain > self.vcc or min_voltage_after_gain < 0
        
        if voltage_overflow:
            warning_text = f"⚠️ WARNING! Range: {min_voltage_after_gain:.2f}V to {max_voltage_after_gain:.2f}V "
            warning_text += f"(Should be: 0V to {self.vcc}V)"
            
            return {
                'warning': True,
                'message': warning_text,
                'min_voltage': min_voltage_after_gain,
                'max_voltage': max_voltage_after_gain
            }
        else:
            return {'warning': False, 'message': ''}
    
    def convert_to_binary(self, signal_data: np.ndarray, record_name: str, mode: str) -> Dict:
        """Convert ECG data to binary format with ESP32 compatibility"""
        if signal_data is None or len(signal_data) == 0:
            return {'success': False, 'error': 'No data available'}
        
        try:
            # Clear previous warnings
            self.clipping_warnings = []
            
            # Convert to ESP32 ADC values
            adc_signal = np.zeros((len(signal_data), 12), dtype=np.uint16)
            
            # Convert each channel to ESP32 ADC values
            for i in range(12):
                if np.any(signal_data[:, i] != 0):  # Only process non-empty channels
                    adc_signal[:, i] = self.convert_mv_to_adc(signal_data[:, i], apply_clipping=True).astype(np.uint16)
            
            # Create output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{record_name}_{mode}_{timestamp}.bin"
            
            # Write binary file
            with open(f"hasil/{output_filename}", 'wb') as f:
                for sample_idx in range(len(adc_signal)):
                    for channel_idx in range(12):
                        value = adc_signal[sample_idx, channel_idx]
                        f.write(struct.pack('<H', value))
            
            # Calculate statistics
            file_size = len(adc_signal) * 12 * 2  # 12 channels * 2 bytes
            min_adc = np.min(adc_signal[adc_signal > 0]) if np.any(adc_signal > 0) else 0
            max_adc = np.max(adc_signal)
            min_voltage = self.convert_adc_to_voltage(min_adc)
            max_voltage = self.convert_adc_to_voltage(max_adc)
            
            return {
                'success': True,
                'filename': output_filename,
                'file_size': file_size,
                'samples': len(adc_signal),
                'min_adc': min_adc,
                'max_adc': max_adc,
                'min_voltage': min_voltage,
                'max_voltage': max_voltage,
                'warnings': self.clipping_warnings.copy()
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_to_csv(self, signal_data: np.ndarray, time_array: np.ndarray, 
                     channel_names: List[str], record_name: str, mode: str, 
                     y_mode: YAxisMode) -> Dict:
        """Export ECG data to CSV format"""
        if signal_data is None or len(signal_data) == 0:
            return {'success': False, 'error': 'No data available'}
        
        try:
            # Get unit suffix based on Y-axis mode
            if y_mode == YAxisMode.ORIGINAL_MV:
                unit_suffix = "mV"
            elif y_mode == YAxisMode.ADC_12BIT:
                unit_suffix = "12bit"
            else:
                unit_suffix = "V"
            
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"{record_name}_{mode}_{unit_suffix}_{timestamp}.csv"
            
            # Prepare headers
            unit_suffix_header = f"({unit_suffix})"
            headers = ["Time(s)"] + [f"{name}{unit_suffix_header}" for name in channel_names]
            
            # Convert data based on Y-axis mode
            display_data = np.zeros_like(signal_data)
            for i in range(signal_data.shape[1]):
                display_data[:, i] = self.get_display_data(signal_data[:, i], y_mode)
            
            # Write CSV file
            with open(f"hasilcsv/{csv_filename}", 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(headers)
                
                # Write data rows
                for i in range(len(time_array)):
                    row = [f"{time_array[i]:.4f}"]  # Time with 4 decimal precision
                    
                    # Add channel data
                    for j in range(len(channel_names)):
                        if y_mode == YAxisMode.ORIGINAL_MV:  # mV - 4 decimal precision
                            row.append(f"{display_data[i, j]:.4f}")
                        elif y_mode == YAxisMode.ADC_12BIT:  # 12bit - integer
                            row.append(f"{int(display_data[i, j])}")
                        else:  # Voltage - 6 decimal precision
                            row.append(f"{display_data[i, j]:.6f}")
                    
                    writer.writerow(row)
            
            # Calculate file statistics
            file_size = len(time_array) * (len(channel_names) + 1) * 20  # Approximate size
            
            return {
                'success': True,
                'filename': csv_filename,
                'file_size': file_size,
                'samples': len(time_array),
                'channels': len(channel_names),
                'unit': unit_suffix
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_esp32_config(self) -> Dict:
        """Get ESP32 configuration"""
        return {
            'adc_resolution': self.adc_resolution,
            'vcc': self.vcc,
            'offset_voltage': self.offset_voltage,
            'offset_adc': self.offset_adc,
            'gain': self.gain
        } 