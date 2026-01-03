"""Setup script for ROM Duplicate Manager."""

from setuptools import setup, find_packages
import os

# Read version from resources/VERSION file
version_file = os.path.join('resources', 'VERSION')
if os.path.exists(version_file):
    with open(version_file, 'r') as f:
        version = f.read().strip()
else:
    version = '1.3.5'

# Read long description from README
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='rom-duplicate-manager',
    version=version,
    author='Anach',
    description='A comprehensive tool for managing duplicate ROM files',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Anach/ROM_Duplicate_Manager',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: System :: Archiving',
        'Topic :: Utilities',
    ],
    python_requires='>=3.8',
    install_requires=[
        'send2trash',
    ],
    entry_points={
        'console_scripts': [
            'rom-duplicate-manager=rom_duplicate_manager:main',
        ],
        'gui_scripts': [
            'rom-duplicate-manager-gui=rom_duplicate_manager:main',
        ],
    },
    include_package_data=True,
    package_data={
        'rom_duplicate_manager': ['resources/*'],
    },
)