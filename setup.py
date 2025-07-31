"""
Setup script for career-agent.
This file is provided for backward compatibility.
Configuration is primarily in pyproject.toml.
"""

from setuptools import setup, find_packages

setup(
    packages=find_packages(exclude=["tests*", "docs*"]),
)