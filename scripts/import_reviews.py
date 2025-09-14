#!/usr/bin/env python3
"""
Import Google Business Profile takeout data.
Extracts and consolidates review data from multiple locations.
"""

import json
import pandas as pd
from pathlib import Path
import zipfile
from datetime import datetime

def extract_takeout_zip(zip_path):
    """Extract takeout zip file"""
    extract_dir = Path('data/raw/extracted')
    extract_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

    print("✓ Extraction complete")
    return extract_dir

def find_review_files(extract_dir):
    """Find review JSON files in the extracted Google Business Profile data"""
    review_files = []

    # Google Business Profile structure
    business_profile_path = extract_dir / "Takeout" / "Google Business Profile"

    if not business_profile_path.exists():
        print("❌ Google Business Profile data not found. Checking alternative paths...")
        # Try alternative path structures
        for path in extract_dir.rglob("reviews*.json"):
            review_files.append(path)
    else:
        print("✓ Found Google Business Profile data")
        # Look for all location directories and their review files
        for location_dir in business_profile_path.glob("account-*/location-*"):
            print(f"  📍 Checking location: {location_dir.name}")

            # Find all review files in this location (reviews.json and reviews-*.json)
            location_review_files = []
            location_review_files.extend(location_dir.glob("reviews.json"))
            location_review_files.extend(location_dir.glob("reviews-*.json"))

            print(f"     Found {len(location_review_files)} review files")
            review_files.extend(location_review_files)

    print(f"\n📋 Total review files found: {len(review_files)}")
    return review_files

def get_restaurant_name_from_location(location_path):
    """Get restaurant name from location data.json file"""
    data_file = location_path / "data.json"
    if data_file.exists():
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                location_data = json.load(f)
                return location_data.get('title', 'Unknown')
        except json.JSONDecodeError:
            pass
    return 'Unknown'

def parse_reviews(json_path):
    """Parse reviews from Google Business Profile JSON"""
    print(f"\n📖 Reading {json_path.name}...")

    # Get restaurant name from the location folder
    location_path = json_path.parent
    restaurant_name = get_restaurant_name_from_location(location_path)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    reviews = []

    # The JSON structure has a "reviews" array
    review_items = data.get('reviews', [])

    for item in review_items:
        # Convert star rating from text to number
        star_rating = item.get('starRating', 'ONE')
        rating_map = {
            'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5
        }
        rating = rating_map.get(star_rating, 0)

        # Get review reply if exists
        review_reply = item.get('reviewReply', {})
        response_comment = review_reply.get('comment', '')
        response_date = review_reply.get('updateTime', '')

        # Extract review details
        review_data = {
            'restaurant': restaurant_name,
            'rating': rating,
            'comment': item.get('comment', ''),
            'reviewer_name': item.get('reviewer', {}).get('displayName', ''),
            'published_date': item.get('createTime', ''),
            'updated_date': item.get('updateTime', ''),
            'response': response_comment,
            'response_date': response_date,
            'review_id': item.get('name', '')
        }

        reviews.append(review_data)

    print(f"✓ Parsed {len(reviews)} reviews for {restaurant_name}")
    return reviews

def main():
    print("=== Google Business Profile Review Importer ===\n")

    # Look for zip files
    zip_files = list(Path('data/raw').glob('*.zip'))

    if not zip_files:
        print("❌ No zip files found in data/raw/")
        print("\nTo get your reviews:")
        print("1. Go to https://takeout.google.com")
        print("2. Select 'Google Business Profile' only")
        print("3. Download the zip file")
        print("4. Copy to: ~/dev/python-projects/review-analysis/data/raw/")
        print("\nExample copy command:")
        print("cp /mnt/c/Users/justi/Downloads/takeout*.zip data/raw/")
        return None

    # Process the most recent zip
    zip_path = sorted(zip_files)[-1]
    print(f"Processing: {zip_path.name}")

    # Extract
    extract_dir = extract_takeout_zip(zip_path)

    # Find review files
    review_files = find_review_files(extract_dir)

    if not review_files:
        print("❌ No review files found in the takeout data")
        return None

    # Parse all reviews
    all_reviews = []
    for review_file in review_files:
        reviews = parse_reviews(review_file)
        all_reviews.extend(reviews)

    if not all_reviews:
        print("❌ No reviews found for your restaurants")
        return None

    # Create DataFrame
    df = pd.DataFrame(all_reviews)

    # Parse dates (Google Business Profile uses ISO format)
    df['published_datetime'] = pd.to_datetime(df['published_date'], errors='coerce')
    df['updated_datetime'] = pd.to_datetime(df['updated_date'], errors='coerce')
    df['response_datetime'] = pd.to_datetime(df['response_date'], errors='coerce')

    # Save raw imported data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/reviews_imported_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved imported reviews to: {output_file}")
    print(f"✓ Total reviews imported: {len(df)}")

    return df

if __name__ == '__main__':
    df = main()