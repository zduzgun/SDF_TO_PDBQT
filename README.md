# SDF to PDBQT Converter Pipeline

Bu proje, büyük ölçekli SDF (Structure Data File) formatındaki moleküler verileri PDBQT formatına dönüştürmek için geliştirilmiş kapsamlı bir pipeline'dır. Moleküler docking çalışmaları için optimize edilmiş moleküler yapıları üretir.

## 🚀 Özellikler

- **Büyük Ölçekli İşleme**: Binlerce molekülü paralel olarak işleyebilir
- **Akıllı Filtreleme**: Rotatable bond sayısına göre molekülleri filtreler
- **Çoklu Minimizasyon Stratejileri**: Fast, balanced ve thorough seçenekleri
- **HPC Uyumlu**: SLURM cluster sistemleri için optimize edilmiş
- **Hata Yönetimi**: Kapsamlı loglama ve hata raporlama
- **Resume Özelliği**: Kesinti durumunda kaldığı yerden devam edebilir

## 📋 Gereksinimler

### Yazılım Gereksinimleri
- Python 3.7+
- RDKit
- OpenBabel 3.1.0+
- GNU Parallel (opsiyonel, paralel işleme için)

### Python Paketleri
```bash
pip install rdkit-pypi
conda install -c conda-forge openbabel>=3.1.0
```

## 🏗️ Proje Yapısı

```
SDF_TO_PDBQT/
├── sdf_splitter.py              # Büyük SDF dosyalarını batch'lere böler
├── analyze_and_filter_sdf.py    # Molekülleri rotatable bond sayısına göre filtreler
├── sdf_to_pdbqt_converter.py    # Ana dönüştürme pipeline'ı
├── worker.py                    # Tek dosya dönüştürme worker'ı
├── run_parallel.sbatch          # GNU Parallel ile paralel işleme
├── md_barbun.slurm             # Barbun cluster için SLURM script
├── md_debug.slurm              # Debug modu için SLURM script
└── md_orfoz.slurm              # Orfoz cluster için SLURM script
```

## 🔧 Kurulum

1. **Repository'yi klonlayın:**
```bash
git clone https://github.com/kullaniciadi/SDF_TO_PDBQT.git
cd SDF_TO_PDBQT
```

2. **Gerekli paketleri yükleyin:**
```bash
conda create -n sdf_pdbqt python=3.9
conda activate sdf_pdbqt
conda install -c conda-forge rdkit openbabel>=3.1.0
```

3. **Test edin:**
```bash
python -c "from rdkit import Chem; print('RDKit OK')"
obabel -V
```

## 📖 Kullanım

### 1. SDF Dosyasını Bölme

Büyük SDF dosyasını yönetilebilir batch'lere bölün:

```bash
python sdf_splitter.py
```

**Konfigürasyon:**
- `compounds_per_folder`: Her klasördeki maksimum molekül sayısı (varsayılan: 10000)
- `output_base_dir`: Çıktı klasörü (varsayılan: "output")

### 2. Molekül Filtreleme

Rotatable bond sayısına göre molekülleri filtreleyin:

```bash
python analyze_and_filter_sdf.py
```

**Konfigürasyon:**
- `ROTATABLE_BOND_THRESHOLD`: Maksimum rotatable bond sayısı (varsayılan: 15)
- `NUM_PROCESSES`: Paralel işlem sayısı (varsayılan: 20)

### 3. PDBQT Dönüştürme

SDF dosyalarını PDBQT formatına dönüştürün:

```bash
python sdf_to_pdbqt_converter.py
```

**Minimizasyon Stratejileri:**
- `fast`: Tek aşamalı conjugate gradient (500 adım)
- `balanced`: İki aşamalı optimizasyon (500 SD + 1000 CG adım) **[ÖNERİLEN]**
- `thorough`: Genişletilmiş optimizasyon (1000 SD + 2000 CG adım)

### 4. HPC Cluster Kullanımı

#### SLURM ile Çalıştırma:

```bash
# Debug modu (4 saat)
sbatch md_debug.slurm

# Orfoz cluster (24 saat)
sbatch md_orfoz.slurm

# Barbun cluster (4 saat)
sbatch md_barbun.slurm
```

#### GNU Parallel ile Yerel Çalıştırma:

```bash
bash run_parallel.sbatch
```

## ⚙️ Konfigürasyon

### Ana Konfigürasyon Parametreleri

```python
# sdf_to_pdbqt_converter.py içinde
NUM_PROCESSES = 55              # İşlemci sayısı
INPUT_BASE_DIR = "filtered_sdf_files"
OUTPUT_BASE_DIR = "pdbqt_files"
MINIMIZATION_STRATEGY = "balanced"
RESUME_MODE = True
OVERWRITE_EXISTING = False
```

### Test Modu

```python
TEST_MODE = True
TEST_SINGLE_BATCH = "batch_0012"
TEST_FILE_COUNT = 100
TEST_PROCESSES = 4
```

## 📊 Performans

### Beklenen Performans (Orfoz Cluster)
- **CPU**: 55 core
- **Memory**: 128GB
- **İşleme Hızı**: ~60-120 saniye/molekül (balanced strateji)
- **Başarı Oranı**: %85-95

### Ölçeklenebilirlik
- **Küçük Kütüphane**: <10,000 molekül → 2-4 saat
- **Orta Kütüphane**: 10,000-100,000 molekül → 4-24 saat
- **Büyük Kütüphane**: >100,000 molekül → 24+ saat

## 🔍 Çıktı Formatları

### PDBQT Dosya Yapısı
```
pdbqt_files/
├── batch_0001/
│   ├── molecule1.pdbqt
│   ├── molecule2.pdbqt
│   └── ...
├── batch_0002/
└── ...
```

### Log Dosyaları
```
filtered_sdf_files/logs/
├── filter_log_batch_0001_20231201_143022.log
├── filter_log_batch_0002_20231201_143022.log
└── ...

pdbqt_files/logs/
├── conversion_log_batch_0001_20231201_143022.log
└── ...
```

## 🐛 Hata Ayıklama

### Yaygın Hatalar ve Çözümleri

1. **OpenBabel Bulunamadı:**
```bash
conda install -c conda-forge openbabel>=3.1.0
```

2. **RDKit Import Hatası:**
```bash
conda install -c conda-forge rdkit
```

3. **Memory Hatası:**
- `NUM_PROCESSES` değerini azaltın
- `MINIMIZATION_STRATEGY`'yi "fast" yapın

4. **Timeout Hatası:**
- `TEST_MODE = True` ile test edin
- Daha az dosya ile başlayın

## 📝 Loglama

Tüm işlemler detaylı loglar üretir:

- **Filtreleme Logları**: Hangi moleküllerin kabul/reddedildiği
- **Dönüştürme Logları**: Başarılı/başarısız dönüştürmeler
- **Hata Logları**: Detaylı hata mesajları ve stack trace'ler

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Commit yapın (`git commit -m 'Add some AmazingFeature'`)
4. Push yapın (`git push origin feature/AmazingFeature`)
5. Pull Request açın

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için `LICENSE` dosyasına bakın.

## 👥 Yazar

- **Zekeriya Duzgun** - *İlk geliştirme*

## 🙏 Teşekkürler

- RDKit geliştiricileri
- OpenBabel topluluğu
- TR-GRID altyapısı

## 📞 İletişim

Sorularınız için:
- GitHub Issues: [Proje Issues Sayfası](https://github.com/zduzgun/SDF_TO_PDBQT/issues)
- Email: [email@example.com]

---

**Not**: Bu pipeline, moleküler docking çalışmaları için optimize edilmiştir. Farklı kullanım senaryoları için konfigürasyon ayarlarını değiştirmeniz gerekebilir. 