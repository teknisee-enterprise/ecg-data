"""
CSV Export Utilities
"""
import csv
import os
import numpy as np
from datetime import datetime


class CSVExporter:
    """CSV export utilities for ECG data"""
    
    def __init__(self):
        self.y_axis_modes = [
            "Asli (mV)",
            "Hasil (12bit)", 
            "Tegangan Hasil (V)"
        ]
    
    def get_unit_suffix(self, y_mode):
        """Get unit suffix based on Y-axis mode"""
        if y_mode == 0:  # Asli (mV)
            return "mV"
        elif y_mode == 1:  # Hasil (12bit)
            return "12bit"
        else:  # Tegangan Hasil (V)
            return "V"
    
    def export_to_csv(self, active_data, active_names, relative_time, 
                     output_path, record_name, mode, y_mode, trim_start, trim_end):
        """Export trimmed ECG data to CSV format"""
        try:
            # Create filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            mode_suffix = "10lead" if mode == "10-lead" else "12lead"
            unit_suffix = self.get_unit_suffix(y_mode)
            
            csv_filename = f"{record_name}_{mode_suffix}_{unit_suffix}_{timestamp}.csv"
            csv_path = os.path.join(output_path, csv_filename)
            
            # Prepare headers
            unit_suffix_header = f"({unit_suffix})"
            headers = ["Time(s)"] + [f"{name}{unit_suffix_header}" for name in active_names]
            
            # Write CSV file
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(headers)
                
                # Write data rows
                for i in range(len(relative_time)):
                    row = [f"{relative_time[i]:.4f}"]  # Time with 4 decimal precision
                    
                    # Add channel data
                    for j in range(len(active_names)):
                        if y_mode == 0:  # mV - 4 decimal precision
                            row.append(f"{active_data[i, j]:.4f}")
                        elif y_mode == 1:  # 12bit - integer
                            row.append(f"{int(active_data[i, j])}")
                        else:  # Voltage - 6 decimal precision
                            row.append(f"{active_data[i, j]:.6f}")
                    
                    writer.writerow(row)
            
            # Calculate file statistics
            file_size = os.path.getsize(csv_path)
            
            return {
                'success': True,
                'filename': csv_filename,
                'file_size': file_size,
                'samples': len(active_data),
                'channels': len(active_names),
                'duration': trim_end - trim_start,
                'mode': mode,
                'y_mode': self.y_axis_modes[y_mode],
                'unit_suffix': unit_suffix
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_export_info(self, result, record_name, trim_start, trim_end):
        """Generate export information text"""
        if not result['success']:
            return f"CSV Export failed: {result['error']}"
        
        export_info = f"--- CSV Export Results ---\n"
        export_info += f"Output file: {result['filename']}\n"
        export_info += f"Mode: {result['mode']}\n"
        export_info += f"Y-axis mode: {result['y_mode']}\n"
        export_info += f"Source record: {record_name}\n"
        export_info += f"Trimmed duration: {trim_start:.2f}s - {trim_end:.2f}s\n"
        export_info += f"Total duration: {result['duration']:.2f}s\n"
        export_info += f"Samples exported: {result['samples']:,}\n"
        export_info += f"Active channels: {result['channels']}\n"
        export_info += f"File size: {result['file_size']:,} bytes\n"
        export_info += f"Status: Success\n"
        
        return export_info 