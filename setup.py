"""Setup file for the package."""

from setuptools import find_packages, setup

setup(
    name="multiplexed_device_dose_customization",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pillow",
        "pytest",
    ],
)
