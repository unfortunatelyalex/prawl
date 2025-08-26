import requests
import json
import re
from typing import Tuple, Optional

# Fixed repository configuration to point to correct repo
REPO_OWNER = 'unfortunatelyalex'
REPO_NAME = 'prawl'
API_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/releases/latest'

class Update:
    def __init__(self, version: str):
        self.api_url = API_URL
        self.current_version = version
        self.latest_version: Optional[str] = None
        self.release_url: Optional[str] = None

    def _version_parse(self, version: str) -> Tuple[int, ...]:
        """
        Parse version string into comparable tuple.
        Handles semantic versioning including pre-release versions.
        Examples: '1.0.0', '1.0.0-beta', '1.0.0-alpha.1'
        """
        if not version:
            return (0,)
        
        # Remove 'v' prefix if present
        version = version.lstrip('v')
        
        # Split on pre-release indicators
        main_version = re.split(r'[-+]', version)[0]
        
        try:
            # Parse main version numbers
            parts = [int(x) for x in main_version.split('.')]
            return tuple(parts)
        except ValueError:
            # Fallback for invalid version format
            return (0,)

    def check(self) -> Tuple[str, bool]:
        """
        Check for updates and return status message and update availability.
        
        Returns:
            Tuple of (message, is_update_available)
        """
        try:
            response = requests.get(self.api_url, timeout=10)
            response.raise_for_status()

            data = response.json()
            self.latest_version = data.get('tag_name')
            self.release_url = data.get('html_url')

            if not self.latest_version:
                return 'Could not get latest version from server', False

            current_parsed = self._version_parse(self.current_version)
            latest_parsed = self._version_parse(self.latest_version)
            
            if latest_parsed > current_parsed:
                return f'Update available: {self.latest_version}', True
            elif latest_parsed == current_parsed:
                return f'Up to date! ({self.current_version})', False
            else:
                return f'You have a newer version ({self.current_version})', False

        except requests.exceptions.Timeout:
            return 'Request timed out - check your connection', False
        except requests.exceptions.ConnectionError:
            return 'Could not connect to update server', False
        except requests.exceptions.HTTPError as e:
            return f'Server error: {e.response.status_code}', False
        except requests.exceptions.RequestException:
            return 'Network error occurred', False
        except json.JSONDecodeError:
            return 'Invalid response from server', False
        except Exception as e:
            # Log the actual error for debugging while showing user-friendly message
            print(f"Unexpected error in update check: {e}")
            return 'Unexpected error occurred', False
