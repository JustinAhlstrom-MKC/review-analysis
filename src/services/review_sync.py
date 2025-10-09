#!/usr/bin/env python3
"""
Main orchestration service for syncing reviews to Google Sheets.
"""

from datetime import datetime
from typing import List, Dict, Any
from src.core.config import config
from src.core.auth import GoogleAuthManager
from src.api.google_business import GoogleBusinessClient
# from src.api.sevenshift import SevenShiftClient  # Disabled for now
from src.api.google_sheets import GoogleSheetsClient


class ReviewSyncService:
    """Orchestrates the review sync process"""

    def __init__(self):
        # Initialize authentication
        self.auth_manager = GoogleAuthManager(
            credentials_path=config.google_credentials_path,
            token_path=config.google_token_path
        )

        # Initialize API clients
        self.gmb_client = GoogleBusinessClient(
            self.auth_manager,
            config.google_business_account_id
        )
        self.sheets_client = GoogleSheetsClient(
            self.auth_manager,
            config.sheet_id
        )

        # 7shifts integration disabled for now
        # Will be re-enabled in future version
        # try:
        #     self.sevenshift_client = SevenShiftClient(
        #         api_key=config.sevenshift_api_key,
        #         company_id=config.sevenshift_company_id
        #     )
        # except ValueError:
        #     print("⚠️  7shifts credentials not configured, skipping employee sync")
        #     self.sevenshift_client = None
        self.sevenshift_client = None

    def sync_all(self):
        """Main sync process - fetch and update all data"""
        print("=" * 60)
        print("🚀 Starting Review Sync Process")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        try:
            # Step 1: Fetch and sync reviews for each restaurant
            for restaurant in config.get_restaurants():
                self._sync_restaurant_reviews(restaurant)

            # Step 2: Create/update dashboard (placeholder for now)
            self._update_dashboard()

            print("\n" + "=" * 60)
            print("✅ Sync Complete!")
            print("=" * 60)
            print(f"📊 View your data: {self.sheets_client.get_sheet_url()}")
            print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"\n❌ Sync failed with error: {e}")
            raise

    # DISABLED: Employee sync - keeping code for future reference
    # def _sync_employees(self) -> List[str]:
    #     """Fetch employees and write to sheet, return list of names for dropdowns"""
    #     if not self.sevenshift_client:
    #         return []
    #
    #     try:
    #         # Fetch employees
    #         employees = self.sevenshift_client.fetch_employees(
    #             roles=config.employee_roles
    #         )
    #
    #         if not employees:
    #             print("⚠️  No employees found")
    #             return []
    #
    #         # Prepare employee data for sheet
    #         headers = ['Full Name', 'Role', 'Locations', 'Email', 'Phone']
    #         rows = [headers]
    #
    #         employee_names = []
    #         for emp in employees:
    #             rows.append([
    #                 emp['full_name'],
    #                 emp['role'],
    #                 emp['locations'],
    #                 emp['email'],
    #                 emp['phone']
    #             ])
    #             employee_names.append(emp['full_name'])
    #
    #         # Write to employee tab
    #         tab_name = config.employee_tab_name
    #         self.sheets_client.create_or_clear_sheet(tab_name)
    #         self.sheets_client.write_rows(tab_name, rows)
    #         self.sheets_client.format_header_row(tab_name)
    #
    #         print(f"✅ Synced {len(employees)} employees to sheet")
    #         return employee_names
    #
    #     except Exception as e:
    #         print(f"⚠️  Failed to sync employees: {e}")
    #         return []

    def _sync_restaurant_reviews(self, restaurant):
        """Fetch and sync reviews for one restaurant"""
        print(f"\n{'='*60}")
        print(f"📍 Processing: {restaurant.name}")
        print(f"{'='*60}")

        # Fetch reviews
        reviews = self.gmb_client.fetch_reviews(
            location_id=restaurant.location_id,
            restaurant_name=restaurant.name
        )

        if not reviews:
            print(f"⚠️  No reviews found for {restaurant.name}")
            return

        # Sort reviews by Date Updated for running average calculation
        # Sort in ascending order for running average calculation (oldest to newest)
        reviews_sorted = sorted(reviews, key=lambda x: x['date_updated'])

        # Calculate running averages
        running_sum = 0
        for idx, review in enumerate(reviews_sorted):
            running_sum += review['rating']
            running_avg = running_sum / (idx + 1)
            review['running_avg_1dec'] = round(running_avg, 1)
            # Format 3-decimal running average with padding zeros for consistent width
            review['running_avg_3dec'] = f"{running_avg:.3f}"

        # Prepare data for sheet
        # New column order: Date Posted, Date Updated, Review Month, Reviewer Name, Rating,
        #                   Running Avg, Running Avg (3 dec), Review Text, Response Text,
        #                   Response Date, Notes, Review ID, Restaurant
        rows = [config.review_columns]

        # Reverse the sort order to show newest reviews first (descending by date_updated)
        for review in reversed(reviews_sorted):
            rows.append([
                review['date_posted'],
                review['date_updated'],
                review['review_month'],
                review['reviewer_name'],
                review['rating'],
                review['running_avg_1dec'],
                review['running_avg_3dec'],
                review['review_text'],
                review['response_text'],
                review['response_date'],
                review['notes'],
                review['review_id'],
                review['restaurant']
            ])

        # Write to sheet
        tab_name = restaurant.sheet_name
        self.sheets_client.create_or_clear_sheet(tab_name)
        self.sheets_client.write_rows(tab_name, rows)
        self.sheets_client.format_header_row(tab_name)

        # Apply conditional formatting and column formatting
        self.sheets_client.format_review_sheet(tab_name)

        # Add filter view
        self.sheets_client.add_filter_view(tab_name)

        print(f"✅ Synced {len(reviews)} reviews for {restaurant.name}")

    def _update_dashboard(self):
        """Create/update dashboard tab (placeholder for future enhancement)"""
        # For now, just create a simple dashboard with instructions
        tab_name = config.dashboard_tab_name

        rows = [
            ['Review Dashboard', '', '', ''],
            ['', '', '', ''],
            ['This dashboard is under construction.', '', '', ''],
            ['For now, check the individual restaurant tabs:', '', '', ''],
            ['', '', '', ''],
        ]

        for restaurant in config.get_restaurants():
            rows.append([f'  • {restaurant.name}', '', '', ''])

        rows.extend([
            ['', '', '', ''],
            ['Future features:', '', '', ''],
            ['  • Summary statistics', '', '', ''],
            ['  • Rating trends', '', '', ''],
            ['  • Response rate tracking', '', '', ''],
            ['  • Employee mention analysis', '', '', ''],
        ])

        self.sheets_client.create_or_clear_sheet(tab_name)
        self.sheets_client.write_rows(tab_name, rows)
