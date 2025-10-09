#!/usr/bin/env python3
"""
Google My Business API client for fetching reviews.
"""

from typing import List, Dict, Any
from datetime import datetime
import requests


class GoogleBusinessClient:
    """Client for Google My Business API"""

    def __init__(self, auth_manager, account_id: str):
        """
        Args:
            auth_manager: GoogleAuthManager instance
            account_id: Google Business account ID (e.g., "accounts/12345" or just "12345")
        """
        self.auth_manager = auth_manager
        # Ensure account_id is in the format "accounts/12345"
        self.account_id = account_id if account_id.startswith('accounts/') else f'accounts/{account_id}'

    def _get_headers(self):
        """Get authorization headers for API requests"""
        creds = self.auth_manager.get_credentials()
        # Refresh token if needed
        if creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        return {'Authorization': f'Bearer {creds.token}'}

    def fetch_reviews(self, location_id: str, restaurant_name: str) -> List[Dict[str, Any]]:
        """
        Fetch all reviews for a specific location.

        Args:
            location_id: Location ID - can be "locations/12345" or "accounts/123/locations/456"
            restaurant_name: Human-readable restaurant name

        Returns:
            List of review dictionaries
        """
        print(f"📊 Fetching reviews for {restaurant_name}...")

        try:
            reviews = []
            page_token = None

            # Construct full location path if needed
            if location_id.startswith('locations/'):
                # Need to prepend account_id
                full_location_path = f'{self.account_id}/{location_id}'
            else:
                # Already has accounts/x/locations/y format
                full_location_path = location_id

            while True:
                # Build URL for reviews endpoint using My Business API v4
                url = f'https://mybusiness.googleapis.com/v4/{full_location_path}/reviews'
                params = {'pageSize': 50}
                if page_token:
                    params['pageToken'] = page_token

                # Make API request
                response = requests.get(url, headers=self._get_headers(), params=params)
                response.raise_for_status()
                data = response.json()

                # Process reviews
                for review in data.get('reviews', []):
                    reviews.append(self._parse_review(review, restaurant_name))

                # Check for more pages
                page_token = data.get('nextPageToken')
                if not page_token:
                    break

            print(f"✅ Fetched {len(reviews)} reviews for {restaurant_name}")
            return reviews

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error fetching reviews for {restaurant_name}: {e}")
            print(f"   Response: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            print(f"❌ Error fetching reviews for {restaurant_name}: {e}")
            raise

    def _parse_review(self, review_data: Dict[str, Any], restaurant_name: str) -> Dict[str, Any]:
        """Parse a single review from API response"""

        # Extract rating
        star_rating = review_data.get('starRating', 'STAR_RATING_UNSPECIFIED')
        rating_map = {
            'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
            'STAR_RATING_UNSPECIFIED': None
        }
        rating = rating_map.get(star_rating, None)

        # Extract review reply
        review_reply = review_data.get('reviewReply', {})
        response_text = review_reply.get('comment', '')
        response_date_raw = review_reply.get('updateTime', '')

        # Parse reviewer info
        reviewer = review_data.get('reviewer', {})
        reviewer_name = reviewer.get('displayName', 'Anonymous')

        # Parse and format dates
        date_posted_raw = review_data.get('createTime', '')
        date_updated_raw = review_data.get('updateTime', '')

        # Format dates as YYYY-MM-DD (remove timestamp)
        date_posted = self._format_date(date_posted_raw)
        date_updated = self._format_date(date_updated_raw)
        response_date = self._format_date(response_date_raw)

        # Extract Review Month from date_updated (YYYY-MM format)
        review_month = self._format_month(date_updated_raw)

        return {
            'review_id': review_data.get('name', ''),
            'restaurant': restaurant_name,
            'date_posted': date_posted,
            'date_updated': date_updated,
            'review_month': review_month,
            'reviewer_name': reviewer_name,
            'rating': rating,
            'review_text': review_data.get('comment', ''),
            'response_text': response_text,
            'response_date': response_date,
            'notes': ''  # Will be manually added in sheet
        }

    def _format_date(self, date_string: str) -> str:
        """Format ISO 8601 date string to YYYY-MM-DD"""
        if not date_string:
            return ''
        try:
            # Parse ISO 8601 format (e.g., "2024-03-15T14:30:00Z")
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d')
        except Exception:
            return date_string  # Return as-is if parsing fails

    def _format_month(self, date_string: str) -> str:
        """Format ISO 8601 date string to YYYY-MM"""
        if not date_string:
            return ''
        try:
            # Parse ISO 8601 format (e.g., "2024-03-15T14:30:00Z")
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m')
        except Exception:
            return ''  # Return empty if parsing fails

    def get_location_info(self, location_id: str) -> Dict[str, Any]:
        """Get information about a location"""
        try:
            # For location info, we'd typically use mybusinessbusinessinformation API
            # For now, return basic info from the location_id
            print(f"⚠️  Location info API not fully implemented, using location_id: {location_id}")
            return {
                'name': 'Unknown',
                'address': {},
                'phone': '',
            }
        except Exception as e:
            print(f"⚠️  Could not fetch location info: {e}")
            return {}
