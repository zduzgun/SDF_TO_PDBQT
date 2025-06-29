# Katkıda Bulunma Rehberi

TR-GRID SDF to PDBQT Converter projesine katkıda bulunmak istediğiniz için teşekkürler! Bu rehber, projeye nasıl katkıda bulunabileceğinizi açıklar.

## 🚀 Başlangıç

### Geliştirme Ortamını Kurma

1. **Repository'yi fork edin**
```bash
git clone https://github.com/YOUR_USERNAME/SDF_TO_PDBQT.git
cd SDF_TO_PDBQT
```

2. **Conda environment oluşturun**
```bash
conda env create -f environment.yml
conda activate sdf_pdbqt
```

3. **Geliştirme bağımlılıklarını yükleyin**
```bash
pip install -e .[dev]
```

## 📝 Katkı Türleri

### 🐛 Hata Raporlama

Hata raporlarken lütfen şunları dahil edin:
- İşletim sistemi ve Python versiyonu
- Tam hata mesajı ve stack trace
- Hatanın nasıl yeniden üretileceği
- Beklenen davranış

### 💡 Özellik İstekleri

Yeni özellik önerirken:
- Özelliğin amacını açıklayın
- Kullanım senaryosunu belirtin
- Varsa benzer özelliklerin örneklerini verin

### 🔧 Kod Katkıları

#### Kod Standartları

- **Python**: PEP 8 standartlarına uyun
- **Dokümantasyon**: Tüm fonksiyonlar için docstring yazın
- **Test**: Yeni özellikler için test yazın
- **Commit Mesajları**: Açıklayıcı commit mesajları kullanın

#### Kod Formatı

```bash
# Kod formatını kontrol edin
black .
flake8 .
mypy .
```

#### Test Çalıştırma

```bash
# Tüm testleri çalıştırın
pytest

# Coverage ile test çalıştırın
pytest --cov=.

# Belirli test dosyasını çalıştırın
pytest tests/test_sdf_splitter.py
```

## 🔄 Pull Request Süreci

### 1. Branch Oluşturma

```bash
git checkout -b feature/amazing-feature
# veya
git checkout -b fix/bug-fix
```

### 2. Değişiklikleri Yapma

- Kodunuzu yazın
- Testleri ekleyin
- Dokümantasyonu güncelleyin
- README.md'yi gerekirse güncelleyin

### 3. Commit ve Push

```bash
git add .
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

### 4. Pull Request Oluşturma

GitHub'da Pull Request oluşturun ve şunları dahil edin:
- Değişikliklerin açıklaması
- Test sonuçları
- Screenshot'lar (varsa)

## 📋 Commit Mesaj Formatı

[Conventional Commits](https://www.conventionalcommits.org/) standardını kullanın:

```
type(scope): description

feat: yeni özellik
fix: hata düzeltmesi
docs: dokümantasyon değişikliği
style: kod formatı değişikliği
refactor: kod refactoring
test: test ekleme/düzenleme
chore: bakım işleri
```

Örnekler:
- `feat(converter): add new minimization strategy`
- `fix(filter): resolve memory leak in batch processing`
- `docs(readme): update installation instructions`

## 🧪 Test Yazma

### Test Dosya Yapısı

```
tests/
├── test_sdf_splitter.py
├── test_analyze_and_filter_sdf.py
├── test_sdf_to_pdbqt_converter.py
└── test_worker.py
```

### Test Örnekleri

```python
import pytest
from pathlib import Path
from sdf_splitter import split_sdf_file

def test_split_sdf_file():
    """Test SDF dosyası bölme fonksiyonu"""
    # Test setup
    input_file = "test_data/sample.sdf"
    output_dir = "test_output"
    
    # Test execution
    split_sdf_file(input_file, output_dir, compounds_per_folder=100)
    
    # Assertions
    output_path = Path(output_dir)
    assert output_path.exists()
    assert len(list(output_path.glob("batch_*"))) > 0
```

## 📚 Dokümantasyon

### Docstring Formatı

```python
def process_molecules(input_file: str, output_dir: str) -> bool:
    """
    Molekülleri işler ve PDBQT formatına dönüştürür.
    
    Args:
        input_file (str): Giriş SDF dosyasının yolu
        output_dir (str): Çıktı klasörünün yolu
        
    Returns:
        bool: İşlem başarılı ise True, değilse False
        
    Raises:
        FileNotFoundError: Giriş dosyası bulunamazsa
        ValueError: Geçersiz parametreler verilirse
        
    Example:
        >>> success = process_molecules("data.sdf", "output/")
        >>> print(f"İşlem başarılı: {success}")
        İşlem başarılı: True
    """
    pass
```

## 🔍 Code Review Süreci

### Review Kriterleri

- **Fonksiyonellik**: Kod doğru çalışıyor mu?
- **Performans**: Kod verimli mi?
- **Güvenlik**: Güvenlik açığı var mı?
- **Okunabilirlik**: Kod anlaşılır mı?
- **Test Coverage**: Yeterli test var mı?

### Review Yorumları

- Yapıcı olun
- Spesifik öneriler verin
- Kod örnekleri kullanın
- Pozitif geri bildirim de verin

## 🚀 Sürüm Yayınlama

### Sürüm Numaralandırma

[Semantic Versioning](https://semver.org/) kullanın:
- `MAJOR.MINOR.PATCH`
- Örnek: `1.2.3`

### Release Süreci

1. **Changelog güncelleyin**
2. **Sürüm numarasını artırın**
3. **Release tag'i oluşturun**
4. **GitHub Release oluşturun**

## 📞 İletişim

- **GitHub Issues**: [Proje Issues](https://github.com/tr-grid/SDF_TO_PDBQT/issues)
- **Email**: info@tr-grid.org
- **Discord**: TR-GRID Discord sunucusu

## 🙏 Teşekkürler

Katkıda bulunan herkese teşekkürler! Projeyi daha iyi hale getirmek için çalıştığınız için minnettarız.

---

**Not**: Bu rehber, projenin ihtiyaçlarına göre güncellenebilir. Önerileriniz varsa lütfen GitHub Issues üzerinden paylaşın. 