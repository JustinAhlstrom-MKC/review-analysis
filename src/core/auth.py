#!/usr/bin/env python3
"""
Authentication management for Google APIs.
Handles OAuth flow and token persistence.
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# OAuth scopes required
SCOPES = [
    'https://www.googleapis.com/auth/business.manage',  # Google My Business
    'https://www.googleapis.com/auth/spreadsheets',     # Google Sheets
    'https://www.googleapis.com/auth/drive.file',       # Google Drive
]


class GoogleAuthManager:
    """Manages Google OAuth authentication and service creation"""

    def __init__(self, credentials_path: Path, token_path: Path):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._creds = None

    def get_credentials(self):
        """Get valid credentials, refreshing or authenticating as needed"""
        if self._creds:
            return self._creds

        # Load token if it exists
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                self._creds = pickle.load(token)

        # If there are no (valid) credentials available, authenticate
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                print("🔄 Refreshing expired token...")
                self._creds.refresh(Request())
            else:
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_path}\n"
                        "Please run the setup script first."
                    )

                # Check if running in CI environment
                is_ci = os.getenv('CI') == 'true' or os.getenv('GITHUB_ACTIONS') == 'true'

                if is_ci:
                    raise RuntimeError(
                        "❌ Cannot authenticate in CI environment without a valid token.\n"
                        "The Google token is missing or expired.\n\n"
                        "To fix this:\n"
                        "1. Run the sync locally first to generate a token: python scripts/sync_reviews.py\n"
                        "2. Encode the token: base64 config/credentials/google_token.pickle\n"
                        "3. Update the GOOGLE_TOKEN_PICKLE secret in GitHub with the encoded value\n"
                        "4. Re-run the workflow\n"
                    )

                print("🔐 Starting OAuth authentication flow...")
                print("A browser window will open for Google sign-in")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                self._creds = flow.run_local_server(port=0)
                print("✅ Authentication successful!")

            # Save the credentials for next time
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(self._creds, token)
                print(f"💾 Token saved to {self.token_path}")

        return self._creds

    def get_service(self, service_name: str, version: str):
        """Build and return a Google API service"""
        creds = self.get_credentials()
        return build(service_name, version, credentials=creds)

    def get_mybusiness_service(self):
        """Get My Business API service v4 for reviews"""
        # Use static discovery document URL for v4 API
        creds = self.get_credentials()
        discovery_url = 'https://mybusiness.googleapis.com/$discovery/rest?version=v4'
        return build('mybusiness', 'v4', credentials=creds, discoveryServiceUrl=discovery_url)

    def get_sheets_service(self):
        """Get Google Sheets API service"""
        return self.get_service('sheets', 'v4')

    def get_drive_service(self):
        """Get Google Drive API service"""
        return self.get_service('drive', 'v3')
