#!/usr/bin/env python3
"""
List Google My Business accounts to find your account ID.
"""

import sys
from pathlib import Path
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.auth import GoogleAuthManager
from google.auth.transport.requests import Request


def main():
    print("=" * 60)
    print("🔍 Listing Google My Business Accounts")
    print("=" * 60)

    # Initialize auth
    creds_dir = project_root / 'config' / 'credentials'
    auth_manager = GoogleAuthManager(
        credentials_path=creds_dir / 'google_credentials.json',
        token_path=creds_dir / 'google_token.pickle'
    )

    # Get credentials
    creds = auth_manager.get_credentials()
    if creds.expired and creds.refresh_token:
        print("🔄 Refreshing token...")
        creds.refresh(Request())

    # Make API request to list accounts using Account Management API
    url = 'https://mybusinessaccountmanagement.googleapis.com/v1/accounts'
    headers = {'Authorization': f'Bearer {creds.token}'}

    try:
        print("🔍 Checking API access...\n")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        accounts = data.get('accounts', [])

        if not accounts:
            print("⚠️  No accounts found")
            print("\nThis could mean:")
            print("  1. You don't have a Google Business Profile")
            print("  2. Your OAuth credentials don't have the right permissions")
            print("  3. The API requires verification from Google")
            return

        print(f"\n✅ Found {len(accounts)} account(s):\n")

        for i, account in enumerate(accounts, 1):
            account_name = account.get('name', 'Unknown')  # Full resource name like "accounts/12345"
            account_display_name = account.get('accountName', 'Unknown')  # Human-readable name
            account_type = account.get('type', 'Unknown')
            account_role = account.get('role', 'Unknown')

            print(f"{i}. Business Name: {account_display_name}")
            print(f"   Account Resource: {account_name}")
            print(f"   Type: {account_type}")
            print(f"   Your Role: {account_role}")
            print()

        print("=" * 60)
        print("📝 Next Steps:")
        print("=" * 60)
        print("1. Copy your account ID from above")
        print("2. Use scripts/list_locations.py to find your location IDs")
        print("3. Update your .env file with format:")
        print("   MARGIES_LOCATION_ID=accounts/{account_id}/locations/{location_id}")

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response:
            print(f"   Status: {e.response.status_code}")
            print(f"   Response: {e.response.text}")

        if e.response and e.response.status_code == 403:
            print("\n⚠️  Access Denied (403)")
            print("This usually means:")
            print("  1. The My Business API requires verification")
            print("  2. You need to apply for API access at:")
            print("     https://developers.google.com/my-business/content/basic-setup")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == '__main__':
    main()
