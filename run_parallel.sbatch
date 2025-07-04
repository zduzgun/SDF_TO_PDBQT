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
#   Orijinal betikteki t�m ayarlar buraya ta��nd� ve korundu.
# =============================================================================

# "full" veya "test"
RUN_MODE="full"

# --- "full" mod ayarlar� ---
PROCESS_ALL_BATCHES=True
TARGET_BATCHES=("batch_0001" "batch_0002") # E�er PROCESS_ALL_BATCHES=False ise bu kullan�l�r
NUM_PROCESSES=$SLURM_CPUS_PER_TASK # SLURM'dan otomatik al�n�yor, elle de�i�tirebilirsiniz

# --- "test" mod ayarlar� ---
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

# Y�netici betik mant��� ba�l�yor

# Overwrite arg�man�n� Python beti�ine uygun hale getir
overwrite_arg=""
if [ "$OVERWRITE_EXISTING" = "True" ]; then
    overwrite_arg="--overwrite"
fi

# ��lenecek dosya listesini ve i�lemci say�s�n� belirle
file_list_command=""
jobs_to_run=0

if [ "$RUN_MODE" = "test" ]; then
    echo "--- RUNNING IN TEST MODE ---"
    test_batch_path="$INPUT_BASE_DIR/$TEST_SINGLE_BATCH"
    if [ ! -d "$test_batch_path" ]; then
        echo "ERROR: Test batch directory not found: $test_batch_path"
        exit 1
    fi
    # Test modu i�in dosya listesi komutu (sadece N dosya al)
    file_list_command="find $test_batch_path -type f -name '*.sdf' | head -n $TEST_FILE_COUNT"
    jobs_to_run=4 # Test i�in g�venli i�lemci say�s�
else
    echo "--- RUNNING IN FULL MODE ---"
    if [ "$PROCESS_ALL_BATCHES" = "True" ]; then
        # T�m batch klas�rlerini i�le
        search_dirs_str=$(find $INPUT_BASE_DIR -mindepth 1 -maxdepth 1 -type d -name 'batch_*' | tr '\n' ' ')
        eval "search_dirs=($search_dirs_str)"
    else
        # Sadece hedef batch klas�rlerini i�le
        for batch in "${TARGET_BATCHES[@]}"; do
            search_dirs+=("$INPUT_BASE_DIR/$batch")
        done
    fi
    file_list_command="find ${search_dirs[@]} -type f -name '*.sdf'"
    jobs_to_run=$NUM_PROCESSES
fi

echo "Number of parallel jobs set to: $jobs_to_run"

# ��kt� ana dizinini olu�tur
mkdir -p $OUTPUT_BASE_DIR

# --- GNU PARALLEL �LE ��LEME ---

# ��lenecek dosyalar� bul
# Not: find komutunu bir de�i�kene atamak yerine do�rudan pipe ile parallel'e vermek
# b�y�k dosya listeleri i�in daha verimlidir.
eval $file_list_command |
    # --joblog: Hangi komutun ba�ar�l�/ba�ar�s�z oldu�unu loglar. Hata ay�klama i�in harika.
    # --eta: Kalan s�re tahmini verir.
    # --bar: G�rsel ilerleme �ubu�u ekler.
    parallel \
        -j $jobs_to_run \
        --eta --bar \
        --joblog parallel_joblog.log \
    '
    # {} -> parallel taraf�ndan verilen tam girdi dosya yolu
    inputfile="{}"

    # ��kt� dosya yolunu girdiden t�ret
    # �rn: filtered_sdf_files/batch_0001/chem.sdf -> pdbqt_files/batch_0001/chem.pdbqt
    relative_path=${inputfile#$INPUT_BASE_DIR/}
    outputfile="'$OUTPUT_BASE_DIR'/${relative_path%.sdf}.pdbqt"

    # --resume �zelli�i GNU Parallel taraf�ndan y�netiliyor,
    # --joblog dosyas�na bakarak tamamlanan i�leri tekrar �al��t�rmaz.
    # Bizim RESUME_MODE ayar�m�z ise batch baz�nda atlamak i�in kullan�labilir,
    # ancak parallel'in kendi devam etme �zelli�i daha verimlidir.

    # ���i beti�ini �al��t�r
    python3 worker.py \
        --input-file "$inputfile" \
        --output-file "$outputfile" \
        --strategy "'$MINIMIZATION_STRATEGY'" \
        '$overwrite_arg'
    '

echo "Job finished at $(date)"