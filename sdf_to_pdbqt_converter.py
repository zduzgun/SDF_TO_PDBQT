#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import multiprocessing as mp
import queue
from pathlib import Path
import time
import logging
from datetime import datetime
import shutil

# =============================================================================
# CONFIGURATION SECTION - MODIFY THESE VARIABLES
# =============================================================================

# Processing mode for all batches
PROCESS_ALL_BATCHES = True  # Set to True to process all batch folders found in INPUT_BASE_DIR

# Specific batch folders to process (ONLY used if PROCESS_ALL_BATCHES is False)
# Example: TARGET_BATCHES = ["batch_0001", "batch_0002", "batch_0012"] 
TARGET_BATCHES = []  # Add specific batch names here when PROCESS_ALL_BATCHES = False

# Number of parallel processes (set to number of available cores)
# For Orfoz server with 55 cores, set this to 55
NUM_PROCESSES = 55

# Input and output directories
INPUT_BASE_DIR = "filtered_sdf_files" # Directory containing FILTERED batch folders
OUTPUT_BASE_DIR = "pdbqt_files"       # Directory where PDBQT files will be saved

# Minimization strategy (recommended: "balanced")
MINIMIZATION_STRATEGY = "balanced"   # Options: "fast", "balanced", "thorough"
# 
# Strategy Details:
# - "fast": Single-stage conjugate gradient (500 steps)
#   * Processing time: ~30-60 seconds per compound
#   * Quality: Good for removing major clashes
#   * Use case: Large libraries (>50k compounds), quick screening
#
# - "balanced": Two-stage optimization (500 SD + 1000 CG steps) [RECOMMENDED]
#   * Processing time: ~60-120 seconds per compound  
#   * Quality: High quality structures suitable for docking
#   * Use case: Most molecular docking projects, best quality/speed balance
#
# - "thorough": Extended two-stage optimization (1000 SD + 2000 CG steps)
#   * Processing time: ~120-300 seconds per compound
#   * Quality: Maximum quality, literature-standard minimization
#   * Use case: High-precision studies, lead optimization, publication quality

# Test mode settings
TEST_MODE = False                    # Set to True for testing with limited files
TEST_SINGLE_BATCH = "batch_0012"   # Only process this batch in test mode (set to None to test all batches)
TEST_FILE_COUNT = 100               # Number of files to process in test mode
TEST_PROCESSES = 4                  # Number of processes for testing (lower for easier debugging)

# SLURM/Non-interactive mode settings
AUTO_RUN_MODE = "full"              # Options: "test", "full", "skip_menu"
# - "test": Automatically run with TEST_FILE_COUNT and TEST_PROCESSES on TEST_SINGLE_BATCH
# - "full": Automatically run full conversion with NUM_PROCESSES on all batches
# - "skip_menu": Show interactive menu (for manual runs)

# Resume functionality
RESUME_MODE = True                  # Skip batches that are already completed
OVERWRITE_EXISTING = False          # Set to True to overwrite existing PDBQT files

# Progress reporting
PROGRESS_REPORT_FREQUENCY = 100     # Report progress every N files
SAVE_PROGRESS_LOG = True           # Save detailed progress log for each batch

# =============================================================================
# END CONFIGURATION SECTION
# =============================================================================

def setup_logging(log_dir, batch_name=None):
    """
    Setup logging configuration for specific batch or general processing
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if batch_name:
        log_file = log_dir / f"conversion_log_{batch_name}_{timestamp}.log"
    else:
        log_file = log_dir / f"multi_batch_conversion_{timestamp}.log"
    
    # Clear any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_openbabel():
    """
    Check if OpenBabel is available for 3D generation and minimization
    """
    try:
        # Use -V for version check, which is more standard and reliable
        result = subprocess.run(['obabel', '-V'], 
                              capture_output=True, text=True, timeout=10)
        
        # Combine stdout and stderr to catch version info wherever it's printed
        full_output = (result.stdout.strip() + " " + result.stderr.strip()).strip()
        
        if "Open Babel" in full_output:
            logging.info(f"OpenBabel check successful: {full_output}")
            return True
        else:
            # Provide more detailed error info if the check fails
            logging.error("OpenBabel version check failed. Could not find 'Open Babel' string in output.")
            logging.error("Command executed: obabel -V")
            logging.error(f"stdout: {result.stdout.strip()}")
            logging.error(f"stderr: {result.stderr.strip()}")
            return False
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        logging.error("OpenBabel not found. Please install OpenBabel first.")
        logging.error("Installation: conda install -c conda-forge openbabel>=3.1.0")
        return False

def get_batch_folders(input_base_dir):
    """
    Get all batch folders from input directory
    """
    input_path = Path(input_base_dir)
    if not input_path.exists():
        logging.error(f"Input directory does not exist: {input_path}")
        return []
    
    batch_folders = []
    for item in input_path.iterdir():
        if item.is_dir() and item.name.startswith('batch_'):
            batch_folders.append(item)
    
    return sorted(batch_folders)

def check_batch_completion(batch_folder, output_base_dir):
    """
    Check if a batch has already been processed
    """
    output_folder = output_base_dir / batch_folder.name
    if not output_folder.exists():
        return False, 0, 0
    
    sdf_files = list(batch_folder.glob("*.sdf"))
    pdbqt_files = list(output_folder.glob("*.pdbqt"))
    
    total_sdf = len(sdf_files)
    total_pdbqt = len(pdbqt_files)
    
    # Consider batch completed if 95% or more files are converted
    completion_rate = total_pdbqt / total_sdf if total_sdf > 0 else 0
    is_completed = completion_rate >= 0.95
    
    return is_completed, total_sdf, total_pdbqt

def convert_single_file(args):
    """
    Convert a single SDF file to PDBQT format with balanced 2-stage minimization
    Args: tuple (input_file_path, output_file_path, strategy, process_id)
    Returns: tuple (success, input_file, error_message, processing_time, process_id)
    """
    input_file, output_file, strategy, process_id = args
    start_time = time.time()
    
    # Skip if file already exists and not overwriting
    if not OVERWRITE_EXISTING and output_file.exists() and output_file.stat().st_size > 0:
        processing_time = time.time() - start_time
        return True, input_file.name, "Already exists (skipped)", processing_time, process_id
    
    try:
        # Create temporary intermediate file for 3D generation
        temp_3d_file = output_file.with_suffix(f'.temp_3d_p{process_id}.sdf')
        
        # Step 1: 2D to 3D conversion with fallback mechanism
        gen3d_success = False
        error_msg_step1 = ""

        # METHOD 1: --gen3D (Fast and standard)
        step1a_cmd = [
            'obabel', str(input_file), '-O', str(temp_3d_file),
            '--gen3D',
            '-h',
            '--ff', 'MMFF94s'
        ]
        result1a = subprocess.run(step1a_cmd, capture_output=True, text=True, timeout=180)
        
        if result1a.returncode == 0 and temp_3d_file.exists() and temp_3d_file.stat().st_size > 0:
            gen3d_success = True
        else:
            error_msg_step1 += f"gen3D failed: {result1a.stderr.strip() if result1a.stderr else 'Error'}. "
            
            # METHOD 2: --build (Slower but more systematic fallback)
            step1b_cmd = [
                'obabel', str(input_file), '-O', str(temp_3d_file),
                '--build',
                '-h',
                '--ff', 'MMFF94s'
            ]
            result1b = subprocess.run(step1b_cmd, capture_output=True, text=True, timeout=300)
            if result1b.returncode == 0 and temp_3d_file.exists() and temp_3d_file.stat().st_size > 0:
                gen3d_success = True
            else:
                error_msg_step1 += f"Build failed: {result1b.stderr.strip() if result1b.stderr else 'Error'}."

        if not gen3d_success:
            return False, input_file.name, f"Step 1 (3D gen): {error_msg_step1}", 0, process_id
        
        # Step 2: Energy minimization based on strategy
        if strategy == "fast":
            step2_cmd = ['obminimize', '-ff', 'MMFF94s', '-cg', '-n', '500', str(temp_3d_file)]
            result2 = subprocess.run(step2_cmd, capture_output=True, text=True, timeout=180)
            if result2.returncode != 0:
                return False, input_file.name, f"Step 2 (fast min): {result2.stderr.strip()}", 0, process_id
        
        elif strategy == "balanced":
            step2a_cmd = ['obminimize', '-ff', 'MMFF94s', '-sd', '-n', '500', str(temp_3d_file)]
            result2a = subprocess.run(step2a_cmd, capture_output=True, text=True, timeout=180)
            if result2a.returncode != 0:
                return False, input_file.name, f"Step 2a (SD): {result2a.stderr.strip()}", 0, process_id
            
            step2b_cmd = ['obminimize', '-ff', 'MMFF94s', '-cg', '-n', '1000', str(temp_3d_file)]
            result2b = subprocess.run(step2b_cmd, capture_output=True, text=True, timeout=300)
            if result2b.returncode != 0:
                return False, input_file.name, f"Step 2b (CG): {result2b.stderr.strip()}", 0, process_id
        
        elif strategy == "thorough":
            step2a_cmd = ['obminimize', '-ff', 'MMFF94s', '-sd', '-n', '1000', str(temp_3d_file)]
            result2a = subprocess.run(step2a_cmd, capture_output=True, text=True, timeout=300)
            if result2a.returncode != 0:
                return False, input_file.name, f"Step 2a (SD): {result2a.stderr.strip()}", 0, process_id
            
            step2b_cmd = ['obminimize', '-ff', 'MMFF94s', '-cg', '-n', '2000', str(temp_3d_file)]
            result2b = subprocess.run(step2b_cmd, capture_output=True, text=True, timeout=300)
            if result2b.returncode != 0:
                return False, input_file.name, f"Step 2b (CG): {result2b.stderr.strip()}", 0, process_id
        
        # Step 3: Convert minimized SDF to PDBQT format
        python2_success = False
        try:
            # First try with prepare_ligand4.py
            step3_cmd = ['python2', 'prepare_ligand4.py', '-l', str(temp_3d_file), '-o', str(output_file), '-A', 'hydrogens', '-U', 'nphs_lps', '-v']
            result3 = subprocess.run(step3_cmd, capture_output=True, text=True, timeout=120)
            if result3.returncode == 0 and output_file.exists() and output_file.stat().st_size > 0:
                python2_success = True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass # Fallback to obabel
        
        if not python2_success:
            # Fallback to Open Babel PDBQT conversion
            step3_cmd = ['obabel', str(temp_3d_file), '-O', str(output_file), '-p', '7.4', '--partialcharge', 'gasteiger', '-h']
            result3 = subprocess.run(step3_cmd, capture_output=True, text=True, timeout=120)
            if result3.returncode != 0:
                return False, input_file.name, f"Step 3 (PDBQT Fallback): {result3.stderr.strip()}", 0, process_id
        
        try:
            temp_3d_file.unlink() # Clean up temporary file
        except FileNotFoundError:
            pass
        
        # Step 4: Assume success if PDBQT file was created and is not empty.
        if output_file.exists() and output_file.stat().st_size > 0:
            processing_time = time.time() - start_time
            return True, input_file.name, None, processing_time, process_id
        else:
            return False, input_file.name, "Final PDBQT file not created or is empty.", 0, process_id            
    except subprocess.TimeoutExpired:
        return False, input_file.name, "Processing timeout", 0, process_id
    except Exception as e:
        return False, input_file.name, f"Unexpected error: {str(e)}", 0, process_id

def progress_monitor(total_files, result_queue, logger, batch_name):
    """
    Monitor and report progress in real-time
    """
    completed = 0
    successful = 0
    failed = 0
    skipped = 0
    total_time = 0
    start_time = time.time()
    
    logger.info(f"Processing {total_files} files in {batch_name}...")
    
    while completed < total_files:
        try:
            success, filename, error, proc_time, process_id = result_queue.get(timeout=30)
            completed += 1
            total_time += proc_time
            
            if success:
                if error and "Already exists" in error:
                    skipped += 1
                else:
                    successful += 1
            else:
                failed += 1
                logger.error(f"Process {process_id}: Failed to convert {filename}: {error}")
            
            # Report progress
            if completed % PROGRESS_REPORT_FREQUENCY == 0 or completed in [1, 10, 50] or completed == total_files:
                elapsed_time = time.time() - start_time
                rate = completed / elapsed_time if elapsed_time > 0 else 0
                eta = (total_files - completed) / rate if rate > 0 else 0
                avg_time = total_time / completed if completed > 0 else 0
                
                progress_message = (
                    f"PROGRESS [{batch_name}]: [{completed}/{total_files}] | "
                    f"Success: {successful}, Failed: {failed}, Skipped: {skipped} | "
                    f"Rate: {rate:.1f} f/s | Avg: {avg_time:.2f} s/f | ETA: {eta/60:.1f} min"
                )
                logger.info(progress_message)
        
        except queue.Empty:
            if not any(p.is_alive() for p in mp.active_children()):
                if completed < total_files:
                    logger.warning(f"All worker processes terminated for {batch_name}, but not all tasks are complete.")
                break
            continue
    
    total_elapsed = time.time() - start_time
    
    logger.info("="*50 + f" {batch_name} SUMMARY " + "="*50)
    logger.info(f"Batch {batch_name} completed in {total_elapsed/60:.2f} minutes")
    logger.info(f"Successfully converted: {successful} files")
    logger.info(f"Failed conversions: {failed} files")
    logger.info(f"Skipped (already exist): {skipped} files")
    if successful + failed + skipped > 0:
        logger.info(f"Success rate: {successful/(successful+failed+skipped)*100:.1f}%")
    if total_elapsed > 0:
        logger.info(f"Throughput: {total_files/total_elapsed:.2f} files/second")
    logger.info("="*120)
    
    return successful, failed, skipped, total_elapsed

def worker_process(task_queue, result_queue):
    """
    Worker process for parallel processing
    """
    while True:
        try:
            args = task_queue.get(timeout=10)
            if args is None:  # Poison pill to stop
                break
            result = convert_single_file(args)
            result_queue.put(result)
        except queue.Empty:
            break
        except Exception as e:
            break

def process_batch_folder_parallel(batch_folder, output_base_dir, num_processes, logger, file_limit=None):
    """
    Process all SDF files in a batch folder using maximum parallelization
    """
    output_folder = output_base_dir / batch_folder.name
    output_folder.mkdir(exist_ok=True)
    
    sdf_files = sorted(list(batch_folder.glob("*.sdf")))
    
    if file_limit:
        sdf_files = sdf_files[:file_limit]
    
    if not sdf_files:
        logger.warning(f"No SDF files found in {batch_folder}")
        return 0, 0, 0, 0
    
    total_files = len(sdf_files)
    
    logger.info(f"Found {total_files} SDF files in {batch_folder.name}")
    if file_limit:
        logger.info(f"Processing a limited subset of {len(sdf_files)} files for this run.")
    
    manager = mp.Manager()
    task_queue = manager.Queue()
    result_queue = manager.Queue()
    
    for i, sdf_file in enumerate(sdf_files):
        output_file = output_folder / f"{sdf_file.stem}.pdbqt"
        task_queue.put((sdf_file, output_file, MINIMIZATION_STRATEGY, i % num_processes))
    
    workers = []
    for i in range(num_processes):
        worker = mp.Process(target=worker_process, args=(task_queue, result_queue))
        worker.daemon = True
        worker.start()
        workers.append(worker)
    
    successful, failed, skipped, total_time = progress_monitor(total_files, result_queue, logger, batch_folder.name)
    
    for worker in workers:
        worker.join(timeout=10)
    
    return successful, failed, skipped, total_time

def main():
    """
    Main function to convert all batch folders to PDBQT format
    """
    # Setup main logging
    output_base_dir = Path(OUTPUT_BASE_DIR)
    output_base_dir.mkdir(exist_ok=True)
    logger = setup_logging(output_base_dir)
    
    # Display configuration
    logger.info("="*70)
    logger.info("SDF to PDBQT Multi-Batch Converter")
    logger.info("="*70)
    logger.info(f"Processing mode: {'All batches' if PROCESS_ALL_BATCHES else 'Selected batches'}")
    logger.info(f"Parallel processes: {NUM_PROCESSES}")
    logger.info(f"Input directory: {INPUT_BASE_DIR}")
    logger.info(f"Output directory: {OUTPUT_BASE_DIR}")
    logger.info(f"Minimization strategy: {MINIMIZATION_STRATEGY}")
    logger.info(f"Resume mode: {RESUME_MODE}")
    logger.info(f"Overwrite existing: {OVERWRITE_EXISTING}")
    if TEST_MODE:
        if TEST_SINGLE_BATCH:
            logger.info(f"Test mode: Only {TEST_SINGLE_BATCH} - {TEST_FILE_COUNT} files")
        else:
            logger.info(f"Test mode: {TEST_FILE_COUNT} files per batch")
    logger.info("="*70)
    
    # Check OpenBabel
    if not check_openbabel():
        logger.error("OpenBabel check failed. Exiting.")
        return
    
    # Get batch folders
    input_base_dir = Path(INPUT_BASE_DIR)
    all_batch_folders = get_batch_folders(input_base_dir)
    
    if not all_batch_folders:
        logger.error(f"No batch folders found in {input_base_dir}")
        return
    
    # Select batches to process
    if TEST_MODE and AUTO_RUN_MODE == "test" and TEST_SINGLE_BATCH:
        # Test mode: process only the specified single batch
        batch_path = input_base_dir / TEST_SINGLE_BATCH
        if batch_path.exists() and batch_path.is_dir():
            batches_to_process = [batch_path]
            logger.info(f"Test mode: Processing only {TEST_SINGLE_BATCH} with {TEST_FILE_COUNT} files")
        else:
            logger.error(f"Test batch folder not found: {TEST_SINGLE_BATCH}")
            return
    elif PROCESS_ALL_BATCHES:
        batches_to_process = all_batch_folders
        logger.info(f"Found {len(all_batch_folders)} batch folders to process")
    else:
        batches_to_process = []
        for batch_name in TARGET_BATCHES:
            batch_path = input_base_dir / batch_name
            if batch_path in all_batch_folders:
                batches_to_process.append(batch_path)
            else:
                logger.warning(f"Batch folder not found: {batch_name}")
        logger.info(f"Selected {len(batches_to_process)} batch folders to process")
    
    if not batches_to_process:
        logger.error("No valid batch folders to process")
        return
    
    # Process each batch
    total_successful = 0
    total_failed = 0
    total_skipped = 0
    total_processing_time = 0
    processed_batches = 0
    skipped_batches = 0
    
    start_time = time.time()
    
    for i, batch_folder in enumerate(batches_to_process, 1):
        logger.info(f"\n{'='*20} PROCESSING BATCH {i}/{len(batches_to_process)}: {batch_folder.name} {'='*20}")
        
        # Check if batch is already completed
        if RESUME_MODE:
            is_completed, sdf_count, pdbqt_count = check_batch_completion(batch_folder, output_base_dir)
            if is_completed:
                logger.info(f"Batch {batch_folder.name} already completed ({pdbqt_count}/{sdf_count} files). Skipping.")
                skipped_batches += 1
                continue
            elif pdbqt_count > 0:
                logger.info(f"Batch {batch_folder.name} partially completed ({pdbqt_count}/{sdf_count} files). Resuming.")
        
        # Process batch
        file_limit = TEST_FILE_COUNT if TEST_MODE else None
        processes_to_use = TEST_PROCESSES if TEST_MODE else NUM_PROCESSES
        
        successful, failed, skipped, batch_time = process_batch_folder_parallel(
            batch_folder, output_base_dir, processes_to_use, logger, file_limit
        )
        
        total_successful += successful
        total_failed += failed
        total_skipped += skipped
        total_processing_time += batch_time
        processed_batches += 1
        
        # Log batch completion
        logger.info(f"Batch {batch_folder.name} completed: {successful} successful, {failed} failed, {skipped} skipped")
    
    # Final summary
    total_elapsed = time.time() - start_time
    
    logger.info("\n" + "="*80)
    logger.info("MULTI-BATCH CONVERSION COMPLETE")
    logger.info("="*80)
    logger.info(f"Total batches processed: {processed_batches}")
    logger.info(f"Total batches skipped: {skipped_batches}")
    logger.info(f"Total wall-clock time: {total_elapsed/3600:.2f} hours")
    logger.info(f"Total processing time: {total_processing_time/3600:.2f} hours")
    logger.info(f"Total files converted: {total_successful}")
    logger.info(f"Total files failed: {total_failed}")
    logger.info(f"Total files skipped: {total_skipped}")
    if total_successful + total_failed + total_skipped > 0:
        logger.info(f"Overall success rate: {total_successful/(total_successful+total_failed+total_skipped)*100:.1f}%")
    if total_elapsed > 0:
        logger.info(f"Overall throughput: {(total_successful+total_failed+total_skipped)/total_elapsed:.2f} files/second")
    logger.info("="*80)

if __name__ == "__main__":
    mp.freeze_support()
    main()