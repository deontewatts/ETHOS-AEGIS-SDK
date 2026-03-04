"""
setup.py — Ethos Aegis package installation configuration.

Install (editable, for development):
    pip install -e .

Install (production):
    pip install .

No external dependencies required — the entire package runs on Python 3.10+
standard library only (hashlib, hmac, re, unicodedata, threading, dataclasses).
"""

from setuptools import setup, find_packages
from pathlib import Path

long_description = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="ethos-aegis",
    version="1.0.0",
    author="The Ethos Aegis Project",
    description=(
        "A sovereign digital immune system: a living, adaptive framework that maps "
        "every biological defense mechanism into a rigorous computational architecture "
        "for the purification of AI systems."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ethos-aegis/ethos-aegis",
    packages=find_packages(exclude=["tests*", "scripts*", "docs*"]),
    python_requires=">=3.10",
    install_requires=[],          # zero external dependencies
    extras_require={
        "dev": ["pytest>=7.0"],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords=[
        "ai-safety", "prompt-injection", "digital-immune-system",
        "adversarial-robustness", "llm-security", "content-moderation",
    ],
    entry_points={
        "console_scripts": [
            "aegis-demo=scripts.demo:main",
        ],
    },
)
