#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import subprocess
from pathlib import Path
import sys
import logging

# Loglamayý basit tutuyoruz, çünkü her iþlem kendi logunu stderr'e yazabilir
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s', stream=sys.stderr)

def convert_single_file(input_sdf, output_pdbqt, strategy, overwrite):
    """
    Tek bir SDF dosyasýný, belirtilen strateji ile PDBQT formatýna dönüþtürür.
    Tüm özellikler korunmuþtur.
    """
    input_file = Path(input_sdf)
    output_file = Path(output_pdbqt)

    # 1. ÖZELLÝK KORUNDU: Üzerine Yazma (Overwrite) Modu
    if not overwrite and output_file.exists() and output_file.stat().st_size > 0:
        # print(f"Skipping existing file: {output_file.name}") # Isteðe baðlý: çok fazla log üretir
        return True

    # Çýktý klasörünün var olduðundan emin ol
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Her iþlem için benzersiz geçici dosya adý
    temp_3d_file = output_file.with_suffix(f'.{input_file.stem}.temp.sdf')

    try:
        # 2. ÖZELLÝK KORUNDU: 3D Oluþturma ve Yedek Mekanizma
        cmd_gen3d = ['obabel', str(input_file), '-O', str(temp_3d_file), '--gen3D', '-h', '--ff', 'MMFF94s']
        res_gen3d = subprocess.run(cmd_gen3d, capture_output=True, text=True, timeout=180)
        
        if not (res_gen3d.returncode == 0 and temp_3d_file.exists() and temp_3d_file.stat().st_size > 0):
            cmd_build = ['obabel', str(input_file), '-O', str(temp_3d_file), '--build', '-h', '--ff', 'MMFF94s']
            res_build = subprocess.run(cmd_build, capture_output=True, text=True, timeout=300)
            if not (res_build.returncode == 0 and temp_3d_file.exists()):
                logging.error(f"3D GEN FAILED for {input_file.name}: {res_build.stderr.strip() or res_gen3d.stderr.strip()}")
                return False

        # 3. ÖZELLÝK KORUNDU: Farklý Minimizasyon Stratejileri
        if strategy == "fast":
            cmds = [['obminimize', '-ff', 'MMFF94s', '-cg', '-n', '500', str(temp_3d_file)]]
        elif strategy == "thorough":
            sd_steps, cg_steps = '1000', '2000'
            cmds = [['obminimize', '-ff', 'MMFF94s', '-sd', '-n', sd_steps, str(temp_3d_file)], ['obminimize', '-ff', 'MMFF94s', '-cg', '-n', cg_steps, str(temp_3d_file)]]
        else: # "balanced" (varsayýlan)
            sd_steps, cg_steps = '500', '1000'
            cmds = [['obminimize', '-ff', 'MMFF94s', '-sd', '-n', sd_steps, str(temp_3d_file)], ['obminimize', '-ff', 'MMFF94s', '-cg', '-n', cg_steps, str(temp_3d_file)]]
        
        for cmd in cmds:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if res.returncode != 0:
                logging.error(f"MINIMIZATION FAILED for {input_file.name} (strategy: {strategy}): {res.stderr.strip()}")
                return False
        
        # 4. ÖZELLÝK KORUNDU: PDBQT Dönüþtürme
        cmd_pdbqt = ['obabel', str(temp_3d_file), '-O', str(output_file), '-p', '7.4', '--partialcharge', 'gasteiger', '-h']
        res_pdbqt = subprocess.run(cmd_pdbqt, capture_output=True, text=True, timeout=120)
        if res_pdbqt.returncode != 0:
            logging.error(f"PDBQT CONVERSION FAILED for {input_file.name}: {res_pdbqt.stderr.strip()}")
            return False
        
        if not (output_file.exists() and output_file.stat().st_size > 0):
            logging.error(f"FINAL PDBQT IS EMPTY for {input_file.name}")
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"TIMEOUT for {input_file.name}")
        return False
    except Exception as e:
        logging.error(f"UNEXPECTED ERROR for {input_file.name}: {e}")
        return False
    finally:
        if temp_3d_file.exists():
            temp_3d_file.unlink()

    return True

def main():
    parser = argparse.ArgumentParser(description="Worker script to convert one SDF to PDBQT.")
    parser.add_argument("--input-file", required=True, help="Path to the input SDF file.")
    parser.add_argument("--output-file", required=True, help="Path for the output PDBQT file.")
    parser.add_argument("--strategy", default="balanced", choices=["fast", "balanced", "thorough"], help="Minimization strategy.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing output files.")
    
    args = parser.parse_args()

    success = convert_single_file(args.input_file, args.output_file, args.strategy, args.overwrite)
    
    if not success:
        sys.exit(1) # Hata durumunda çýkýþ kodu 1 ver

if __name__ == "__main__":
    main()