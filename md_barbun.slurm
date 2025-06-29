#!/bin/bash
#SBATCH -p debug
#SBATCH -A fdemirtaskorkmaz
#SBATCH -J barbun_pdbqt_direct
#SBATCH -N 1
#SBATCH -C weka
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=40
#SBATCH --time=0-04:00:00
#SBATCH --hint=nomultithread
#SBATCH --mem=128G
#SBATCH -o barbun_direct_%j.out
#SBATCH -e barbun_direct_%j.err

echo "=========================================="
echo "BARBUN DIRECT SOLUTION - NO WRAPPER"
echo "Started: $(date)"
echo "=========================================="

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
unset SLURM_CPU_BIND

MAIN_DIR="$(pwd)"
OUTPUT_BASE="$MAIN_DIR/poap_pdbqt_final"
TEMP_BASE="$MAIN_DIR/temp_work"

mkdir -p "$OUTPUT_BASE"
mkdir -p "$TEMP_BASE"

echo "Main directory: $MAIN_DIR"
echo "Output directory: $OUTPUT_BASE" 
echo "Temp work directory: $TEMP_BASE"

# Process each batch
batch_counter=0
for batch in filtered_sdf_files/batch_*; do
    if [[ -d "$batch" ]]; then
        batch_counter=$((batch_counter + 1))
        batch_name=$(basename "$batch")
        
        echo ""
        echo "=== Processing $batch_name ==="
        
        # Create temp directory for this batch
        BATCH_TEMP="$TEMP_BASE/$batch_name"
        BATCH_OUTPUT="$OUTPUT_BASE/$batch_name"
        
        mkdir -p "$BATCH_TEMP"
        mkdir -p "$BATCH_OUTPUT"
        
        # Copy SDF files to temp
        sdf_count=$(find "$batch" -name "*.sdf" | wc -l)
        echo "Copying $sdf_count SDF files to temp directory..."
        find "$batch" -name "*.sdf" -exec cp {} "$BATCH_TEMP/" \;
        
        if [[ $sdf_count -eq 0 ]]; then
            echo "No SDF files found, skipping..."
            continue
        fi
        
        echo "Running POAP on temp directory..."
        echo "Temp input: $BATCH_TEMP"
        echo "Final output: $BATCH_OUTPUT"
        
        # Run POAP directly on temp directory
        start_time=$(date +%s)
        if POAP_lig_refactored.bash -t med -m cg 2500 -o pdbqt py -l "$BATCH_TEMP" -j $SLURM_CPUS_PER_TASK; then
            end_time=$(date +%s)
            duration=$((end_time - start_time))
            
            echo "POAP completed in ${duration}s"
            
            # Move outputs to final location
            echo "Moving outputs to final location..."
            
            # Create final subdirectories
            mkdir -p "$BATCH_OUTPUT/pdbqt" "$BATCH_OUTPUT/processed" "$BATCH_OUTPUT/errors"
            
            # Move PDBQT files
            if [[ -d "$BATCH_TEMP/pdbqt" ]]; then
                mv "$BATCH_TEMP/pdbqt"/* "$BATCH_OUTPUT/pdbqt/" 2>/dev/null || true
                pdbqt_count=$(find "$BATCH_OUTPUT/pdbqt" -name "*.pdbqt" | wc -l)
                echo "Moved $pdbqt_count PDBQT files"
            fi
            
            # Move processed files
            if [[ -d "$BATCH_TEMP/processed" ]]; then
                mv "$BATCH_TEMP/processed"/* "$BATCH_OUTPUT/processed/" 2>/dev/null || true
                processed_count=$(find "$BATCH_OUTPUT/processed" -name "*.sdf" | wc -l)
                echo "Moved $processed_count processed files"
            fi
            
            # Move error files
            if [[ -d "$BATCH_TEMP/pdbqt_error" ]]; then
                mv "$BATCH_TEMP/pdbqt_error"/* "$BATCH_OUTPUT/errors/" 2>/dev/null || true
                error_count=$(find "$BATCH_OUTPUT/errors" -name "*" | wc -l)
                echo "Moved $error_count error files"
            fi
            
            # Generate batch summary
            cat > "$BATCH_OUTPUT/batch_summary.txt" << EOF
Batch: $batch_name
Processed: $(date)
Duration: ${duration}s
Input SDF files: $sdf_count
PDBQT files: $pdbqt_count
Processed files: $processed_count
Errors: $error_count
Success rate: $((pdbqt_count * 100 / sdf_count))%
EOF
            
            echo "? $batch_name completed successfully"
            echo "   PDBQT: $pdbqt_count, Errors: $error_count"
            
        else
            echo "? POAP failed for $batch_name"
        fi
        
        # Clean up temp directory for this batch
        rm -rf "$BATCH_TEMP"
        echo "Cleaned up temp directory"
        
        echo "----------------------------------------"
    fi
done

# Clean up main temp directory
rm -rf "$TEMP_BASE"

# Final summary
echo ""
echo "=========================================="
echo "FINAL SUMMARY"
echo "=========================================="

total_batches=$(ls -1d "$OUTPUT_BASE"/batch_* 2>/dev/null | wc -l)
total_pdbqt=$(find "$OUTPUT_BASE" -name "*.pdbqt" 2>/dev/null | wc -l)
total_errors=$(find "$OUTPUT_BASE/*/errors" -name "*" 2>/dev/null | wc -l)

echo "Completed batches: $total_batches"
echo "Total PDBQT files: $total_pdbqt"
echo "Total errors: $total_errors"
echo "Output location: $OUTPUT_BASE"

echo ""
echo "Directory structure:"
ls -la "$OUTPUT_BASE"

echo ""
echo "Job completed: $(date)"
echo "=========================================="