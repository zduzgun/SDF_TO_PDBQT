#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import multiprocessing as mp
from pathlib import Path
import logging
from datetime import datetime
import time
from rdkit import Chem
from rdkit.Chem import Lipinski

# =============================================================================
# CONFIGURATION SECTION
# =============================================================================

# Upper limit for the number of rotatable bonds.
# Based on literature, 10 (strict) or 15 (reasonable) is a good choice.
ROTATABLE_BOND_THRESHOLD = 15

# Input and output base directories
INPUT_BASE_DIR = "compound_files"
OUTPUT_BASE_DIR = "filtered_sdf_files"  # New directory for filtered files

# Number of processes
NUM_PROCESSES = 20 # Adjust according to the number of cores on your server

# =============================================================================
# END CONFIGURATION SECTION
# =============================================================================

def setup_logging(log_dir, batch_name):
    """Sets up logging configuration for a specific batch."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"filter_log_{batch_name}_{timestamp}.log"
    
    # Clear any existing handlers to prevent duplicate logs in the main logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
    )
    return logging.getLogger(batch_name)

def analyze_single_file(args):
    """Analyzes a single SDF file and returns the rotatable bond count."""
    input_file_path, threshold = args
    filename = input_file_path.name

    try:
        suppl = Chem.SDMolSupplier(str(input_file_path), removeHs=False, sanitize=True)
        mol = next(suppl)

        if mol is None:
            return filename, -1, 'REJECTED', 'Molecule could not be read from SDF file.'

        rotatable_bonds = Lipinski.NumRotatableBonds(mol)

        if rotatable_bonds <= threshold:
            return filename, rotatable_bonds, 'PASSED', None
        else:
            return filename, rotatable_bonds, 'REJECTED', f'Exceeds threshold of {threshold}'

    except Exception as e:
        return filename, -1, 'REJECTED', f'An unexpected error occurred: {str(e)}'

def worker_process(task_queue, result_queue):
    """Worker function for parallel processing."""
    while True:
        try:
            args = task_queue.get_nowait()
            if args is None:
                break
            result = analyze_single_file(args)
            result_queue.put(result)
        except mp.queues.Empty:
            break
        except Exception:
            break

def process_single_batch(input_batch_dir, output_base_dir, threshold, num_processes):
    """
    Analyzes and filters all SDF files in a single batch directory.
    """
    batch_name = input_batch_dir.name
    
    # Set up a unique logger for this batch run
    log_dir = output_base_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    logger = setup_logging(log_dir, batch_name)

    # Create the output directory for the filtered files of this batch
    output_batch_dir = output_base_dir / batch_name
    output_batch_dir.mkdir(exist_ok=True)
    
    logger.info(f"================== STARTING BATCH: {batch_name} ==================")
    logger.info(f"Input Directory: {input_batch_dir}")
    logger.info(f"Output Directory: {output_batch_dir}")
    logger.info(f"Rotatable Bond Threshold: <= {threshold}")
    
    sdf_files = list(input_batch_dir.glob("*.sdf"))
    if not sdf_files:
        logger.warning(f"No SDF files found in {input_batch_dir}. Skipping.")
        logger.info(f"================== FINISHED BATCH: {batch_name} ==================\n")
        return

    total_files = len(sdf_files)
    logger.info(f"Found {total_files} SDF files to analyze.")

    task_queue = mp.Queue()
    for sdf_file in sdf_files:
        task_queue.put((sdf_file, threshold))

    result_queue = mp.Queue()
    processes = [mp.Process(target=worker_process, args=(task_queue, result_queue)) for _ in range(num_processes)]

    for p in processes:
        p.start()

    passed_count = 0
    rejected_count = 0
    
    for i in range(total_files):
        try:
            filename, bond_count, status, message = result_queue.get(timeout=120)
            
            if status == 'PASSED':
                passed_count += 1
                shutil.copy(input_batch_dir / filename, output_batch_dir / filename)
                if (i+1) % 200 == 0:
                    logger.info(f"[{i+1}/{total_files}] ... PASSED: {filename} (Rot. Bonds: {bond_count})")
            else:
                rejected_count += 1
                logger.warning(f"[{i+1}/{total_files}] REJECTED: {filename} (Rot. Bonds: {bond_count}) - Reason: {message}")
        except mp.queues.Empty:
            logger.error("Result queue timeout. A process might have stalled.")
            break
            
    for p in processes:
        p.join()

    logger.info("-------------------- BATCH SUMMARY --------------------")
    logger.info(f"Total files processed: {total_files}")
    logger.info(f"Files PASSED (<= {threshold} rot. bonds): {passed_count}")
    logger.info(f"Files REJECTED (> {threshold} rot. bonds): {rejected_count}")
    logger.info(f"================== FINISHED BATCH: {batch_name} ==================\n")

def main():
    """Main function to find and process all batch directories."""
    
    input_base_dir = Path(INPUT_BASE_DIR)
    output_base_dir = Path(OUTPUT_BASE_DIR)
    output_base_dir.mkdir(exist_ok=True)

    # Find all directories matching the "batch_*" pattern
    all_batch_dirs = sorted([d for d in input_base_dir.glob("batch_*") if d.is_dir()])

    if not all_batch_dirs:
        print(f"Error: No 'batch_*' directories found in '{input_base_dir}'.")
        return

    print("=====================================================")
    print("SDF Rotatable Bond Analyzer - Multi-Batch Processor")
    print("=====================================================")
    print(f"Found {len(all_batch_dirs)} batch directories to process in '{input_base_dir}'.")
    print(f"Filtered files will be saved in subdirectories under '{output_base_dir}'.")
    print("Processing will now begin...")
    print("=====================================================")
    
    total_start_time = time.time()

    # Loop through each found batch directory and process it
    for batch_dir in all_batch_dirs:
        process_single_batch(
            input_batch_dir=batch_dir,
            output_base_dir=output_base_dir,
            threshold=ROTATABLE_BOND_THRESHOLD,
            num_processes=NUM_PROCESSES
        )
        
    total_time = time.time() - total_start_time
    print("\n=====================================================")
    print("ALL BATCHES HAVE BEEN PROCESSED.")
    print(f"Total execution time: {total_time / 60:.2f} minutes.")
    print(f"Log files for each batch are located in: '{output_base_dir / 'logs'}'")
    print("=====================================================")

if __name__ == "__main__":
    try:
        from rdkit import Chem
    except ImportError:
        print("RDKit is not installed. Please install it first.")
        print("Installation: conda install -c conda-forge rdkit")
        exit()

    mp.freeze_support()
    main()