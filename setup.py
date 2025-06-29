#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import os

# README dosyasını oku
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Requirements dosyasını oku
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="sdf-to-pdbqt-converter",
    version="1.0.0",
    author="TR-GRID Team",
    author_email="info@tr-grid.org",
    description="Büyük ölçekli SDF dosyalarını PDBQT formatına dönüştürmek için geliştirilmiş pipeline",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/tr-grid/SDF_TO_PDBQT",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Chemistry",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.2.5",
            "pytest-cov>=3.0.0",
            "black>=21.7b0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "sdf-splitter=sdf_splitter:main",
            "sdf-filter=analyze_and_filter_sdf:main",
            "sdf-to-pdbqt=sdf_to_pdbqt_converter:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="chemistry, molecular docking, sdf, pdbqt, rdkit, openbabel, cheminformatics",
    project_urls={
        "Bug Reports": "https://github.com/tr-grid/SDF_TO_PDBQT/issues",
        "Source": "https://github.com/tr-grid/SDF_TO_PDBQT",
        "Documentation": "https://github.com/tr-grid/SDF_TO_PDBQT#readme",
    },
) 