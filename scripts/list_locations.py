#!/usr/bin/env python3
"""
Script to list all Google My Business locations for your account.
This helps you find the location IDs needed for the .env file.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.auth import GoogleAuthManager
import requests
from google.auth.transport.requests import Request


def list_all_locations():
    """List all available Google My Business locations"""

    # Setup paths
    config_dir = project_root / 'config' / 'credentials'
    credentials_path = config_dir / 'google_oauth.json'
    token_path = config_dir / 'google_token.pickle'

    # Check if credentials exist
    if not credentials_path.exists():
        print("❌ Error: google_oauth.json not found in config/credentials/ directory")
        print("Please download your OAuth credentials from Google Cloud Console")
        return

    # Initialize auth
    auth_manager = GoogleAuthManager(credentials_path, token_path)

    try:
        print("🔍 Fetching your Google My Business locations...\n")

        # Get credentials
        creds = auth_manager.get_credentials()
        if creds.expired and creds.refresh_token:
            print("🔄 Refreshing token...")
            creds.refresh(Request())

        headers = {'Authorization': f'Bearer {creds.token}'}

        # List all accounts
        accounts_url = 'https://mybusinessaccountmanagement.googleapis.com/v1/accounts'
        accounts_response = requests.get(accounts_url, headers=headers)
        accounts_response.raise_for_status()
        accounts_data = accounts_response.json()

        accounts = accounts_data.get('accounts', [])
        if not accounts:
            print("❌ No Google My Business accounts found")
            return

        print(f"Found {len(accounts)} account(s)\n")
        print("=" * 80)

        # For each account, list locations
        for account in accounts:
            account_name = account['name']  # e.g., "accounts/12345"
            account_display = account.get('accountName', 'Unnamed Account')

            print(f"\n📍 Account: {account_display}")
            print(f"   Account Resource: {account_name}")
            print("-" * 80)

            # Get locations using Business Information API
            try:
                locations_url = f'https://mybusinessbusinessinformation.googleapis.com/v1/{account_name}/locations'
                params = {'readMask': 'name,title,storefrontAddress'}

                locations_response = requests.get(locations_url, headers=headers, params=params)
                locations_response.raise_for_status()
                locations_data = locations_response.json()

                locations = locations_data.get('locations', [])
                if not locations:
                    print("   No locations found for this account\n")
                    continue

                print(f"   Found {len(locations)} location(s):\n")

                for idx, location in enumerate(locations, 1):
                    location_id = location['name']  # Full resource name
                    title = location.get('title', 'Unnamed Location')
                    address = location.get('storefrontAddress', {})

                    print(f"   {idx}. {title}")
                    print(f"      Full Location Resource: {location_id}")

                    if address:
                        addr_lines = address.get('addressLines', [])
                        addr_line = addr_lines[0] if addr_lines else ''
                        city = address.get('locality', '')
                        state = address.get('administrativeArea', '')

                        if addr_line or city:
                            print(f"      Address: {addr_line}, {city}, {state}")

                    print()

            except requests.exceptions.HTTPError as e:
                print(f"   ⚠️  Could not fetch locations: {e}")
                if e.response:
                    print(f"      Status: {e.response.status_code}")
                    print(f"      Response: {e.response.text[:200]}")
                print()

        print("=" * 80)
        print("\n✅ Done! Copy the FULL Location Resource above to your .env file")
        print("   Format: MARGIES_LOCATION_ID=accounts/12345/locations/67890")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    list_all_locations()
