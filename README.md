# X-Plane Airway Extractor

A tool to convert navigation data from CSV format to X-Plane compatible DAT format for creating custom airway definitions.

## Overview

This utility extracts navigation data from CSV files and converts it to the X-Plane airway format, allowing you to create custom airway definitions for X-Plane flight simulator.

It processes navigation points (fixes, VORs, NDBs) and creates proper bidirectional airway definitions with the correct format required by X-Plane.

## Features

- Converts CSV navigation data to X-Plane DAT format
- Supports different navigation point types (fixes, VORDMEs, NDBs)
- Validates input data against X-Plane's earth_fix.dat and earth_nav.dat files
- Generates bidirectional airway definitions
- Provides detailed logging and error handling
- Command-line interface with flexible options

## Requirements

- Python 3.6+
- tqdm (for progress bars)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/xplane-airway-extractor.git
   cd xplane-airway-extractor
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Basic Usage

```bash
python xplane_airway_extractor.py \
  -c input_data.csv \
  -f /path/to/X-Plane/Custom\ Data/earth_fix.dat \
  -n /path/to/X-Plane/Custom\ Data/earth_nav.dat \
  -o /path/to/output/airway.dat
```

### Command Line Arguments

| Argument | Description |
|----------|-------------|
| `-c, --csv-file` | Path to input CSV file with airway data |
| `-f, --fix-file` | Path to earth_fix.dat reference file |
| `-n, --nav-file` | Path to earth_nav.dat reference file |
| `-o, --output-file` | Path for output DAT file |
| `-v, --verbose` | Enable verbose output |

### Input CSV Format

The input CSV file must contain the following columns:

- `CODE_POINT_START`: Identifier for the starting navigation point
- `CODE_TYPE_START`: Type of the starting navigation point (DESIGNATED_POINT, VORDME, NDB)
- `CODE_POINT_END`: Identifier for the ending navigation point
- `CODE_TYPE_END`: Type of the ending navigation point (DESIGNATED_POINT, VORDME, NDB)
- `CODE_DIR`: Direction code (N for North, etc., X for bidirectional)
- `TXT_DESIG`: Airway designator (e.g., J123, A456)

## Output Format

The output is a properly formatted X-Plane airway.dat file that can be used directly with X-Plane. The format follows X-Plane's specifications for airways.

Each line in the output file represents one segment of an airway and contains:
- Start point identifier and details
- End point identifier and details  
- Direction information
- Altitude constraints
- Airway designator

## Examples

### Example Input CSV

```csv
CODE_POINT_START,CODE_TYPE_START,CODE_POINT_END,CODE_TYPE_END,CODE_DIR,TXT_DESIG
ALPHA,DESIGNATED_POINT,BRAVO,DESIGNATED_POINT,X,J123
BRAVO,DESIGNATED_POINT,CHARLIE,VORDME,X,J123
```

### Example Output DAT

```
ALPHA OBE 11 BRAVO OBE 11 N 1   0 600 J123
ALPHA OBE 11 BRAVO OBE 11 N 2   0 600 J123
BRAVO OBE 11CHARLIE OBE  3 N 1   0 600 J123
BRAVO OBE 11CHARLIE OBE  3 N 2   0 600 J123
```

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Thanks to the X-Plane community for their documentation on the airway format
- Navigation data is typically sourced from aviation authorities like FAA, NATS, etc. 