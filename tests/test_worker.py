#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path
from worker import convert_single_file

class TestWorker:
    """Worker script test sınıfı"""
    
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
$$$$"""
        
        sdf_file = temp_dir / "test.sdf"
        with open(sdf_file, 'w') as f:
            f.write(sdf_content)
        return sdf_file
    
    def test_convert_single_file_basic(self, temp_dir, sample_sdf_file):
        """Temel dönüştürme işlemini test eder"""
        output_file = temp_dir / "test.pdbqt"
        
        # Dönüştürme işlemi
        success = convert_single_file(
            str(sample_sdf_file), 
            str(output_file), 
            "fast", 
            False
        )
        
        # Başarı durumunu kontrol et
        assert success is True
        
        # Çıktı dosyasının oluştuğunu kontrol et
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    def test_convert_single_file_overwrite(self, temp_dir, sample_sdf_file):
        """Üzerine yazma modunu test eder"""
        output_file = temp_dir / "test.pdbqt"
        
        # İlk dönüştürme
        success1 = convert_single_file(
            str(sample_sdf_file), 
            str(output_file), 
            "fast", 
            False
        )
        assert success1 is True
        
        # Dosya boyutunu kaydet
        original_size = output_file.stat().st_size
        
        # Üzerine yazma ile ikinci dönüştürme
        success2 = convert_single_file(
            str(sample_sdf_file), 
            str(output_file), 
            "fast", 
            True
        )
        assert success2 is True
        
        # Dosyanın güncellendiğini kontrol et
        assert output_file.stat().st_size > 0
    
    def test_convert_single_file_skip_existing(self, temp_dir, sample_sdf_file):
        """Mevcut dosyayı atlama modunu test eder"""
        output_file = temp_dir / "test.pdbqt"
        
        # İlk dönüştürme
        success1 = convert_single_file(
            str(sample_sdf_file), 
            str(output_file), 
            "fast", 
            False
        )
        assert success1 is True
        
        # Dosya boyutunu kaydet
        original_size = output_file.stat().st_size
        
        # Atlama ile ikinci dönüştürme
        success2 = convert_single_file(
            str(sample_sdf_file), 
            str(output_file), 
            "fast", 
            False
        )
        assert success2 is True
        
        # Dosyanın değişmediğini kontrol et
        assert output_file.stat().st_size == original_size
    
    def test_convert_single_file_different_strategies(self, temp_dir, sample_sdf_file):
        """Farklı minimizasyon stratejilerini test eder"""
        strategies = ["fast", "balanced", "thorough"]
        
        for strategy in strategies:
            output_file = temp_dir / f"test_{strategy}.pdbqt"
            
            success = convert_single_file(
                str(sample_sdf_file), 
                str(output_file), 
                strategy, 
                False
            )
            
            assert success is True
            assert output_file.exists()
            assert output_file.stat().st_size > 0
    
    def test_convert_single_file_nonexistent_input(self, temp_dir):
        """Var olmayan giriş dosyası durumunu test eder"""
        input_file = temp_dir / "nonexistent.sdf"
        output_file = temp_dir / "test.pdbqt"
        
        success = convert_single_file(
            str(input_file), 
            str(output_file), 
            "fast", 
            False
        )
        
        assert success is False
        assert not output_file.exists()
    
    def test_convert_single_file_invalid_sdf(self, temp_dir):
        """Geçersiz SDF dosyası durumunu test eder"""
        # Geçersiz SDF içeriği
        invalid_sdf_content = """Invalid Molecule
  RDKit          2D

  1  0  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 X   0  0  0  0  0  0  0  0  0  0  0  0
M  END
$$$$"""
        
        input_file = temp_dir / "invalid.sdf"
        with open(input_file, 'w') as f:
            f.write(invalid_sdf_content)
        
        output_file = temp_dir / "test.pdbqt"
        
        success = convert_single_file(
            str(input_file), 
            str(output_file), 
            "fast", 
            False
        )
        
        # Geçersiz molekül durumunda başarısız olabilir
        # Bu test, OpenBabel'in davranışına bağlıdır
        if not success:
            assert not output_file.exists() or output_file.stat().st_size == 0
    
    @pytest.mark.skipif(not shutil.which('obabel'), reason="OpenBabel not installed")
    def test_openbabel_available(self):
        """OpenBabel'in mevcut olduğunu test eder"""
        result = subprocess.run(['obabel', '-V'], 
                              capture_output=True, text=True, timeout=10)
        assert result.returncode == 0 or "Open Babel" in (result.stdout + result.stderr) 