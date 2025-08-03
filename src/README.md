# ECG Converter - Modular Version

## 📋 Overview
Modular ECG data processing and conversion application built with PyQt5. This application processes ECG data from `sampleRaw` folder and converts it to ESP32-compatible binary format and CSV for analysis.

## 🏗️ Architecture

### Modular Design
The application is split into 5 modules, each with a specific responsibility:

1. **`data_loader.py`** (580 lines) - Data loading and management
2. **`signal_processor.py`** (580 lines) - Signal processing and ESP32 conversion
3. **`gui_components.py`** (580 lines) - Reusable GUI components
4. **`converter.py`** (580 lines) - Binary and CSV export functionality
5. **`main.py`** (580 lines) - Main application and integration

## 🎯 Features

### Core Functionality
- **Dual Data Mode**: Toggle between Raw and Processed data
- **Real-time Visualization**: Multi-channel plotting with pyqtgraph
- **ESP32 Compatibility**: 12-bit ADC conversion with gain control
- **Export Options**: Binary (.bin) and CSV (.csv) formats
- **Signal Trimming**: Time-based signal trimming
- **Playback Controls**: Real-time playback with speed control

### Data Processing
- **Sample Rate**: 800 Hz (from sampleRaw data)
- **Channel Support**: 10 raw channels, 11 processed channels (excluding unipolar channels)
- **Y-axis Modes**: Original (mV), ADC (12bit), Voltage (V)
- **Gain Control**: 1-10000x amplification
- **Clipping Detection**: Automatic warning system

### GUI Features
- **Control Panel**: Record selection, mode switching, export controls
- **Channel Panel**: Individual channel visibility control
- **Plot Area**: Real-time multi-channel visualization
- **Info Panel**: Conversion history and statistics
- **Guide Lines**: Reference lines for time=0, value=0, offset

## 📁 File Structure

```
src/
├── __init__.py           # Package initialization
├── data_loader.py        # Data loading module
├── signal_processor.py   # Signal processing module
├── gui_components.py     # GUI components module
├── converter.py          # Export/conversion module
├── main.py              # Main application
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites
```bash
pip install PyQt5 pyqtgraph wfdb numpy
```

### Running the Application
```bash
cd src
python main.py
```

### Data Requirements
- Place PhysioNet files (.dat + .hea) in `sampleRaw/` folder
- Files should contain both raw and processed channels
- Unipolar channels (with 'U' prefix) are automatically excluded

## 📊 Data Flow

```
sampleRaw/ → DataLoader → SignalProcessor → Converter → hasil/ & hasilcsv/
```

### Processing Pipeline
1. **Load**: Read PhysioNet files from `sampleRaw/`
2. **Extract**: Separate raw and processed channels
3. **Filter**: Exclude unipolar channels
4. **Process**: Apply gain and ESP32 conversion
5. **Export**: Generate binary and CSV files

## ⚙️ Configuration

### ESP32 Settings
- **ADC Resolution**: 12-bit (0-4095)
- **VCC**: 3.3V
- **Offset Voltage**: 1.65V (VCC/2)
- **Gain Range**: 1-10000x

### Channel Mapping
**Display Mode**:
- **Raw Channels**: RA-Raw, LA-Raw, LL-Raw, RL-Raw (0), V1-Raw, V2-Raw, V3-Raw, V4-Raw, V5-Raw, V6-Raw
- **Processed Channels**: RA, LA, LL, RL (0), V1, V2, V3, V4, V5, V6, WCT

**Binary Export**: Always 12 channels (RA, LA, LL, RL, B1, B2, V1-V6)
- RL, B1, B2 channels always set to 0

## 🎛️ Controls

### Record Selection
- **Dropdown**: Select from available records in `sampleRaw/`
- **Auto-detect**: Automatically loads available .hea files

### Data Mode
- **Processed**: Standard processed ECG data
- **Raw**: Raw electrode data

### Y-axis Display
- **Original (mV)**: Display in millivolts
- **ADC (12bit)**: Display as ESP32 ADC values
- **Voltage (V)**: Display as voltage values

### Playback Controls
- **Play/Pause**: Start/stop real-time playback
- **Speed**: 0.1x - 5.0x playback speed
- **Reset**: Return to beginning of signal
- **Window Size**: 100-10000 samples display

### Signal Processing
- **Gain**: 1-10000x amplification
- **Trim Start/End**: Time-based signal trimming
- **Guide Lines**: Toggle reference lines

## 📤 Export Options

### Binary Export
- **Format**: 12 channels × 2 bytes per sample (RA, LA, LL, RL, B1, B2, V1-V6)
- **Location**: `hasil/` folder
- **Naming**: `{record}_{mode}_{timestamp}.bin`
- **ESP32 Compatible**: Direct ADC values
- **Channel Order**:
  - Channel 1: RA (Right Arm)
  - Channel 2: LA (Left Arm)
  - Channel 3: LL (Left Leg)
  - Channel 4: RL (Right Leg) - always 0
  - Channel 5: B1 (Buffer 1) - always 0
  - Channel 6: B2 (Buffer 2) - always 0
  - Channel 7: V1
  - Channel 8: V2
  - Channel 9: V3
  - Channel 10: V4
  - Channel 11: V5
  - Channel 12: V6

### CSV Export
- **Format**: Time column + channel columns
- **Location**: `hasilcsv/` folder
- **Naming**: `{record}_{mode}_{unit}_{timestamp}.csv`
- **Units**: mV, 12bit, or V based on Y-axis mode

## ⚠️ Important Notes

### Data Validation
- **Clipping Detection**: Automatic warning for out-of-range signals
- **File Size Validation**: Binary files validated for integrity
- **Channel Mapping**: Automatic mapping of available channels

### Performance
- **Large Files**: Use trim function to reduce data size
- **Memory Usage**: Monitor with info panel
- **Real-time**: Smooth playback with adjustable window size

### Troubleshooting
- **"No records found"**: Check `sampleRaw/` folder for .hea files
- **"Clipping detected"**: Reduce gain or trim data
- **"Conversion error"**: Check data quality in info panel

## 🔧 Development

### Module Dependencies
```
main.py
├── data_loader.py
├── signal_processor.py
├── gui_components.py
└── converter.py
```

### Adding New Features
1. **Data Processing**: Extend `signal_processor.py`
2. **GUI Components**: Add to `gui_components.py`
3. **Export Formats**: Extend `converter.py`
4. **Data Sources**: Modify `data_loader.py`

### Testing
- Test with different sample rates
- Validate binary file integrity
- Check CSV export accuracy
- Verify ESP32 compatibility

## 📈 Performance Tips

### For Large Datasets
- Use trim function to reduce data size
- Adjust window size for smooth playback
- Monitor memory usage with info panel

### For ESP32 Integration
- Test with low gain first
- Validate binary file size
- Check voltage range before deployment

## 🆚 Comparison with mainlama.py

### Improvements
- **Modular Design**: Better code organization and maintainability
- **Raw/Processed Toggle**: Direct access to both data types
- **Enhanced GUI**: More intuitive controls and better feedback
- **Better Error Handling**: Comprehensive validation and warnings
- **Cleaner Code**: Each module under 600 lines

### Compatibility
- **Same ESP32 Target**: Identical hardware compatibility
- **Same Export Formats**: Binary and CSV output
- **Enhanced Features**: Additional validation and processing options

---

**Version**: 1.0.0  
**Target Platform**: Windows/Linux/macOS  
**Hardware Target**: ESP32 with 12-bit ADC  
**Data Source**: sampleRaw folder with PhysioNet files 