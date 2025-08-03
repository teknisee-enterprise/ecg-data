import os
import struct
import csv
from datetime import datetime
from typing import Dict, List, Optional
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

class ECGConverter:
    """Converter for ECG data to binary and CSV formats"""
    
    def __init__(self):
        # Create output folders if not exist
        self.output_folder = "hasil"
        self.csv_output_folder = "hasilcsv"
        
        for folder in [self.output_folder, self.csv_output_folder]:
            if not os.path.exists(folder):
                os.makedirs(folder)
    
    def convert_to_binary(self, signal_data: np.ndarray, record_name: str, 
                         mode: DataMode, processor) -> Dict:
        """Convert ECG data to binary format with ESP32 compatibility"""
        if signal_data is None or len(signal_data) == 0:
            return {'success': False, 'error': 'No data available'}
        
        try:
            # Clear previous warnings
            processor.clipping_warnings = []
            
            # Convert to ESP32 ADC values
            adc_signal = np.zeros((len(signal_data), 12), dtype=np.uint16)
            
            # Convert each channel to ESP32 ADC values
            for i in range(12):
                if np.any(signal_data[:, i] != 0):  # Only process non-empty channels
                    adc_signal[:, i] = processor.convert_mv_to_adc(signal_data[:, i], apply_clipping=True).astype(np.uint16)
            
            # Create output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode_str = mode.value
            output_filename = f"{record_name}_{mode_str}_{timestamp}.bin"
            output_path = os.path.join(self.output_folder, output_filename)
            
            # Write binary file
            with open(output_path, 'wb') as f:
                for sample_idx in range(len(adc_signal)):
                    for channel_idx in range(12):
                        value = adc_signal[sample_idx, channel_idx]
                        f.write(struct.pack('<H', value))
            
            # Calculate statistics
            file_size = os.path.getsize(output_path)
            expected_size = len(adc_signal) * 12 * 2  # 12 channels * 2 bytes
            
            min_adc = np.min(adc_signal[adc_signal > 0]) if np.any(adc_signal > 0) else 0
            max_adc = np.max(adc_signal)
            min_voltage = processor.convert_adc_to_voltage(min_adc)
            max_voltage = processor.convert_adc_to_voltage(max_adc)
            
            # Prepare conversion info
            conversion_info = f"--- ESP32 Conversion Results ---\n"
            conversion_info += f"Output file: {output_filename}\n"
            conversion_info += f"Mode: {mode_str}\n"
            conversion_info += f"Source record: {record_name}\n"
            conversion_info += f"File size: {file_size:,} bytes\n"
            conversion_info += f"Expected size: {expected_size:,} bytes\n"
            conversion_info += f"Samples converted: {len(adc_signal):,}\n"
            
            conversion_info += f"\nESP32 ADC Mapping:\n"
            conversion_info += f"- Gain applied: {processor.gain}x\n"
            conversion_info += f"- ADC range: {min_adc} - {max_adc} (0-{processor.adc_resolution})\n"
            conversion_info += f"- Voltage range: {min_voltage:.3f}V - {max_voltage:.3f}V (0-{processor.vcc}V)\n"
            conversion_info += f"- Zero level: {processor.offset_adc} ADC ({processor.offset_voltage}V)\n"
            
            # Add warnings
            if processor.clipping_warnings:
                conversion_info += f"\n⚠️ WARNINGS:\n"
                for warning in processor.clipping_warnings:
                    conversion_info += f"- {warning}\n"
            
            status = "Success" if file_size == expected_size else "Size mismatch"
            if processor.clipping_warnings:
                status += " (with warnings)"
            
            conversion_info += f"\nStatus: {status}\n"
            
            return {
                'success': True,
                'filename': output_filename,
                'file_size': file_size,
                'samples': len(adc_signal),
                'min_adc': min_adc,
                'max_adc': max_adc,
                'min_voltage': min_voltage,
                'max_voltage': max_voltage,
                'warnings': processor.clipping_warnings.copy(),
                'conversion_info': conversion_info,
                'status': status
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_to_csv(self, signal_data: np.ndarray, time_array: np.ndarray, 
                     channel_names: List[str], record_name: str, mode: DataMode, 
                     y_mode: YAxisMode, processor) -> Dict:
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
            mode_str = mode.value
            csv_filename = f"{record_name}_{mode_str}_{unit_suffix}_{timestamp}.csv"
            csv_path = os.path.join(self.csv_output_folder, csv_filename)
            
            # Prepare headers
            unit_suffix_header = f"({unit_suffix})"
            headers = ["Time(s)"] + [f"{name}{unit_suffix_header}" for name in channel_names]
            
            # Convert data based on Y-axis mode
            display_data = np.zeros_like(signal_data)
            for i in range(signal_data.shape[1]):
                display_data[:, i] = processor.get_display_data(signal_data[:, i], y_mode)
            
            # Write CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
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
            file_size = os.path.getsize(csv_path)
            
            # Prepare export info
            export_info = f"--- CSV Export Results ---\n"
            export_info += f"Output file: {csv_filename}\n"
            export_info += f"Mode: {mode_str}\n"
            export_info += f"Y-axis mode: {y_mode.name}\n"
            export_info += f"Source record: {record_name}\n"
            export_info += f"Samples exported: {len(signal_data):,}\n"
            export_info += f"Active channels: {len(channel_names)} ({', '.join(channel_names)})\n"
            export_info += f"File size: {file_size:,} bytes\n"
            export_info += f"Location: {self.csv_output_folder}\n"
            export_info += f"Status: Success\n"
            
            return {
                'success': True,
                'filename': csv_filename,
                'file_size': file_size,
                'samples': len(signal_data),
                'channels': len(channel_names),
                'unit': unit_suffix,
                'export_info': export_info
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_history_item(self, result: Dict, mode: DataMode, timestamp: str = None) -> Dict:
        """Create history item for tracking"""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return {
            'filename': result.get('filename', 'Unknown'),
            'timestamp': timestamp,
            'mode': mode.value,
            'status': result.get('status', 'Unknown'),
            'samples': result.get('samples', 0),
            'file_size': result.get('file_size', 0)
        }
    
    def validate_binary_file(self, filepath: str) -> Dict:
        """Validate binary file integrity"""
        try:
            if not os.path.exists(filepath):
                return {'valid': False, 'error': 'File not found'}
            
            file_size = os.path.getsize(filepath)
            
            # Check if file size is multiple of 24 (12 channels * 2 bytes)
            if file_size % 24 != 0:
                return {'valid': False, 'error': f'Invalid file size: {file_size} bytes'}
            
            # Read first few samples to validate format
            with open(filepath, 'rb') as f:
                # Read first 24 bytes (1 sample)
                data = f.read(24)
                if len(data) != 24:
                    return {'valid': False, 'error': 'Incomplete data'}
                
                # Try to unpack as 12 uint16 values
                try:
                    values = struct.unpack('<12H', data)
                    # Check if values are in valid ADC range (0-4095)
                    for value in values:
                        if value > 4095:
                            return {'valid': False, 'error': f'Invalid ADC value: {value}'}
                except struct.error:
                    return {'valid': False, 'error': 'Invalid binary format'}
            
            samples = file_size // 24
            return {
                'valid': True,
                'file_size': file_size,
                'samples': samples,
                'channels': 12
            }
            
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def get_file_statistics(self, filepath: str) -> Dict:
        """Get statistics for a file"""
        try:
            if not os.path.exists(filepath):
                return {'error': 'File not found'}
            
            file_size = os.path.getsize(filepath)
            file_name = os.path.basename(filepath)
            file_ext = os.path.splitext(file_name)[1]
            
            stats = {
                'filename': file_name,
                'file_size': file_size,
                'file_type': file_ext,
                'created': datetime.fromtimestamp(os.path.getctime(filepath)).strftime('%Y-%m-%d %H:%M:%S'),
                'modified': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if file_ext == '.bin':
                # Binary file statistics
                validation = self.validate_binary_file(filepath)
                if validation['valid']:
                    stats.update(validation)
                else:
                    stats['error'] = validation['error']
            
            elif file_ext == '.csv':
                # CSV file statistics
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        stats['lines'] = len(lines)
                        if len(lines) > 1:  # Has header
                            stats['data_rows'] = len(lines) - 1
                        else:
                            stats['data_rows'] = 0
                except Exception as e:
                    stats['error'] = f'Error reading CSV: {str(e)}'
            
            return stats
            
        except Exception as e:
            return {'error': str(e)}
    
    def cleanup_old_files(self, max_age_days: int = 30) -> Dict:
        """Clean up old files in output folders"""
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            deleted_files = []
            
            for folder in [self.output_folder, self.csv_output_folder]:
                if not os.path.exists(folder):
                    continue
                
                for filename in os.listdir(folder):
                    filepath = os.path.join(folder, filename)
                    if os.path.isfile(filepath):
                        file_time = os.path.getmtime(filepath)
                        if file_time < cutoff_time:
                            try:
                                os.remove(filepath)
                                deleted_files.append(filename)
                            except Exception as e:
                                print(f"Error deleting {filename}: {e}")
            
            return {
                'success': True,
                'deleted_files': deleted_files,
                'count': len(deleted_files)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)} 