#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import tempfile
import shutil
from pathlib import Path
from sdf_splitter import split_sdf_file, extract_database_id

class TestSDFSplitter:
    """SDF Splitter test sınıfı"""
    
    @pytest.fixture
    def temp_dir(self):
        """Geçici test dizini oluşturur"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_sdf_file(self, temp_dir):
        """Örnek SDF dosyası oluşturur"""
        sdf_content = """Molecule1
  RDKit          2D

  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
M  END
> <DATABASE_ID>
Molecule1
$$$$

Molecule2
  RDKit          2D

  2  1  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
M  END
> <DATABASE_ID>
Molecule2
$$$$"""
        
        sdf_file = temp_dir / "test.sdf"
        with open(sdf_file, 'w') as f:
            f.write(sdf_content)
        return sdf_file
    
    def test_extract_database_id(self):
        """DATABASE_ID çıkarma fonksiyonunu test eder"""
        compound_lines = [
            "Molecule1\n",
            "  RDKit          2D\n",
            "> <DATABASE_ID>\n",
            "Molecule1\n",
            "$$$$\n"
        ]
        
        database_id = extract_database_id(compound_lines)
        assert database_id == "Molecule1"
    
    def test_extract_database_id_not_found(self):
        """DATABASE_ID bulunamadığında None döndüğünü test eder"""
        compound_lines = [
            "Molecule1\n",
            "  RDKit          2D\n",
            "$$$$\n"
        ]
        
        database_id = extract_database_id(compound_lines)
        assert database_id is None
    
    def test_split_sdf_file_basic(self, temp_dir, sample_sdf_file):
        """Temel SDF bölme işlemini test eder"""
        output_dir = temp_dir / "output"
        
        # SDF dosyasını böl
        split_sdf_file(str(sample_sdf_file), str(output_dir), compounds_per_folder=1)
        
        # Çıktı dizininin oluştuğunu kontrol et
        assert output_dir.exists()
        
        # Batch klasörlerinin oluştuğunu kontrol et
        batch_dirs = list(output_dir.glob("batch_*"))
        assert len(batch_dirs) == 2  # 2 molekül, 1'er molekül per folder
        
        # Her batch'te doğru dosyaların olduğunu kontrol et
        for batch_dir in batch_dirs:
            sdf_files = list(batch_dir.glob("*.sdf"))
            assert len(sdf_files) == 1
    
    def test_split_sdf_file_multiple_compounds_per_folder(self, temp_dir, sample_sdf_file):
        """Birden fazla molekül per folder durumunu test eder"""
        output_dir = temp_dir / "output"
        
        # SDF dosyasını böl (2 molekül per folder)
        split_sdf_file(str(sample_sdf_file), str(output_dir), compounds_per_folder=2)
        
        # Çıktı dizininin oluştuğunu kontrol et
        assert output_dir.exists()
        
        # Tek batch klasörünün oluştuğunu kontrol et
        batch_dirs = list(output_dir.glob("batch_*"))
        assert len(batch_dirs) == 1
        
        # Batch'te 2 dosyanın olduğunu kontrol et
        sdf_files = list(batch_dirs[0].glob("*.sdf"))
        assert len(sdf_files) == 2
    
    def test_split_sdf_file_nonexistent_input(self, temp_dir):
        """Var olmayan giriş dosyası durumunu test eder"""
        output_dir = temp_dir / "output"
        nonexistent_file = temp_dir / "nonexistent.sdf"
        
        # Hata log dosyasının oluştuğunu kontrol et
        split_sdf_file(str(nonexistent_file), str(output_dir))
        
        error_log = output_dir / "error.log"
        assert error_log.exists()
        
        # Hata log içeriğini kontrol et
        with open(error_log, 'r') as f:
            content = f.read()
            assert "FILE_NOT_FOUND" in content
    
    def test_split_sdf_file_empty_input(self, temp_dir):
        """Boş SDF dosyası durumunu test eder"""
        output_dir = temp_dir / "output"
        
        # Boş SDF dosyası oluştur
        empty_sdf = temp_dir / "empty.sdf"
        with open(empty_sdf, 'w') as f:
            f.write("")
        
        # Boş dosya ile bölme işlemi
        split_sdf_file(str(empty_sdf), str(output_dir))
        
        # Çıktı dizininin oluştuğunu kontrol et
        assert output_dir.exists()
        
        # Batch klasörlerinin oluşmadığını kontrol et
        batch_dirs = list(output_dir.glob("batch_*"))
        assert len(batch_dirs) == 0 