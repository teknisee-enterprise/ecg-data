# Quick Review: mainlama.py - ECG PhysioNet to Binary Converter

## 📋 Overview
`mainlama.py` adalah aplikasi GUI untuk mengkonversi data ECG dari format PhysioNet ke format binary yang kompatibel dengan ESP32. Aplikasi mendukung mode 12-lead dan 10-lead ECG dengan visualisasi real-time.

## 🎯 Purpose
- **Input**: File PhysioNet (.dat + .hea) dari folder `sample/`
- **Output**: File binary untuk ESP32 + CSV untuk analisis
- **Target**: Sistem monitoring ECG berbasis ESP32

## ⚙️ Key Features

### 1. **Dual Mode Support**
- **12-Lead Mode**: Standard ECG (I, II, III, aVR, aVL, aVF, V1-V6)
- **10-Lead Mode**: Raw electrodes (RA, LA, LL, RL, V1-V6) untuk ESP32

### 2. **Real-time Visualization**
- Multi-channel plotting dengan pyqtgraph
- Playback controls dengan speed adjustment
- Channel visibility toggle
- Window size control (100-10000 samples)

### 3. **ESP32 Compatibility**
- **ADC**: 12-bit (0-4095)
- **VCC**: 3.3V
- **Gain**: 1-10000x (adjustable)
- **Offset**: 1.65V (VCC/2)
- **Clipping Detection**: Auto-warning jika out of range

### 4. **Data Processing**
- Signal trimming (start/end time)
- Gain application
- 10-lead conversion algorithm
- Data validation & error detection

## 📊 Display Modes

### Y-Axis Options:
1. **"Asli (mV)"** - Original millivolt values
2. **"Hasil (12bit)"** - ESP32 ADC values (0-4095)
3. **"Tegangan Hasil (V)"** - Voltage values (0-3.3V)

### Guide Lines:
- **Time = 0**: Solid black line
- **Value = 0**: Solid black line  
- **Offset**: Dashed line (2048 ADC / 1.65V)

## 🔧 Technical Specifications

### Hardware Target (ESP32):
```
ADC Resolution: 12-bit (0-4095)
VCC: 3.3V
Offset Voltage: 1.65V
Gain Range: 1-10000x
Sample Rate: Configurable (typically 360Hz)
```

### Data Flow:
```
PhysioNet (.dat/.hea) → Load → Trim → Apply Gain → Convert → Binary/CSV
```

### File Structure:
```
ecgdata/
├── sample/          # Input PhysioNet files
├── hasil/           # Binary output files
├── hasilcsv/        # CSV output files
└── mainlama.py      # Main application
```

## 🚀 Quick Start Guide

### 1. **Setup**
```bash
# Install dependencies
pip install PyQt5 pyqtgraph wfdb numpy

# Run application
python mainlama.py
```

### 2. **Basic Workflow**
1. **Load Record**: Pilih file dari dropdown (auto-detect dari `sample/`)
2. **Select Mode**: 12-lead atau 10-lead
3. **Configure**: Set gain, window size, trim range
4. **Visualize**: Play/pause, adjust speed, toggle channels
5. **Convert**: Export ke binary atau CSV

### 3. **Key Controls**
- **Play/Pause**: Real-time playback
- **Speed Slider**: 0.1x - 5.0x playback speed
- **Window Size**: 100-10000 samples display
- **Gain Control**: 1-10000x amplification
- **Trim Controls**: Start/end time selection

## 📁 File Formats

### Input (PhysioNet):
```
sample/
├── 00001_lr.hea    # Header file (metadata)
├── 00001_lr.dat    # Data file (12-lead, 100Hz)
├── 100.hea         # Header file (2-lead)
├── 100.dat         # Data file (MLII, V5, 360Hz)
├── I01.hea         # Header file (12-lead)
└── I01.dat         # Data file (257Hz)
```

### Output:
```
hasil/
└── [record]_[mode]_[timestamp].bin    # ESP32 binary

hasilcsv/
└── [record]_[mode]_[unit]_[timestamp].csv    # CSV data
```

## ⚠️ Important Notes

### 1. **Clipping Warnings**
- Aplikasi mendeteksi jika sinyal melebihi range ESP32 (0-3.3V)
- Conversion disabled jika clipping terdeteksi
- Warning ditampilkan di status bar dan info panel

### 2. **10-lead Conversion**
- Menggunakan algoritma: RA = -(I+II)/3, LA = (2I-II)/3, LL = (2II-I)/3
- Validation error jika Lead III tidak match
- RL = 0 (ground reference)

### 3. **Data Validation**
- File size validation
- Channel mapping verification
- Empty channel detection
- Conversion error tracking

## 🔍 Troubleshooting

### Common Issues:
1. **"No records found"**: Pastikan ada file `.hea` di folder `sample/`
2. **"Clipping detected"**: Kurangi gain atau trim data
3. **"Conversion error"**: Periksa data quality di info panel
4. **"File size mismatch"**: Periksa binary file integrity

### Debug Info:
- Info panel (toggle dengan "Info Panel" button)
- Conversion history (10 terakhir)
- Real-time statistics
- Warning messages

## 📈 Performance Tips

### For Large Files:
- Gunakan trim untuk mengurangi data size
- Adjust window size untuk smooth playback
- Monitor memory usage dengan info panel

### For ESP32 Integration:
- Test dengan gain rendah dulu
- Validasi binary file size
- Check voltage range sebelum deployment

## 🎛️ Advanced Features

### 1. **Info Panel**
- Collapsible sidebar dengan conversion history
- Real-time statistics
- Warning tracking
- File validation info

### 2. **Export Options**
- **Binary**: Optimized untuk ESP32 (12 channels × 2 bytes)
- **CSV**: Human-readable dengan timestamp dan unit labels

### 3. **Channel Management**
- Select/deselect all channels
- Individual channel visibility
- Auto-scaling per channel
- Color-coded channels

## 📞 Support

### File Structure:
```
mainlama.py          # Main application (1565 lines)
├── ECGToBinaryConverter class
├── SidebarInfoPanel class  
├── ConversionHistoryItem class
└── ECGMode enum
```

### Key Classes:
- **ECGToBinaryConverter**: Main GUI application
- **SidebarInfoPanel**: Information display panel
- **ConversionHistoryItem**: History tracking
- **ECGMode**: Mode enumeration (12-lead/10-lead)

### Dependencies:
- **PyQt5**: GUI framework
- **pyqtgraph**: Real-time plotting
- **wfdb**: PhysioNet file reading
- **numpy**: Data processing

---

**Last Updated**: 2024  
**Version**: 1.0  
**Target Platform**: Windows/Linux/macOS  
**Hardware Target**: ESP32 with 12-bit ADC 