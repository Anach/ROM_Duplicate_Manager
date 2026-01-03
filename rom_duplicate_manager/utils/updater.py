"""Update checker and management system for ROM Duplicate Manager."""

import asyncio
import json
import os
import platform
import urllib.request
import urllib.error
from typing import Dict, Optional, Tuple, Any
from packaging import version


class UpdateInfo:
    """Container for update information."""

    def __init__(self, version: str, download_url: str, release_notes: str,
                 published_date: str, is_prerelease: bool = False):
        self.version = version
        self.download_url = download_url
        self.release_notes = release_notes
        self.published_date = published_date
        self.is_prerelease = is_prerelease


class UpdateChecker:
    """Handles checking for and managing application updates."""

    def __init__(self, current_version: str, github_repo: str = "Anach/ROM_Duplicate_Manager"):
        """Initialize update checker.

        Args:
            current_version: Current version of the application
            github_repo: GitHub repository in format "owner/repo"
        """
        self.current_version = current_version
        self.github_repo = github_repo
        self.github_api_url = f"https://api.github.com/repos/{github_repo}"

    def get_platform_filename(self, version_str: str) -> str:
        """Get the expected filename for current platform.

        Args:
            version_str: Version string (e.g. "1.4.0")

        Returns:
            Expected filename for this platform
        """
        system = platform.system().lower()
        if system == "windows":
            return f"ROM.Duplicate.Manager.v.{version_str}.zip"
        elif system == "darwin":  # macOS
            return f"ROM.Duplicate.Manager.v.{version_str}.macos.tar.gz"
        else:  # Linux and others
            return f"ROM.Duplicate.Manager.v.{version_str}.linux.tar.gz"

    async def check_for_updates(self, include_prereleases: bool = False) -> Optional[UpdateInfo]:
        """Check GitHub for available updates.

        Args:
            include_prereleases: Whether to include pre-release versions

        Returns:
            UpdateInfo if newer version available, None otherwise
        """
        try:
            # Get latest release info from GitHub API
            url = f"{self.github_api_url}/releases/latest"
            if include_prereleases:
                url = f"{self.github_api_url}/releases"

            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read().decode())

            # Handle list response for prereleases
            if include_prereleases and isinstance(data, list):
                if not data:
                    return None
                release_data = data[0]  # Latest release
            else:
                release_data = data

            remote_version = release_data["tag_name"].lstrip("v")

            # Compare versions
            if version.parse(remote_version) > version.parse(self.current_version):
                # Find download URL for current platform
                platform_filename = self.get_platform_filename(remote_version)
                download_url = None

                for asset in release_data.get("assets", []):
                    if asset["name"] == platform_filename:
                        download_url = asset["browser_download_url"]
                        break

                if not download_url:
                    # Fallback to GitHub release page
                    download_url = release_data["html_url"]

                return UpdateInfo(
                    version=remote_version,
                    download_url=download_url,
                    release_notes=release_data.get("body", ""),
                    published_date=release_data.get("published_at", ""),
                    is_prerelease=release_data.get("prerelease", False)
                )

        except (urllib.error.URLError, json.JSONDecodeError, KeyError, Exception):
            # Silently fail for async update checks
            pass

        return None

    def check_for_updates_sync(self, include_prereleases: bool = False) -> Optional[UpdateInfo]:
        """Synchronous wrapper for update checking.

        Args:
            include_prereleases: Whether to include pre-release versions

        Returns:
            UpdateInfo if newer version available, None otherwise
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an event loop, create a new one
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(self.check_for_updates(include_prereleases))
                    )
                    return future.result(timeout=15)
            else:
                return asyncio.run(self.check_for_updates(include_prereleases))
        except Exception:
            # Silently fail - caller will handle UI messaging
            return None

    def download_update(self, update_info: UpdateInfo, save_path: str) -> bool:
        """Download update file.

        Args:
            update_info: Update information
            save_path: Where to save the downloaded file

        Returns:
            True if download successful, False otherwise
        """
        try:
            urllib.request.urlretrieve(update_info.download_url, save_path)
            return os.path.exists(save_path)
        except Exception:
            return False

    def get_update_message(self, update_info: UpdateInfo) -> str:
        """Format update notification message.

        Args:
            update_info: Update information

        Returns:
            Formatted message string
        """
        prerelease_text = " (Pre-release)" if update_info.is_prerelease else ""

        message = f"""New version available: v{update_info.version}{prerelease_text}
Current version: v{self.current_version}

Release Notes:
{update_info.release_notes[:500]}{'...' if len(update_info.release_notes) > 500 else ''}

Would you like to download the update?"""

        return message


def get_current_version() -> str:
    """Get current application version.

    Returns:
        Current version string
    """
    try:
        # Try to get version from package
        from rom_duplicate_manager import __version__
        return __version__
    except ImportError:
        # Fallback to VERSION file
        version_file = "resources/VERSION"
        if os.path.exists(version_file):
            with open(version_file, 'r') as f:
                return f.read().strip()
        return "1.4.0"  # Default fallback