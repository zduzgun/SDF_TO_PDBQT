#!/bin/bash
#SBATCH -p debug
#SBATCH -A fdemirtaskorkmaz
#SBATCH -J tar
#SBATCH -N 1
#SBATCH -C weka
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=20
#SBATCH --time=0-04:00:00
#SBATCH --hint=nomultithread

echo "SLURM_NODELIST: $SLURM_NODELIST"
echo "ALLOCATED CPUS: $SLURM_CPUS_PER_TASK"

export OMP_NUM_THREADS=$SLURM_CPUS_PER_TASK
unset SLURM_CPU_BIND


# Ýþi Baþlat
#du -sh -- */

#tar xvjf BAP_2020.tar.bz2

#python sdf_splitter.py

#python sdf_to_pdbqt_converter.py

#python analyze_and_filter_sdf.py

# Tüm batch'leri poap_pdbqt klasörü altýnda organize et
mkdir -p poap_pdbqt
for batch in filtered_sdf_files/batch_*; do
    batch_name=$(basename "$batch")
    echo "Processing $batch_name..."
    ./poap_wrapper.sh -i "$batch" -o "./poap_pdbqt/$batch_name" -j 20
done