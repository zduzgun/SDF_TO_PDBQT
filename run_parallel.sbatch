#!/bin/bash
#SBATCH -p debug
#SBATCH -A fdemirtaskorkmaz
#SBATCH -J pdbqt
#SBATCH -N 1
#SBATCH -C weka
#SBATCH --ntasks-per-node=1
#SBATCH --cpus-per-task=20
#SBATCH --time=0-04:00:00
#SBATCH --hint=nomultithread

echo "Job started on $(hostname) at $(date)"
echo "Allocated CPUs: $SLURM_CPUS_PER_TASK"

# =============================================================================
#                            CONFIGURATION SETTINGS
#   Orijinal betikteki tüm ayarlar buraya taþýndý ve korundu.
# =============================================================================

# "full" veya "test"
RUN_MODE="full"

# --- "full" mod ayarlarý ---
PROCESS_ALL_BATCHES=True
TARGET_BATCHES=("batch_0001" "batch_0002") # Eðer PROCESS_ALL_BATCHES=False ise bu kullanýlýr
NUM_PROCESSES=$SLURM_CPUS_PER_TASK # SLURM'dan otomatik alýnýyor, elle deðiþtirebilirsiniz

# --- "test" mod ayarlarý ---
TEST_SINGLE_BATCH="batch_0012"
TEST_FILE_COUNT=100

# --- Genel Ayarlar ---
INPUT_BASE_DIR="filtered_sdf_files"
OUTPUT_BASE_DIR="pdbqt_files"
MINIMIZATION_STRATEGY="balanced" # fast, balanced, thorough
RESUME_MODE=True                 # True or False
OVERWRITE_EXISTING=False         # True or False

# =============================================================================
#                        END OF CONFIGURATION SECTION
# =============================================================================

# Yönetici betik mantýðý baþlýyor

# Overwrite argümanýný Python betiðine uygun hale getir
overwrite_arg=""
if [ "$OVERWRITE_EXISTING" = "True" ]; then
    overwrite_arg="--overwrite"
fi

# Ýþlenecek dosya listesini ve iþlemci sayýsýný belirle
file_list_command=""
jobs_to_run=0

if [ "$RUN_MODE" = "test" ]; then
    echo "--- RUNNING IN TEST MODE ---"
    test_batch_path="$INPUT_BASE_DIR/$TEST_SINGLE_BATCH"
    if [ ! -d "$test_batch_path" ]; then
        echo "ERROR: Test batch directory not found: $test_batch_path"
        exit 1
    fi
    # Test modu için dosya listesi komutu (sadece N dosya al)
    file_list_command="find $test_batch_path -type f -name '*.sdf' | head -n $TEST_FILE_COUNT"
    jobs_to_run=4 # Test için güvenli iþlemci sayýsý
else
    echo "--- RUNNING IN FULL MODE ---"
    if [ "$PROCESS_ALL_BATCHES" = "True" ]; then
        # Tüm batch klasörlerini iþle
        search_dirs_str=$(find $INPUT_BASE_DIR -mindepth 1 -maxdepth 1 -type d -name 'batch_*' | tr '\n' ' ')
        eval "search_dirs=($search_dirs_str)"
    else
        # Sadece hedef batch klasörlerini iþle
        for batch in "${TARGET_BATCHES[@]}"; do
            search_dirs+=("$INPUT_BASE_DIR/$batch")
        done
    fi
    file_list_command="find ${search_dirs[@]} -type f -name '*.sdf'"
    jobs_to_run=$NUM_PROCESSES
fi

echo "Number of parallel jobs set to: $jobs_to_run"

# Çýktý ana dizinini oluþtur
mkdir -p $OUTPUT_BASE_DIR

# --- GNU PARALLEL ÝLE ÝÞLEME ---

# Ýþlenecek dosyalarý bul
# Not: find komutunu bir deðiþkene atamak yerine doðrudan pipe ile parallel'e vermek
# büyük dosya listeleri için daha verimlidir.
eval $file_list_command |
    # --joblog: Hangi komutun baþarýlý/baþarýsýz olduðunu loglar. Hata ayýklama için harika.
    # --eta: Kalan süre tahmini verir.
    # --bar: Görsel ilerleme çubuðu ekler.
    parallel \
        -j $jobs_to_run \
        --eta --bar \
        --joblog parallel_joblog.log \
    '
    # {} -> parallel tarafýndan verilen tam girdi dosya yolu
    inputfile="{}"

    # Çýktý dosya yolunu girdiden türet
    # Örn: filtered_sdf_files/batch_0001/chem.sdf -> pdbqt_files/batch_0001/chem.pdbqt
    relative_path=${inputfile#$INPUT_BASE_DIR/}
    outputfile="'$OUTPUT_BASE_DIR'/${relative_path%.sdf}.pdbqt"

    # --resume özelliði GNU Parallel tarafýndan yönetiliyor,
    # --joblog dosyasýna bakarak tamamlanan iþleri tekrar çalýþtýrmaz.
    # Bizim RESUME_MODE ayarýmýz ise batch bazýnda atlamak için kullanýlabilir,
    # ancak parallel'in kendi devam etme özelliði daha verimlidir.

    # Ýþçi betiðini çalýþtýr
    python3 worker.py \
        --input-file "$inputfile" \
        --output-file "$outputfile" \
        --strategy "'$MINIMIZATION_STRATEGY'" \
        '$overwrite_arg'
    '

echo "Job finished at $(date)"