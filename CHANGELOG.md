# Changelog

Bu dosya, SDF to PDBQT Converter projesindeki tüm önemli değişiklikleri kaydeder.

Format [Keep a Changelog](https://keepachangelog.com/tr/1.0.0/) standardına uyar.

## [Unreleased]

### Added
- GitHub repository yapısı
- Kapsamlı dokümantasyon
- Test framework hazırlığı
- CI/CD pipeline hazırlığı

### Changed
- Kod organizasyonu iyileştirildi
- Dokümantasyon güncellendi

## [1.0.0] - 2024-12-01

### Added
- **SDF Splitter**: Büyük SDF dosyalarını batch'lere bölme
- **Molekül Filtreleme**: Rotatable bond sayısına göre filtreleme
- **PDBQT Dönüştürücü**: SDF'den PDBQT'ye dönüştürme
- **Worker Script**: Tek dosya dönüştürme
- **SLURM Scripts**: HPC cluster desteği
  - `md_debug.slurm`: Debug modu
  - `md_orfoz.slurm`: Orfoz cluster
  - `md_barbun.slurm`: Barbun cluster
- **GNU Parallel**: Paralel işleme desteği
- **Kapsamlı Loglama**: Detaylı hata ve işlem logları
- **Resume Özelliği**: Kesinti durumunda devam etme
- **Çoklu Minimizasyon Stratejileri**:
  - Fast: Tek aşamalı (500 adım)
  - Balanced: İki aşamalı (500 SD + 1000 CG) **[ÖNERİLEN]**
  - Thorough: Genişletilmiş (1000 SD + 2000 CG)

### Features
- **Büyük Ölçekli İşleme**: 100,000+ molekül işleyebilir
- **Paralel İşleme**: Çoklu CPU core desteği
- **Hata Yönetimi**: Kapsamlı hata yakalama ve raporlama
- **Performans Optimizasyonu**: Memory ve CPU kullanımı optimize edildi
- **HPC Uyumlu**: SLURM cluster sistemleri için optimize edildi

### Technical Details
- **Python 3.7+** desteği
- **RDKit** entegrasyonu
- **OpenBabel 3.1.0+** entegrasyonu
- **Multiprocessing** desteği
- **Pathlib** kullanımı
- **Logging** framework'ü

### Performance
- **İşleme Hızı**: ~60-120 saniye/molekül (balanced strateji)
- **Başarı Oranı**: %85-95
- **Memory Kullanımı**: Optimize edilmiş
- **CPU Kullanımı**: Paralel işleme ile maksimum verim

### Cluster Support
- **Orfoz Cluster**: 55 core, 128GB RAM
- **Barbun Cluster**: 40 core, 128GB RAM
- **Debug Mode**: 20 core, test için

### File Formats
- **Input**: SDF (Structure Data File)
- **Output**: PDBQT (AutoDock format)
- **Intermediate**: 3D SDF (geçici)

### Configuration
- **Rotatable Bond Threshold**: 15 (varsayılan)
- **Compounds per Folder**: 10,000 (varsayılan)
- **Process Count**: Otomatik tespit
- **Minimization Strategy**: Balanced (varsayılan)

## [0.9.0] - 2024-11-15

### Added
- İlk beta sürüm
- Temel SDF to PDBQT dönüştürme
- Basit paralel işleme

### Known Issues
- Memory leak sorunları
- Hata yönetimi eksik
- Dokümantasyon yetersiz

---

## Sürüm Numaralandırma

Bu proje [Semantic Versioning](https://semver.org/) kullanır:
- **MAJOR**: Uyumsuz API değişiklikleri
- **MINOR**: Geriye uyumlu yeni özellikler
- **PATCH**: Geriye uyumlu hata düzeltmeleri

## Katkıda Bulunanlar

- TR-GRID Team - İlk geliştirme ve sürüm 1.0.0
- TR-GRID Community - Test ve geri bildirim

## Lisans

Bu proje MIT lisansı altında lisanslanmıştır. 