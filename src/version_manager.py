"""
Version Manager for AlzKB

This module manages AlzKB version information dynamically.
"""

import os
import re
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime


class VersionManager:
    """
    Manages AlzKB version information.
    
    Versions follow semantic versioning: MAJOR.MINOR.PATCH
    - MAJOR: Incompatible API changes or major restructuring
    - MINOR: New functionality in a backwards-compatible manner
    - PATCH: Backwards-compatible bug fixes
    """
    
    def __init__(self, version_file: Optional[str] = None):
        """
        Initialize the version manager.
        
        Args:
            version_file: Path to version file. If None, uses default location.
        """
        if version_file is None:
            # Default to VERSION file in project root
            project_root = Path(__file__).parent.parent.parent
            version_file = project_root / "VERSION"
        
        self.version_file = Path(version_file)
        self.current_version = self._read_version()
    
    def _read_version(self) -> str:
        """
        Read the current version from the version file.
        
        Returns:
            Version string (e.g., "2.3.0")
        """
        if not self.version_file.exists():
            # Default version if file doesn't exist
            return "2.3.0"
        
        try:
            with open(self.version_file, 'r') as f:
                content = f.read().strip()
                # Extract version number (handle various formats)
                match = re.search(r'(\d+\.\d+\.\d+)', content)
                if match:
                    return match.group(1)
                return content
        except Exception:
            return "2.3.0"
    
    def _write_version(self, version: str):
        """
        Write version to the version file.
        
        Args:
            version: Version string to write
        """
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.version_file, 'w') as f:
            f.write(f"{version}\n")
    
    def get_version(self) -> str:
        """
        Get the current version.
        
        Returns:
            Version string
        """
        return self.current_version
    
    def parse_version(self, version: Optional[str] = None) -> Tuple[int, int, int]:
        """
        Parse version string into components.
        
        Args:
            version: Version string to parse. If None, uses current version.
        
        Returns:
            Tuple of (major, minor, patch)
        """
        if version is None:
            version = self.current_version
        
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        
        return int(parts[0]), int(parts[1]), int(parts[2])
    
    def bump_major(self) -> str:
        """
        Bump major version number.
        
        Returns:
            New version string
        """
        major, minor, patch = self.parse_version()
        new_version = f"{major + 1}.0.0"
        self.current_version = new_version
        self._write_version(new_version)
        return new_version
    
    def bump_minor(self) -> str:
        """
        Bump minor version number.
        
        Returns:
            New version string
        """
        major, minor, patch = self.parse_version()
        new_version = f"{major}.{minor + 1}.0"
        self.current_version = new_version
        self._write_version(new_version)
        return new_version
    
    def bump_patch(self) -> str:
        """
        Bump patch version number.
        
        Returns:
            New version string
        """
        major, minor, patch = self.parse_version()
        new_version = f"{major}.{minor}.{patch + 1}"
        self.current_version = new_version
        self._write_version(new_version)
        return new_version
    
    def set_version(self, version: str) -> str:
        """
        Set a specific version.
        
        Args:
            version: Version string to set
        
        Returns:
            The set version string
        """
        # Validate format
        self.parse_version(version)
        self.current_version = version
        self._write_version(version)
        return version
    
    def get_version_info(self) -> dict:
        """
        Get detailed version information.
        
        Returns:
            Dictionary with version details
        """
        major, minor, patch = self.parse_version()
        return {
            'version': self.current_version,
            'major': major,
            'minor': minor,
            'patch': patch,
            'timestamp': datetime.now().isoformat()
        }
