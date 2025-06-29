#!/bin/bash
#SBATCH -p orfoz
#SBATCH -A fdemirtaskorkmaz
#SBATCH -J pdbqt_conversion
#SBATCH -N 1
#SBATCH -C weka
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=55
#SBATCH --time=1-00:00:00
#SBATCH --hint=nomultithread
#SBATCH --mem=128G
#SBATCH -o pdbqt_conversion_%j.out
#SBATCH -e pdbqt_conversion_%j.err

# === SLURM Environment Info ===
echo "=========================================="
echo "SLURM Job Started: $(date)"
echo "SLURM_NODELIST: $SLURM_NODELIST"
echo "ALLOCATED CPUS: $SLURM_CPUS_PER_TASK"
echo "SLURM_JOB_ID: $SLURM_JOB_ID"
echo "Working Directory: $(pwd)"
echo "Partition: orfoz"
echo "=========================================="

# === Environment Setup ===
export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
unset SLURM_CPU_BIND

# Conda environment'ý aktifleþtir (gerekirse)
# source ~/.bashrc
# conda activate docking_env

# === Pre-processing Steps ===
echo "Starting preprocessing..."
#du -sh -- */
#tar xvjf BAP_2020.tar.bz2
#python sdf_splitter.py
#python sdf_to_pdbqt_converter.py
#python analyze_and_filter_sdf.py

# === Check Dependencies ===
echo "Checking dependencies..."
if ! command -v POAP_lig_refactored.bash &> /dev/null; then
    echo "ERROR: POAP_lig_refactored.bash not found in PATH"
    exit 1
fi

if [[ ! -f "./poap_wrapper.sh" ]]; then
    echo "ERROR: poap_wrapper.sh not found in current directory"
    exit 1
fi

# === Check Input Files ===
if [[ ! -d "filtered_sdf_files" ]]; then
    echo "ERROR: filtered_sdf_files directory not found"
    exit 1
fi

batch_count=$(find filtered_sdf_files -maxdepth 1 -type d -name "batch_*" | wc -l)
echo "Found $batch_count batch directories to process"

# === Main Processing ===
echo "=========================================="
echo "Starting POAP batch processing with $SLURM_CPUS_PER_TASK cores..."
echo "Processing settings:"
echo "  - Cluster: Orfoz"
echo "  - CPU cores: $SLURM_CPUS_PER_TASK"
echo "  - Memory: 128GB"
echo "  - 3D conversion: enabled (medium speed)"
echo "  - Minimization: enabled (CG, 2500 steps)"
echo "  - Output format: PDBQT"
echo "  - Parallel jobs per batch: $SLURM_CPUS_PER_TASK"
echo "=========================================="

start_time=$(date +%s)

# Create main output directory
mkdir -p poap_pdbqt

# Process each batch
batch_counter=0
total_sdf_files=0
total_processed_time=0

for batch in filtered_sdf_files/batch_*; do
    if [[ -d "$batch" ]]; then
        batch_counter=$((batch_counter + 1))
        batch_name=$(basename "$batch")
        
        echo ""
        echo "[$batch_counter/$batch_count] Processing $batch_name..."
        
        # Check SDF files in batch
        sdf_count=$(find "$batch" -name "*.sdf" | wc -l)
        total_sdf_files=$((total_sdf_files + sdf_count))
        echo "  SDF files to process: $sdf_count"
        
        batch_start=$(date +%s)
        
        # Run POAP wrapper with all available cores
        if ./poap_wrapper.sh -i "$batch" -o "./poap_pdbqt/$batch_name" -j $SLURM_CPUS_PER_TASK; then
            batch_end=$(date +%s)
            batch_duration=$((batch_end - batch_start))
            total_processed_time=$((total_processed_time + batch_duration))
            
            echo "  ? Successfully completed $batch_name in ${batch_duration}s"
            
            # Quick stats
            pdbqt_count=$(find "./poap_pdbqt/$batch_name/pdbqt" -name "*.pdbqt" 2>/dev/null | wc -l)
            error_count=$(find "./poap_pdbqt/$batch_name/errors" -name "*.sdf" 2>/dev/null | wc -l)
            success_rate=$((pdbqt_count * 100 / sdf_count))
            
            echo "    PDBQT files created: $pdbqt_count"
            echo "    Conversion errors: $error_count"
            echo "    Success rate: $success_rate%"
            echo "    Processing rate: $((sdf_count / batch_duration)) molecules/sec"
        else
            echo "  ? Failed to process $batch_name"
        fi
        
        echo "----------------------------------------"
        
        # Memory usage check
        if command -v free &> /dev/null; then
            echo "Current memory usage:"
            free -h | grep "Mem:"
        fi
    fi
done

# === Final Summary ===
end_time=$(date +%s)
total_duration=$((end_time - start_time))
hours=$((total_duration / 3600))
minutes=$(((total_duration % 3600) / 60))
seconds=$((total_duration % 60))

echo ""
echo "=========================================="
echo "POAP Batch Processing Completed!"
echo "=========================================="
echo "Job finished: $(date)"
echo "Total wall time: ${hours}h ${minutes}m ${seconds}s"
echo "Total processing time: ${total_processed_time}s"

# Generate final statistics
total_pdbqt=$(find poap_pdbqt -name "*.pdbqt" | wc -l)
total_errors=$(find poap_pdbqt -name "*.sdf" 2>/dev/null | wc -l)

if [[ $total_sdf_files -gt 0 ]]; then
    overall_success_rate=$((total_pdbqt * 100 / total_sdf_files))
    processing_rate=$((total_sdf_files / total_duration))
else
    overall_success_rate=0
    processing_rate=0
fi

echo ""
echo "Final Statistics:"
echo "================="
echo "  Cluster: Orfoz"
echo "  CPU cores used: $SLURM_CPUS_PER_TASK"
echo "  Memory allocated: 128GB"
echo "  Batches processed: $batch_counter"
echo "  Total SDF files: $total_sdf_files"
echo "  Total PDBQT files: $total_pdbqt"
echo "  Total errors: $total_errors"
echo "  Overall success rate: $overall_success_rate%"
echo "  Processing rate: $processing_rate molecules/sec"
echo "  Output directory: $(pwd)/poap_pdbqt"
echo "  Job ID: $SLURM_JOB_ID"

# System resource usage
echo ""
echo "Resource Usage Summary:"
echo "======================"
if [[ -f "/proc/$$/status" ]]; then
    max_rss=$(grep "VmHWM" /proc/$$/status 2>/dev/null | awk '{print $2}')
    if [[ -n "$max_rss" ]]; then
        max_rss_gb=$((max_rss / 1024 / 1024))
        echo "  Peak memory used: ${max_rss_gb}GB"
    fi
fi
echo "  CPU cores allocated: $SLURM_CPUS_PER_TASK"
echo "  Memory allocated: 128GB"
echo "  Weka file system: Used"

# Performance metrics
if [[ $total_duration -gt 0 && $total_sdf_files -gt 0 ]]; then
    cpu_hours=$((SLURM_CPUS_PER_TASK * total_duration / 3600))
    efficiency=$((total_pdbqt * 3600 / cpu_hours))
    echo "  CPU hours consumed: $cpu_hours"
    echo "  Molecules per CPU hour: $efficiency"
fi

echo ""
echo "Output Structure:"
echo "================"
echo "  poap_pdbqt/"
echo "  +¦¦ batch_0001/"
echo "  -   +¦¦ pdbqt/          # Converted PDBQT files"
echo "  -   +¦¦ processed/      # Original SDF files"
echo "  -   +¦¦ errors/         # Failed conversions"
echo "  -   L¦¦ conversion_summary.txt"
echo "  +¦¦ batch_0002/"
echo "  -   L¦¦ ..."
echo "  L¦¦ [additional batches]"

echo ""
echo "Next Steps:"
echo "==========="
echo "1. Check conversion summaries in each batch directory"
echo "2. Review error files if any conversions failed"
echo "3. PDBQT files are ready for docking simulations"
echo "4. Consider running quality checks on PDBQT files"

echo "=========================================="
echo "Job completed successfully on Orfoz cluster"
echo "=========================================="