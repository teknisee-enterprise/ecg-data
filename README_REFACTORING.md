# ECG Converter Refactoring Documentation

## Overview

Program `main.py` asli memiliki 1565 baris kode dalam satu file monolitik. Refactoring ini memisahkan kode menjadi modul-modul yang lebih kecil dan mudah di-maintain.

## Struktur Refactoring

### 1. **Models** (`models/`)
**Tujuan:** Menyimpan data structures dan business logic

#### `models/ecg_data.py`
- **ECGMode** (Enum): Mode 12-lead atau 10-lead
- **ConversionHistoryItem** (dataclass): Menyimpan riwayat konversi
- **ECGData** (class): Container data ECG dengan processing capabilities
  - `map_channels_to_standard()`: Mapping channel ke posisi standar 12-lead
  - `convert_to_10lead()`: Konversi 12-lead ke 10-lead electrodes
  - `update_trim()`: Update signal trimming
  - `get_trimmed_samples_count()`: Get jumlah samples yang di-trim

### 2. **Utils** (`utils/`)
**Tujuan:** Helper functions dan utilities

#### `utils/esp32_converter.py`
- **ESP32Converter** (class): Konversi data ke format ESP32
  - `convert_mv_to_adc()`: Konversi mV ke ADC values
  - `convert_adc_to_voltage()`: Konversi ADC ke voltage
  - `get_display_data()`: Data untuk display berdasarkan Y-axis mode
  - `check_gain_warnings()`: Cek warning gain
  - `convert_to_binary()`: Konversi ke binary format

#### `utils/csv_exporter.py`
- **CSVExporter** (class): Export data ke CSV
  - `get_unit_suffix()`: Get unit suffix berdasarkan Y-axis mode
  - `export_to_csv()`: Export data ke CSV format
  - `get_export_info()`: Generate export information text

### 3. **UI** (`ui/`)
**Tujuan:** User interface components

#### `ui/sidebar_panel.py`
- **SidebarInfoPanel** (class): Panel sidebar untuk informasi konversi
  - `toggle()`: Toggle visibility sidebar
  - `set_current_info()`: Update info konversi
  - `add_history_item()`: Tambah item ke history
  - `update_history_display()`: Update display history

#### `ui/plot_manager.py`
- **PlotManager** (class): Manajemen plot widgets dan display
  - `create_plot_area()`: Buat area plot dengan scrollable plots
  - `update_channel_display()`: Update channel labels dan visibility
  - `update_plot_layout()`: Update layout plot berdasarkan visible channels
  - `update_plots()`: Update semua plots dengan current window
  - `toggle_guide_lines()`: Toggle guide lines visibility

### 4. **Main Application** (`main_refactored.py`)
**Tujuan:** Main application yang menggunakan semua modul

- **ECGToBinaryConverter** (class): Main application class
  - `setup_ui()`: Setup user interface
  - `setup_connections()`: Setup signal connections
  - `load_record()`: Load record dari PhysioNet
  - `convert_to_binary()`: Konversi ke binary format
  - `export_to_csv()`: Export ke CSV format

## Keuntungan Refactoring

### 1. **Separation of Concerns**
- **Data Logic** terpisah di `models/`
- **Conversion Logic** terpisah di `utils/esp32_converter.py`
- **UI Logic** terpisah di `ui/`
- **Main Application** hanya fokus pada orchestration

### 2. **Maintainability**
- Setiap modul memiliki tanggung jawab spesifik
- Mudah untuk menambah fitur baru
- Mudah untuk debug masalah tertentu
- Kode lebih readable dan organized

### 3. **Testability**
- Setiap modul bisa di-test secara independen
- Unit testing lebih mudah
- Mock objects bisa dibuat untuk testing

### 4. **Reusability**
- Modul bisa digunakan di aplikasi lain
- ESP32Converter bisa digunakan untuk project lain
- CSVExporter bisa digunakan untuk export data lain

### 5. **Scalability**
- Mudah untuk menambah modul baru
- Mudah untuk mengubah implementasi tanpa mempengaruhi modul lain
- Architecture mendukung future enhancements

## Perbandingan Struktur

### **Sebelum Refactoring:**
```
main.py (1565 baris)
├── ECGMode (Enum)
├── ConversionHistoryItem (class)
├── SidebarInfoPanel (class)
└── ECGToBinaryConverter (class)
    ├── create_control_panel() (100+ baris)
    ├── create_channel_controls() (50+ baris)
    ├── create_plot_area() (200+ baris)
    ├── load_record() (100+ baris)
    ├── convert_to_binary() (200+ baris)
    ├── export_to_csv() (150+ baris)
    ├── update_plots() (100+ baris)
    └── ... (20+ methods lainnya)
```

### **Setelah Refactoring:**
```
models/
├── __init__.py
└── ecg_data.py
    ├── ECGMode (Enum)
    ├── ConversionHistoryItem (dataclass)
    └── ECGData (class)

utils/
├── __init__.py
├── esp32_converter.py
│   └── ESP32Converter (class)
└── csv_exporter.py
    └── CSVExporter (class)

ui/
├── __init__.py
├── sidebar_panel.py
│   └── SidebarInfoPanel (class)
└── plot_manager.py
    └── PlotManager (class)

main_refactored.py (400+ baris)
└── ECGToBinaryConverter (class)
    ├── setup_ui()
    ├── setup_connections()
    ├── load_record()
    ├── convert_to_binary()
    ├── export_to_csv()
    └── ... (10+ methods lainnya)
```

## Cara Menggunakan

### 1. **Setup Project Structure**
```bash
mkdir models utils ui
touch models/__init__.py utils/__init__.py ui/__init__.py
```

### 2. **Copy Files**
- Copy semua file dari struktur di atas
- Pastikan semua dependencies terinstall

### 3. **Run Application**
```bash
python main_refactored.py
```

## Migration Guide

### Dari `main.py` ke `main_refactored.py`:

1. **Data Access:**
   ```python
   # Sebelum
   self.signal = self.record.p_signal
   
   # Sesudah
   self.ecg_data.signal = self.ecg_data.record.p_signal
   ```

2. **Conversion Logic:**
   ```python
   # Sebelum
   adc_values = self.convert_mv_to_adc(signal_mv)
   
   # Sesudah
   adc_values = self.esp32_converter.convert_mv_to_adc(signal_mv)
   ```

3. **Plot Updates:**
   ```python
   # Sebelum
   self.plot_lines[i].setData(visible_time, visible_data)
   
   # Sesudah
   self.plot_manager.update_plots(signal_data, time_data, ...)
   ```

## Best Practices

### 1. **Dependency Injection**
- Main application inject dependencies ke modul
- Modul tidak bergantung pada global state

### 2. **Interface Segregation**
- Setiap modul memiliki interface yang jelas
- Minimal coupling antar modul

### 3. **Single Responsibility**
- Setiap class/module punya satu tanggung jawab
- Mudah untuk understand dan maintain

### 4. **Open/Closed Principle**
- Modul open untuk extension
- Closed untuk modification

## Future Enhancements

### 1. **Configuration Management**
- Buat `config/` module untuk settings
- Support untuk multiple ESP32 configurations

### 2. **Plugin System**
- Buat plugin system untuk custom converters
- Support untuk different output formats

### 3. **Database Integration**
- Buat `database/` module untuk persistent storage
- Support untuk conversion history database

### 4. **API Layer**
- Buat `api/` module untuk REST API
- Support untuk web interface

## Conclusion

Refactoring ini mengubah aplikasi dari monolitik menjadi modular dengan:
- **70% reduction** dalam main file size
- **Clear separation** of concerns
- **Better maintainability** dan testability
- **Improved scalability** untuk future features
- **Easier debugging** dan development

Struktur modular ini membuat aplikasi lebih professional dan siap untuk production use. 