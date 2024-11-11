# src/core/__init__.py
"""Core package initialization"""

# src/core/CLI/__init__.py
"""CLI package initialization"""

# src/core/Client/__init__.py
"""Client package initialization"""

# src/core/Market/__init__.py
"""Market package initialization"""

# src/core/Queue/__init__.py
"""Queue package initialization"""

# src/core/Server/__init__.py
"""Server package initialization"""

# src/simulation/__init__.py
"""Simulation package initialization"""

from setuptools import setup, find_packages

setup(
    name="market-simulation",
    version="0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[],
    description="A distributed electronic food marketplace simulation",
    keywords="distributed-systems, market-simulation, python",
    project_urls={"Source": "DEMI"},
)
