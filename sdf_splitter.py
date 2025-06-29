#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
from pathlib import Path
import datetime

def split_sdf_file(input_file_path, output_base_dir="output", compounds_per_folder=10000):
    """
    Split large SDF file into separate files based on DATABASE_ID
    Organize compounds into folders with maximum compounds_per_folder each
    
    Args:
        input_file_path (str): Path to input SDF file
        output_base_dir (str): Base directory for output
        compounds_per_folder (int): Maximum compounds per folder
    """
    
    # Create output directory
    output_path = Path(output_base_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create error log file
    error_log_path = output_path / "error.log"
    
    current_compound = []
    compound_count = 0
    folder_count = 1
    current_folder_compounds = 0
    error_count = 0
    
    print(f"Processing SDF file: {input_file_path}")
    print(f"Output directory: {output_base_dir}")
    print(f"Maximum {compounds_per_folder} compounds per folder")
    print(f"Error log file: {error_log_path}")
    
    # Initialize error log file
    with open(error_log_path, 'w', encoding='utf-8') as error_log:
        error_log.write(f"SDF File Processing Error Log\n")
        error_log.write(f"Start Time: {datetime.datetime.now()}\n")
        error_log.write(f"Source File: {input_file_path}\n")
        error_log.write("="*80 + "\n\n")
    
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                current_compound.append(line)
                
                # Each compound ends with $$$$
                if line.strip() == "$$$$":
                    # Find DATABASE_ID
                    database_id = extract_database_id(current_compound)
                    
                    if database_id:
                        # Determine folder name
                        folder_name = f"batch_{folder_count:04d}"
                        folder_path = output_path / folder_name
                        folder_path.mkdir(exist_ok=True)
                        
                        # Create filename
                        filename = f"{database_id}.sdf"
                        file_path = folder_path / filename
                        
                        # Write compound to file
                        try:
                            with open(file_path, 'w', encoding='utf-8') as output_file:
                                output_file.writelines(current_compound)
                            
                            compound_count += 1
                            current_folder_compounds += 1
                            
                            # Progress report
                            if compound_count % 1000 == 0:
                                print(f"Processed compounds: {compound_count} | Errors: {error_count}")
                            
                            # Check folder limit
                            if current_folder_compounds >= compounds_per_folder:
                                folder_count += 1
                                current_folder_compounds = 0
                                print(f"Creating new folder: batch_{folder_count:04d}")
                                
                        except Exception as e:
                            error_count += 1
                            error_msg = f"File writing error - {filename}: {e}"
                            print(f"ERROR: {error_msg}")
                            log_error(error_log_path, "FILE_WRITE_ERROR", error_msg, line_num, 
                                    database_id, current_compound[:5])  # Log first 5 lines
                    
                    else:
                        error_count += 1
                        error_msg = f"DATABASE_ID not found (line {line_num})"
                        print(f"ERROR: {error_msg}")
                        log_error(error_log_path, "DATABASE_ID_NOT_FOUND", error_msg, line_num,
                                None, current_compound[:10])  # Log first 10 lines
                    
                    # Clear for next compound
                    current_compound = []
                    
    except FileNotFoundError:
        error_msg = f"File not found - {input_file_path}"
        print(f"ERROR: {error_msg}")
        log_error(error_log_path, "FILE_NOT_FOUND", error_msg, 0, None, [])
        return
    except Exception as e:
        error_msg = f"File reading error: {e}"
        print(f"ERROR: {error_msg}")
        log_error(error_log_path, "FILE_READ_ERROR", error_msg, 0, None, [])
        return
    
    # Add final summary to error log
    with open(error_log_path, 'a', encoding='utf-8') as error_log:
        error_log.write(f"\n" + "="*80 + "\n")
        error_log.write(f"Processing Summary\n")
        error_log.write(f"End Time: {datetime.datetime.now()}\n")
        error_log.write(f"Total Processed Compounds: {compound_count}\n")
        error_log.write(f"Total Errors: {error_count}\n")
        error_log.write(f"Created Folders: {folder_count}\n")
    
    print(f"\nProcessing completed!")
    print(f"Total processed compounds: {compound_count}")
    print(f"Total errors: {error_count}")
    print(f"Created folders: {folder_count}")
    print(f"Compounds in last folder: {current_folder_compounds}")
    if error_count > 0:
        print(f"Error details in: {error_log_path}")

def log_error(error_log_path, error_type, error_message, line_number, database_id, compound_sample):
    """
    Write error information to log file
    
    Args:
        error_log_path (Path): Path to error log file
        error_type (str): Type of error
        error_message (str): Error message
        line_number (int): Line number where error occurred
        database_id (str): Compound ID if available
        compound_sample (list): Sample lines from the compound
    """
    try:
        with open(error_log_path, 'a', encoding='utf-8') as error_log:
            error_log.write(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ")
            error_log.write(f"ERROR TYPE: {error_type}\n")
            error_log.write(f"MESSAGE: {error_message}\n")
            error_log.write(f"LINE: {line_number}\n")
            error_log.write(f"DATABASE_ID: {database_id if database_id else 'Not found'}\n")
            
            if compound_sample:
                error_log.write(f"COMPOUND SAMPLE (first {len(compound_sample)} lines):\n")
                for i, line in enumerate(compound_sample, 1):
                    error_log.write(f"  {i:2d}: {line.rstrip()}\n")
            
            error_log.write("-" * 40 + "\n\n")
            
    except Exception as e:
        print(f"Error log writing error: {e}")

def extract_database_id(compound_lines):
    """
    Extract DATABASE_ID from compound lines
    
    Args:
        compound_lines (list): All lines of the compound
        
    Returns:
        str: DATABASE_ID value or None
    """
    for i, line in enumerate(compound_lines):
        if line.strip() == "> <DATABASE_ID>":
            # ID should be in the next line
            if i + 1 < len(compound_lines):
                database_id = compound_lines[i + 1].strip()
                if database_id:
                    return database_id
    return None

def get_file_info(file_path):
    """
    Get information about the file
    """
    try:
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
        print(f"File size: {file_size:.2f} MB")
        
        # Show first few lines
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = []
            for i, line in enumerate(file):
                if i < 10:
                    lines.append(line.rstrip())
                else:
                    break
            
        print("First 10 lines of the file:")
        for line in lines:
            print(f"  {line}")
            
    except Exception as e:
        print(f"Could not get file info: {e}")

# Usage example
if __name__ == "__main__":
    # Get current working directory
    current_dir = os.getcwd()
    sdf_file_path = os.path.join(current_dir, "structures.sdf")
    output_directory = os.path.join(current_dir, "compound_files")
    
    print("SDF File Splitter")
    print("=" * 50)
    print(f"Working directory: {current_dir}")
    
    # Check file existence
    if os.path.exists(sdf_file_path):
        print(f"SDF file found: {sdf_file_path}")
        get_file_info(sdf_file_path)
        print("\nStarting splitting process...")
        
        # Run main function
        split_sdf_file(
            input_file_path=sdf_file_path,
            output_base_dir=output_directory,
            compounds_per_folder=10000
        )
    else:
        print(f"Error: SDF file not found - {sdf_file_path}")
        print(f"Searched location: {sdf_file_path}")
        print("Please make sure 'structures.sdf' file is in this directory.")
        
        # List existing .sdf files in current directory
        sdf_files = [f for f in os.listdir(current_dir) if f.endswith('.sdf')]
        if sdf_files:
            print(f"\n.sdf files found in this directory:")
            for sdf_file in sdf_files:
                print(f"  - {sdf_file}")
        else:
            print("\nNo .sdf files found in this directory.")