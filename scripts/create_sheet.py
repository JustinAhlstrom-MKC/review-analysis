#!/usr/bin/env python3
"""
Helper script to create a new Google Sheet for reviews.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.auth import GoogleAuthManager
from src.core.config import config


def create_sheet(title: str = "Restaurant Reviews"):
    """Create a new Google Sheet"""
    print(f"📝 Creating new Google Sheet: {title}")

    try:
        auth_manager = GoogleAuthManager(
            credentials_path=config.google_credentials_path,
            token_path=config.google_token_path
        )

        drive_service = auth_manager.get_drive_service()

        # Create the spreadsheet
        file_metadata = {
            'name': title,
            'mimeType': 'application/vnd.google-apps.spreadsheet'
        }

        file = drive_service.files().create(
            body=file_metadata,
            fields='id, webViewLink'
        ).execute()

        sheet_id = file.get('id')
        url = file.get('webViewLink')

        print(f"\n✅ Sheet created successfully!")
        print(f"\n   Sheet ID: {sheet_id}")
        print(f"   URL: {url}")
        print(f"\n📋 Add this to your .env file:")
        print(f"   SHEET_ID={sheet_id}\n")

        return sheet_id

    except Exception as e:
        print(f"❌ Failed to create sheet: {e}")
        return None


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Create a new Google Sheet for reviews')
    parser.add_argument('--title', default='Restaurant Reviews',
                       help='Title for the new sheet')

    args = parser.parse_args()

    sheet_id = create_sheet(args.title)
    return 0 if sheet_id else 1


if __name__ == '__main__':
    sys.exit(main())
