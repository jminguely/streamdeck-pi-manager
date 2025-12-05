#!/usr/bin/env python3
"""
Stream Deck Pi Manager - Setup Script
"""
from setuptools import setup, find_packages
import os

# Read version from __init__.py
version = {}
with open("src/streamdeck_pi/__init__.py") as f:
    exec(f.read(), version)

# Read long description from README
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="streamdeck-pi-manager",
    version=version["__version__"],
    author="Your Name",
    author_email="your.email@example.com",
    description="Web-based management interface for Elgato Stream Deck on Raspberry Pi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/streamdeck-pi-manager",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/streamdeck-pi-manager/issues",
        "Documentation": "https://streamdeck-pi-manager.readthedocs.io/",
        "Source Code": "https://github.com/yourusername/streamdeck-pi-manager",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: System :: Hardware",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.9",
    install_requires=[
        "streamdeck>=0.9.5",
        "pillow>=10.0.0",
        "fastapi>=0.104.0",
        "uvicorn[standard]>=0.24.0",
        "python-multipart>=0.0.6",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "jinja2>=3.1.0",
        "python-jose[cryptography]>=3.3.0",
        "passlib[bcrypt]>=1.7.4",
        "psutil>=5.9.0",
        "aiofiles>=23.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
            "pre-commit>=3.3.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.4.0",
            "mkdocstrings[python]>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "streamdeck-pi=streamdeck_pi.cli:main",
            "streamdeck-pi-web=streamdeck_pi.web:main",
        ],
    },
    include_package_data=True,
    package_data={
        "streamdeck_pi": [
            "web/static/**/*",
            "web/templates/**/*",
            "plugins/**/*",
        ],
    },
    zip_safe=False,
)
