#!/usr/bin/env python3
"""
Interactive setup wizard for first-time configuration.
Guides users through setting up credentials and configuration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.auth import GoogleAuthManager
from src.core.config import config


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")


def test_google_auth():
    """Test Google authentication"""
    print_header("Step 1: Testing Google Authentication")

    print("This will open a browser window for you to authorize the app.")
    print("Make sure you sign in with the Google account that manages your restaurants.\n")

    input("Press Enter to continue...")

    try:
        auth_manager = GoogleAuthManager(
            credentials_path=config.google_credentials_path,
            token_path=config.google_token_path
        )

        # This will trigger OAuth flow if needed
        creds = auth_manager.get_credentials()

        print("\n✅ Google authentication successful!")
        print(f"   Token saved to: {config.google_token_path}\n")

        return True

    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return False


def get_location_ids():
    """Help user find their Google My Business location IDs"""
    print_header("Step 2: Finding Your Restaurant Location IDs")

    print("We need to find your restaurant location IDs from Google My Business.")
    print("This requires accessing the Google My Business API.\n")

    try:
        from src.api.google_business import GoogleBusinessClient

        auth_manager = GoogleAuthManager(
            credentials_path=config.google_credentials_path,
            token_path=config.google_token_path
        )

        client = GoogleBusinessClient(auth_manager)

        print("📍 Searching for your locations...")
        print("\nNote: If this fails, you may need to:")
        print("  1. Verify API access in Google Cloud Console")
        print("  2. Manually find location IDs in Google Business Profile\n")

        # Try to list locations (this might fail depending on API access)
        try:
            # This is a simplified approach - actual implementation may vary
            print("⚠️  Location discovery is complex and may require manual setup.")
            print("   Please refer to Google My Business API documentation.\n")

        except Exception as e:
            print(f"⚠️  Could not auto-discover locations: {e}\n")

        print("To find your location IDs manually:")
        print("  1. Go to: https://business.google.com")
        print("  2. Select your business")
        print("  3. The location ID is in the URL or accessible via API\n")

        print("Once you have your location IDs, add them to your .env file:")
        print(f"  {config.project_root}/.env\n")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def setup_env_file():
    """Guide user through creating .env file"""
    print_header("Step 3: Configuration Setup")

    env_path = config.project_root / ".env"
    env_example_path = config.project_root / ".env.example"

    if env_path.exists():
        print(f"✅ Configuration file already exists: {env_path}")
        overwrite = input("\nDo you want to reconfigure? (y/N): ").strip().lower()
        if overwrite != 'y':
            return True

    print(f"Let's create your configuration file: {env_path}\n")

    # Gather information
    print("Please provide the following information:\n")

    sheet_id = input("Google Sheet ID (leave blank to create later): ").strip()
    sevenshift_key = input("7shifts API Key (leave blank to skip): ").strip()
    sevenshift_company = input("7shifts Company ID (leave blank to skip): ").strip()
    margies_location = input("Margie's Location ID (format: locations/12345): ").strip()
    grackle_location = input("Grackle Location ID (format: locations/12345): ").strip()

    # Create .env file
    env_content = f"""# Google Sheets Configuration
SHEET_ID={sheet_id}

# 7shifts API Configuration
SEVENSHIFT_API_KEY={sevenshift_key}
SEVENSHIFT_COMPANY_ID={sevenshift_company}

# Restaurant Location IDs (from Google My Business)
MARGIES_LOCATION_ID={margies_location}
GRACKLE_LOCATION_ID={grackle_location}

# Optional: Logging level
LOG_LEVEL=INFO
"""

    with open(env_path, 'w') as f:
        f.write(env_content)

    print(f"\n✅ Configuration saved to: {env_path}")
    print("\nYou can edit this file anytime to update your settings.\n")

    return True


def main():
    """Run the setup wizard"""
    print("\n" + "🚀 " * 25)
    print("\n  Welcome to the Review Analysis Setup Wizard!")
    print("\n" + "🚀 " * 25)

    print("\nThis wizard will help you:")
    print("  1. Authenticate with Google")
    print("  2. Find your restaurant location IDs")
    print("  3. Configure your settings")

    print("\n" + "-" * 60)
    input("\nPress Enter to begin...")

    # Step 1: Google Auth
    if not test_google_auth():
        print("\n❌ Setup failed at authentication step.")
        print("   Please check your credentials and try again.")
        return 1

    # Step 2: Location IDs
    get_location_ids()

    # Step 3: Configuration
    if not setup_env_file():
        print("\n❌ Setup failed at configuration step.")
        return 1

    # Success!
    print_header("🎉 Setup Complete!")

    print("Next steps:")
    print("  1. Create a Google Sheet for your reviews")
    print("  2. Add the Sheet ID to your .env file")
    print("  3. Run: python scripts/sync_reviews.py\n")

    print("For more help, see the README.md file.\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
