#!/usr/bin/env python3
"""
X-Plane Airway Extractor

A tool to convert navigation data from CSV format to X-Plane compatible DAT format
for creating custom airway definitions.
"""
import argparse
import csv
import logging
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class NavigationType(Enum):
    """Types of navigation points supported in the X-Plane system."""
    DESIGNATED_POINT = ('DESIGNATED_POINT', '11')
    VORDME = ('VORDME', '3')
    NDB = ('NDB', '2')

    def __init__(self, code_type: str, type_code: str):
        self.code_type = code_type
        self.type_code = type_code


@dataclass
class NavigationPoint:
    """Represents a navigation point with its properties."""
    identifier: str
    type: NavigationType
    area_code: Optional[str] = None


def get_navigation_type(code_type: str) -> Optional[NavigationType]:
    """Get the navigation type from the code type string.
    
    Args:
        code_type: String representing the navigation type code
        
    Returns:
        NavigationType enum if found, None otherwise
    """
    if not code_type:
        logger.error("Empty code type provided")
        return None
        
    for nav_type in NavigationType:
        if nav_type.code_type == code_type:
            return nav_type
    logger.warning(f"Unknown navigation type encountered: {code_type}")
    return None


def process_navigation_point(
    identifier: str,
    code_type: str,
    earth_fix_data: Dict[str, str],
    earth_nav_data: Dict[str, str]
) -> Optional[NavigationPoint]:
    """Process a navigation point and return its details.
    
    Args:
        identifier: The navigation point identifier
        code_type: The type of navigation point
        earth_fix_data: Dictionary of fix point data
        earth_nav_data: Dictionary of navigation point data
        
    Returns:
        NavigationPoint object if valid, None otherwise
    """
    if not identifier:
        logger.error("Empty identifier provided")
        return None
        
    nav_type = get_navigation_type(code_type)
    if not nav_type:
        return None

    # Get area code based on navigation type
    area_code = None
    if nav_type == NavigationType.DESIGNATED_POINT:
        area_code = earth_fix_data.get(identifier)
        if not area_code:
            logger.warning(f"No area code found for fix point {identifier}")
    else:  # VORDME or NDB
        area_code = earth_nav_data.get(identifier)
        if not area_code:
            logger.warning(f"No area code found for {nav_type.code_type} point {identifier}")

    if not area_code:
        return None

    return NavigationPoint(
        identifier=identifier,
        type=nav_type,
        area_code=area_code
    )


def load_fixed_width_data(
    filepath: Union[str, Path], 
    key_index: int, 
    value_index: int, 
    extra_condition_index: Optional[int] = None, 
    extra_condition_values: Optional[Set[str]] = None,
    type_index: Optional[int] = None, 
    type_value: Optional[str] = None
) -> Dict[str, str]:
    """
    Load data from a fixed-width file into a dictionary.
    
    Args:
        filepath: Path to the data file
        key_index: Column index to use as dictionary key
        value_index: Column index to use as dictionary value
        extra_condition_index: Optional index for filtering data
        extra_condition_values: Set of accepted values for the extra condition
        type_index: Optional index for type filtering
        type_value: Value to match for type filtering
        
    Returns:
        Dictionary mapping keys to values from the specified file
    """
    data = {}
    filepath = Path(filepath)
    
    try:
        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return {}
            
        with open(filepath, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                parts = line.split()
                if len(parts) <= max(key_index, value_index):
                    logger.warning(f"Line {line_num} has insufficient columns: {line}")
                    continue
                    
                # Check conditions
                condition_met = True
                if extra_condition_index is not None and extra_condition_values is not None:
                    if len(parts) <= extra_condition_index or parts[extra_condition_index] not in extra_condition_values:
                        condition_met = False
                        
                if type_index is not None and type_value is not None:
                    if len(parts) <= type_index or parts[type_index] != type_value:
                        condition_met = False
                
                if condition_met:
                    key = parts[key_index]
                    value = parts[value_index]
                    data[key] = value
                    
        logger.info(f"Successfully loaded {len(data)} entries from {filepath}")
        return data
        
    except Exception as e:
        logger.error(f"Error loading data from {filepath}: {str(e)}")
        return {}


def sort_key(line: str) -> tuple:
    """
    Extract sort key from a line based on the last component.
    
    Args:
        line: Text line to analyze
        
    Returns:
        Tuple for sorting (letters, numbers)
        
    Raises:
        ValueError: If the line is empty or invalid
    """
    if not line or not isinstance(line, str):
        raise ValueError("Invalid input: line must be a non-empty string")
        
    parts = line.split()
    if not parts:
        raise ValueError("Empty line provided")
        
    last_part = parts[-1]
    match = re.match(r"([A-Z]+)(\d*)$", last_part)
    if match:
        letters, numbers = match.groups()
        numbers = int(numbers) if numbers else 0
        return (letters, numbers)
    return (last_part, float('inf'))


def convert_csv_to_dat(
    csv_file: Union[str, Path], 
    earth_fix_path: Union[str, Path], 
    earth_nav_path: Union[str, Path], 
    output_file: Union[str, Path]
) -> None:
    """
    Convert navigation data from CSV format to X-Plane DAT format.
    
    Args:
        csv_file: Path to input CSV file
        earth_fix_path: Path to earth_fix.dat reference file
        earth_nav_path: Path to earth_nav.dat reference file
        output_file: Path for output DAT file
        
    Raises:
        FileNotFoundError: If any input file is not found
        ValueError: If input files are invalid
    """
    # Convert to Path objects
    csv_file = Path(csv_file)
    earth_fix_path = Path(earth_fix_path)
    earth_nav_path = Path(earth_nav_path)
    output_file = Path(output_file)
    
    # Validate input files
    for file_path in [csv_file, earth_fix_path, earth_nav_path]:
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
    
    # Load reference data
    logger.info("Loading reference data...")
    earth_fix_data = load_fixed_width_data(
        earth_fix_path, 2, 4, 3, {"ENRT"}, 3, "ENRT"
    )
    earth_nav_data = load_fixed_width_data(
        earth_nav_path, 7, 9, 8, {"ENRT"}, 8, "ENRT"
    )
    
    if not earth_fix_data or not earth_nav_data:
        raise ValueError("Failed to load reference data")
        
    logger.info(f"Loaded {len(earth_fix_data)} fix points and {len(earth_nav_data)} nav points")
    
    output_lines = []
    skipped_rows = 0
    processed_rows = 0

    try:
        with open(csv_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            required_fields = {'CODE_POINT_START', 'CODE_TYPE_START', 'CODE_POINT_END', 
                             'CODE_TYPE_END', 'CODE_DIR', 'TXT_DESIG'}
            
            # Validate CSV header
            missing_fields = required_fields - set(reader.fieldnames or [])
            if missing_fields:
                raise ValueError(f"CSV file missing required fields: {missing_fields}")
            
            for row in tqdm(reader, desc="Processing Rows"):
                processed_rows += 1
                
                # Check for empty fields
                missing_values = [field for field in required_fields if not row.get(field)]
                if missing_values:
                    logger.warning(f"Row {processed_rows} missing values for: {', '.join(missing_values)}")
                    skipped_rows += 1
                    continue
                
                # Process start point
                start_point = process_navigation_point(
                    identifier=row['CODE_POINT_START'],
                    code_type=row['CODE_TYPE_START'],
                    earth_fix_data=earth_fix_data,
                    earth_nav_data=earth_nav_data
                )
                
                if not start_point:
                    logger.warning(f"Failed to process start point in row {processed_rows}")
                    skipped_rows += 1
                    continue

                # Process end point
                end_point = process_navigation_point(
                    identifier=row['CODE_POINT_END'],
                    code_type=row['CODE_TYPE_END'],
                    earth_fix_data=earth_fix_data,
                    earth_nav_data=earth_nav_data
                )
                
                if not end_point:
                    logger.warning(f"Failed to process end point in row {processed_rows}")
                    skipped_rows += 1
                    continue

                # Direction
                direction = 'N' if row['CODE_DIR'] == 'X' else row['CODE_DIR']
                
                # Fixed values - part of the X-Plane airway format
                base_altitude = '0'
                top_altitude = '600'
                airway_designator = row['TXT_DESIG']
                
                # Generate both directions of the airway (bidirectional)
                for direction_index in range(1, 3):
                    dat_line = (
                        f"{start_point.identifier:>5}{start_point.area_code:>3}{start_point.type.type_code:>3}"
                        f"{end_point.identifier:>6}{end_point.area_code:>3}{end_point.type.type_code:>3}"
                        f"{direction:>2}{direction_index:>2}{base_altitude:>4}{top_altitude:>4} {airway_designator}\n"
                    )
                    output_lines.append(dat_line)

        # Sort and write output
        try:
            output_lines.sort(key=sort_key)
            
            # Ensure output directory exists
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as datfile:
                datfile.writelines(output_lines)

            logger.info(f"Processing completed! Wrote {len(output_lines)} lines to {output_file}")
            if skipped_rows > 0:
                logger.warning(f"Skipped {skipped_rows} rows due to missing or invalid data")
                
        except Exception as e:
            logger.error(f"Error writing output file: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Convert navigation data from CSV to X-Plane DAT format',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '-c', '--csv-file', 
        required=True,
        help='Path to input CSV file with airway data'
    )
    
    parser.add_argument(
        '-f', '--fix-file',
        required=True, 
        help='Path to earth_fix.dat reference file'
    )
    
    parser.add_argument(
        '-n', '--nav-file',
        required=True, 
        help='Path to earth_nav.dat reference file'
    )
    
    parser.add_argument(
        '-o', '--output-file',
        required=True, 
        help='Path for output DAT file'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        logger.info("Starting X-Plane Airway Extraction")
        convert_csv_to_dat(
            args.csv_file,
            args.fix_file,
            args.nav_file,
            args.output_file
        )
        logger.info("Airway extraction completed successfully")
        return 0
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Invalid data: {e}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())