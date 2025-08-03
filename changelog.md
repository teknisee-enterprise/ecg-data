# Changelog

All notable changes to the ECG Converter application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-19

### Added
- **Complete modular architecture** - Refactored monolithic `mainlama.py` into 5 focused modules:
  - `data_loader.py` - Handles PhysioNet data loading and channel management
  - `signal_processor.py` - Signal processing and conversion utilities
  - `gui_components.py` - Reusable PyQt5 GUI components
  - `converter.py` - Binary and CSV export functionality
  - `main.py` - Main application entry point and UI orchestration

- **New data source integration** - Support for `sampleRaw/` folder with:
  - 37-channel PhysioNet files (`.dat`, `.hea`)
  - 800 Hz sample rate
  - Raw and processed channel types
  - Automatic filtering of unipolar channels (prefix 'U')

- **Enhanced channel mapping system**:
  - **Raw mode**: RA, LA, LL, RL (always 0), V1-V6 (10 channels total)
  - **Processed mode**: RA, LA, LL, RL (always 0), V1-V6, WCT (11 channels total)
  - **Binary export**: Fixed 12-channel format (RA, LA, LL, RL, B1, B2, V1-V6) with RL, B1, B2 set to 0

- **Improved data display**:
  - Toggle between raw and processed data modes
  - Dynamic channel count handling (10 vs 11 channels)
  - Automatic plot hiding for non-existent channels
  - Channel selection via checkboxes

- **Enhanced binary conversion**:
  - Fixed 12-channel output format for ESP32 compatibility
  - Proper file size calculation (12 channels × 2 bytes per sample)
  - Zero-padding for fixed channels (RL, B1, B2)

- **Comprehensive documentation**:
  - `README.md` with detailed feature descriptions
  - `run_main.py` launcher script
  - `src/__init__.py` package definition

### Changed
- **Architecture**: From monolithic 1565-line `mainlama.py` to modular design with each file < 600 lines
- **Data source**: From `sample/` folder to `sampleRaw/` folder
- **Channel handling**: From fixed 12 channels to dynamic 10/11 channels with proper bounds checking
- **Binary export**: From dynamic channels to fixed 12-channel format for ESP32 compatibility

### Technical Improvements
- **Memory efficiency**: Dynamic array allocation based on actual channel count
- **Error handling**: Bounds checking to prevent IndexError in GUI components
- **Code organization**: Clear separation of concerns across modules
- **Maintainability**: Each module has a single responsibility and clear interfaces

### File Structure
```
ecgdata/
├── src/                    # New modular application
│   ├── __init__.py
│   ├── data_loader.py     # Data loading and channel management
│   ├── signal_processor.py # Signal processing utilities
│   ├── gui_components.py  # GUI components
│   ├── converter.py       # Export functionality
│   └── main.py           # Main application
├── sampleRaw/             # New data source
│   ├── seg01.dat
│   ├── seg01.hea
│   ├── seg02.dat
│   ├── seg02.hea
│   ├── seg03.dat
│   └── seg03.hea
├── run_main.py           # Application launcher
├── README.md             # Comprehensive documentation
└── changelog.md         # This file
```

### Migration Notes
- `mainlama.py` is now reference-only, not part of the new application
- `validator.py` and `validator-10.py` are not related to the new application
- All new development should use the modular `src/` structure
- Environment activation required: `.\env\Scripts\activate`

### Known Issues
- None reported in this version

### Dependencies
- PyQt5 (GUI framework)
- pyqtgraph (plotting library)
- wfdb (PhysioNet data handling)
- NumPy (numerical operations)

### Testing
- Verified channel mapping for both raw and processed modes
- Confirmed binary export uses correct 12-channel format
- Tested dynamic GUI handling for varying channel counts
- Validated file size calculations for binary output

---

## Legacy Version (mainlama.py)

### Features (Reference Only)
- Monolithic ECG data converter application
- Support for 12-lead and 10-lead ECG data
- Binary and CSV export formats
- ESP32-compatible ADC conversion
- Signal processing and visualization
- File: `mainlama.py` (1565 lines)

### Data Source
- `sample/` folder with PhysioNet files
- Files: `I01`, `00001_lr`, `100` (`.dat`, `.hea`)

### Channel Configuration
- Fixed 12-channel system
- No distinction between raw/processed modes
- All channels displayed simultaneously

### Export Format
- Dynamic channel count based on available data
- Variable file sizes depending on channel count

---

*This changelog follows the [Keep a Changelog](https://keepachangelog.com/) format and uses [Semantic Versioning](https://semver.org/).* 