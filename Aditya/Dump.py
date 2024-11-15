import pandas as pd
import json
import csv
from typing import Dict, List, Any
import os
from pathlib import Path

def detect_encoding(csv_file: str) -> str:
    """
    Attempt to detect the file encoding
    Returns default 'utf-8' if unable to determine
    """
    try:
        import chardet
        with open(csv_file, 'rb') as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            return result['encoding'] if result['encoding'] else 'utf-8'
    except ImportError:
        return 'utf-8'

def detect_delimiter(csv_file: str, encoding: str) -> str:
    """
    Attempt to detect the CSV delimiter
    """
    sniffer = csv.Sniffer()
    with open(csv_file, 'r', encoding=encoding) as file:
        sample = file.read(4096)  # Read first 4096 bytes
        try:
            dialect = sniffer.sniff(sample)
            return dialect.delimiter
        except:
            return ','  # Default to comma if detection fails

def csv_to_json(csv_file: str, output_file: str = None, encoding: str = None, delimiter: str = None) -> Dict[str, Any]:
    """
    Convert CSV file to JSON with automatic header detection and data analysis.
    
    Args:
        csv_file (str): Path to the CSV file
        output_file (str, optional): Path to save the JSON output. If None, won't save to file.
        encoding (str, optional): File encoding (auto-detected if None)
        delimiter (str, optional): CSV delimiter (auto-detected if None)
    
    Returns:
        Dict containing the converted data and analysis
    """
    try:
        # Auto-detect encoding if not provided
        if encoding is None:
            encoding = detect_encoding(csv_file)
        
        # Auto-detect delimiter if not provided
        if delimiter is None:
            delimiter = detect_delimiter(csv_file, encoding)
        
        # Read CSV file
        df = pd.read_csv(csv_file, encoding=encoding, delimiter=delimiter)
        
        # Clean column names (remove whitespace, special characters)
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
        
        # Analyze data
        analysis = {
            "file_analysis": {
                "filename": Path(csv_file).name,
                "encoding": encoding,
                "delimiter": delimiter,
                "file_size_bytes": os.path.getsize(csv_file)
            },
            "data_analysis": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "column_names": list(df.columns),
                "data_types": {col: str(df[col].dtype) for col in df.columns},
                "non_null_counts": df.count().to_dict(),
                "null_percentages": (df.isnull().sum() / len(df) * 100).round(2).to_dict(),
                "sample_values": {col: df[col].dropna().head(3).tolist() for col in df.columns},
                "unique_values_count": {col: df[col].nunique() for col in df.columns}
            }
        }
        
        # Convert DataFrame to list of dictionaries
        data = df.replace({pd.NA: None}).to_dict('records')
        
        # Prepare final result
        result = {
            "analysis": analysis,
            "data": data
        }
        
        # Save to file if output_file is specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        
        return result
    
    except Exception as e:
        raise Exception(f"Error processing CSV file: {str(e)}")

def main():
    """
    Example usage of the converter with command line interface
    """
    try:
        # Get input from user
        csv_file = input("Enter the CSV file path: ")
        output_file = input("Enter the output JSON file path (press Enter to skip saving): ").strip()
        encoding = input("Enter file encoding (press Enter for auto-detection): ").strip()
        delimiter = input("Enter delimiter (press Enter for auto-detection): ").strip()
        
        # Process optional inputs
        output_file = output_file if output_file else None
        encoding = encoding if encoding else None
        delimiter = delimiter if delimiter else None
        
        # Convert file
        result = csv_to_json(csv_file, output_file, encoding, delimiter)
        
        # Print summary
        print("\nConversion Summary:")
        print(f"File: {result['analysis']['file_analysis']['filename']}")
        print(f"Encoding: {result['analysis']['file_analysis']['encoding']}")
        print(f"Delimiter: {result['analysis']['file_analysis']['delimiter']}")
        print(f"Total Rows: {result['analysis']['data_analysis']['total_rows']}")
        print(f"Total Columns: {result['analysis']['data_analysis']['total_columns']}")
        print("Columns:", ', '.join(result['analysis']['data_analysis']['column_names']))
        
        if output_file:
            print(f"\nJSON file saved to: {output_file}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
