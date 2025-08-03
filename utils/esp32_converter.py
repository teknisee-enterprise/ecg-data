"""
ESP32 Conversion Utilities
"""
import numpy as np
import struct
import os
from datetime import datetime


class ESP32Converter:
    """ESP32 ADC conversion utilities"""
    
    def __init__(self):
        # ESP32 ADC Configuration
        self.adc_resolution = 4095  # 12-bit ADC (0-4095)
        self.vcc = 3.3  # ESP32 VCC voltage
        self.gain = 1000  # Signal gain (default)
        self.offset_voltage = 1.65  # Offset voltage (VCC/2)
        self.offset_adc = 2048  # Offset in ADC counts (4095/2)
        
        # Warning tracking
        self.clipping_warnings = []
    
    def convert_mv_to_adc(self, signal_mv, apply_clipping=True):
        """Convert mV signal to ESP32 ADC values"""
        # Apply gain (gain value)
        signal_gained = signal_mv * self.gain / 1000.0  # Convert mV to V and apply gain
        
        # Add offset (1.65V)
        signal_offset = signal_gained + self.offset_voltage
        
        # Convert to ADC counts
        adc_values = signal_offset * self.adc_resolution / self.vcc
        
        # Apply clipping only if requested (for conversion, not for display)
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
    
    def convert_adc_to_voltage(self, adc_values):
        """Convert ADC values back to voltage"""
        return adc_values * self.vcc / self.adc_resolution
    
    def get_display_data(self, signal_mv, y_mode):
        """Get data for display based on Y-axis mode"""
        if y_mode == 0:  # Asli (mV)
            return signal_mv
        elif y_mode == 1:  # Hasil (12bit)
            # For display, don't apply clipping - show actual calculated values
            return self.convert_mv_to_adc(signal_mv, apply_clipping=False)
        else:  # Tegangan Hasil (V)
            adc_values = self.convert_mv_to_adc(signal_mv, apply_clipping=False)
            return self.convert_adc_to_voltage(adc_values)
    
    def check_gain_warnings(self, signal_data, vcc=3.3):
        """Check if current gain will cause signal clipping"""
        if signal_data is None:
            return False, "No data available"
        
        # Find min/max of actual signal data
        non_zero_data = signal_data[signal_data != 0]
        if len(non_zero_data) == 0:
            return False, "No signal data"
            
        min_signal = np.min(non_zero_data)
        max_signal = np.max(non_zero_data)
        
        # Apply gain and calculate voltage range
        min_voltage_after_gain = (min_signal * self.gain / 1000.0) + self.offset_voltage
        max_voltage_after_gain = (max_signal * self.gain / 1000.0) + self.offset_voltage
        
        # Check if signal will exceed ESP32 limits
        voltage_overflow = max_voltage_after_gain > vcc or min_voltage_after_gain < 0
        
        if voltage_overflow:
            warning_text = f"Range: {min_voltage_after_gain:.2f}V to {max_voltage_after_gain:.2f}V (Should be: 0V to {vcc}V)"
            return True, warning_text
        
        return False, ""
    
    def convert_to_binary(self, signal_data, output_path, mode="12lead"):
        """Convert ECG data to binary format with ESP32 compatibility"""
        try:
            # Clear previous warnings
            self.clipping_warnings = []
            
            # Convert to ADC values
            adc_signal = np.zeros((len(signal_data), 12), dtype=np.uint16)
            
            for i in range(12):
                if np.any(signal_data[:, i] != 0):  # Only process non-empty channels
                    adc_signal[:, i] = self.convert_mv_to_adc(signal_data[:, i], apply_clipping=True).astype(np.uint16)
            
            # Write binary file
            with open(output_path, 'wb') as f:
                for sample_idx in range(len(adc_signal)):
                    for channel_idx in range(12):
                        value = adc_signal[sample_idx, channel_idx]
                        f.write(struct.pack('<H', value))
            
            # Validate
            file_size = os.path.getsize(output_path)
            expected_size = len(adc_signal) * 12 * 2
            
            # Calculate statistics
            min_adc = np.min(adc_signal[adc_signal > 0]) if np.any(adc_signal > 0) else 0
            max_adc = np.max(adc_signal)
            min_voltage = self.convert_adc_to_voltage(min_adc)
            max_voltage = self.convert_adc_to_voltage(max_adc)
            
            return {
                'success': True,
                'file_size': file_size,
                'expected_size': expected_size,
                'samples': len(adc_signal),
                'min_adc': min_adc,
                'max_adc': max_adc,
                'min_voltage': min_voltage,
                'max_voltage': max_voltage,
                'warnings': self.clipping_warnings.copy(),
                'mode': mode
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'warnings': self.clipping_warnings.copy()
            }
    
    def set_gain(self, gain):
        """Set gain value"""
        self.gain = gain
    
    def get_gain(self):
        """Get current gain value"""
        return self.gain
    
    def clear_warnings(self):
        """Clear clipping warnings"""
        self.clipping_warnings = [] 