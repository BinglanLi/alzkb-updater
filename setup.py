"""
Setup script for AlzKB Updater
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="alzkb-updater",
    version="0.1.0",
    author="AlzKB Team",
    description="Automated Alzheimer's Knowledge Base data integration tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.0.0",
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "python-dateutil>=2.8.2",
        "tqdm>=4.65.0",
    ],
    entry_points={
        "console_scripts": [
            "alzkb-update=main:main",
        ],
    },
)
