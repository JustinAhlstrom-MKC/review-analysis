#!/usr/bin/env python3
"""
Main script to sync reviews from Google My Business to Google Sheets.
This is the primary entry point for the review sync process.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.review_sync import ReviewSyncService


def main():
    """Run the review sync"""
    try:
        service = ReviewSyncService()
        service.sync_all()
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Sync interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
