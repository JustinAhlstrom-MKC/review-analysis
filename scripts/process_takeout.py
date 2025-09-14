#!/usr/bin/env python3
"""
Process Google Business Profile takeout data for restaurant analysis.
Consolidates review data from multiple locations into a single dataframe.
"""

import json
import pandas as pd
from pathlib import Path
import zipfile
from datetime import datetime
import re
from difflib import SequenceMatcher

def load_employee_list(employee_file_path):
    """Load employee names from a file, filtering for servers, bartenders, and managers only"""
    file_path = Path(employee_file_path)

    if not file_path.exists():
        print(f"❌ Employee file not found: {employee_file_path}")
        return {}

    employees = {}

    try:
        if file_path.suffix.lower() == '.csv':
            # Load CSV and filter by roles
            df = pd.read_csv(file_path)

            # Check if we have the expected 7shifts format
            if 'First Name' in df.columns and 'Last name' in df.columns and 'Roles' in df.columns and 'Locations' in df.columns:
                # Filter for customer-facing roles only (excluding managers)
                target_roles = ['Server', 'Bartender', 'Bar Prep']

                for _, row in df.iterrows():
                    roles = str(row['Roles']).lower()
                    if any(role.lower() in roles for role in target_roles):
                        # Get employee info
                        first_name = str(row['First Name']).strip()
                        last_name = str(row['Last name']).strip()
                        locations = str(row['Locations']).lower()

                        # Skip if name is empty or 'nan'
                        if first_name and first_name != 'nan' and last_name and last_name != 'nan':
                            full_name = f"{first_name} {last_name}"

                            # Determine which restaurants this employee works at
                            works_at = []
                            if "grackle" in locations:
                                works_at.append("Grackle")
                            if "margie" in locations:
                                works_at.append("Margie's Kitchen & Cocktails")

                            # Skip default/system entries
                            if first_name.lower() in ['server', 'pm', 'bar', 'catering', 'take']:
                                continue

                            if works_at:  # Only include if they work at one of our restaurants
                                employees[first_name.lower()] = {
                                    'full_name': full_name,
                                    'first_name': first_name,
                                    'restaurants': works_at
                                }

            else:
                # Fallback to generic CSV handling - assume all locations
                if 'name' in df.columns:
                    names = df['name'].dropna().tolist()
                elif 'Name' in df.columns:
                    names = df['Name'].dropna().tolist()
                else:
                    names = df.iloc[:, 0].dropna().tolist()

                for name in names:
                    first_name = name.split()[0] if name.split() else name
                    employees[first_name.lower()] = {
                        'full_name': name,
                        'first_name': first_name,
                        'restaurants': ["Grackle", "Margie's Kitchen & Cocktails"]
                    }

        else:
            print(f"❌ Unsupported file format: {file_path.suffix}")
            return {}

        print(f"✓ Loaded {len(employees)} customer-facing employees (servers/bartenders/managers)")
        return employees

    except Exception as e:
        print(f"❌ Error loading employee file: {e}")
        return {}

def similarity_score(a, b):
    """Calculate similarity between two strings (0-1 scale)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def extract_potential_names(text):
    """Extract potential employee names from review text"""
    if not text or pd.isna(text):
        return []

    # Common patterns for server mentions
    patterns = [
        r'\b([A-Z][a-z]+)\s+(?:was|is|had|did|helped|served|took)\b',  # "Jacob was excellent"
        r'(?:server|waiter|waitress|bartender|host|hostess)\s+([A-Z][a-z]+)',  # "server Jacob"
        r'(?:our|my)?\s*(?:server|waiter|waitress|bartender|host|hostess)[,\s]+([A-Z][a-z]+)',  # "our server, Jacob"
        r'\b([A-Z][a-z]+)(?:\s+[A-Z][a-z]*)?[,\s]+(?:our|my|the)?\s*(?:server|waiter|waitress|bartender|host|hostess)',  # "Jacob, our server"
        r'(?:Thanks?|Thank\s+you),?\s+([A-Z][a-z]+)[!\.\s]',  # "Thanks Jacob!"
        r'\b([A-Z][a-z]+)\s+(?:provided|delivered|gave|recommended|suggested)',  # "Jacob provided excellent"
        r'(?:served\s+by|helped\s+by)\s+([A-Z][a-z]+)',  # "served by Jacob"
        r'\b([A-Z][a-z]+)\s+(?:at\s+the\s+)?(?:bar|front|host)',  # "Jacob at the bar"
    ]

    potential_names = []
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            name = match.group(1).strip()
            if len(name) >= 3:  # Filter out very short matches
                potential_names.append(name)

    # Also look for capitalized words that might be names (less precise)
    words = re.findall(r'\b[A-Z][a-z]{2,}\b', text)
    for word in words:
        # Skip common words that aren't names
        if word.lower() not in ['The', 'This', 'That', 'They', 'There', 'When', 'Where', 'What', 'Who', 'Why', 'How', 'And', 'But', 'Or', 'So', 'Very', 'Really', 'Great', 'Good', 'Bad', 'Nice', 'Food', 'Service', 'Restaurant', 'Place', 'Time', 'First', 'Last', 'Next', 'Best', 'Worst', 'Perfect', 'Amazing', 'Awesome', 'Terrible', 'Horrible', 'Excellent', 'Outstanding', 'Wonderful', 'Fantastic', 'Incredible']:
            potential_names.append(word)

    return list(set(potential_names))  # Remove duplicates

def match_employee_to_review(review_text, restaurant_name, employee_dict, min_similarity=0.8):
    """Match potential employee names in review text to actual employee list"""
    potential_names = extract_potential_names(review_text)
    matches = []

    for potential_name in potential_names:
        # Skip very common words that are clearly not names
        if potential_name.lower() in ['and', 'the', 'was', 'had', 'our', 'very', 'great', 'good', 'food', 'service', 'place', 'time', 'first', 'last', 'next', 'best', 'nice', 'said', 'just', 'that', 'this', 'they', 'with', 'were', 'have', 'been', 'will', 'would', 'could', 'should', 'made', 'came', 'went', 'got', 'get', 'one', 'two', 'all', 'but', 'not', 'can', 'did', 'has', 'are', 'for', 'you', 'your', 'his', 'her', 'him', 'she', 'he', 'we', 'us', 'me', 'my', 'so', 'if', 'or', 'an', 'as', 'at', 'be', 'by', 'do', 'in', 'is', 'it', 'no', 'of', 'on', 'to', 'up', 'clearly']:
            continue

        best_match = None
        best_score = 0
        best_employee_info = None

        # Only match against first names for more accuracy
        for first_name_key, employee_info in employee_dict.items():
            # Check if this employee works at the restaurant being reviewed
            if restaurant_name not in employee_info['restaurants']:
                continue

            # Match against first name only
            first_name = employee_info['first_name']
            score = similarity_score(potential_name, first_name)

            if score > best_score and score >= min_similarity:
                best_match = employee_info['full_name']
                best_score = score
                best_employee_info = employee_info

        if best_match:
            matches.append({
                'potential_name': potential_name,
                'matched_employee': best_match,
                'confidence': best_score
            })

    return matches

def add_employee_matches_to_dataframe(df, employee_dict):
    """Add employee matching columns to the dataframe"""
    if not employee_dict:
        print("⚠️  No employee list provided, skipping employee matching")
        return df

    # Filter to last 6 months for employee matching
    six_months_ago = pd.Timestamp.now() - pd.DateOffset(months=6)
    recent_mask = df['published_datetime'].dt.tz_convert(None) >= six_months_ago
    recent_df = df[recent_mask]

    print(f"\n🔍 Matching employees in {len(recent_df)} reviews from last 6 months...")
    print(f"   (Skipping {len(df) - len(recent_df)} older reviews)")
    print(f"   (Location-aware matching: only matching employees to their assigned restaurants)")

    # Initialize new columns for all rows
    df['mentioned_employees'] = ''
    df['employee_matches'] = ''
    df['employee_confidence'] = ''

    matches_found = 0

    # Only process recent reviews
    for idx, row in recent_df.iterrows():
        restaurant_name = row.get('restaurant', '')
        comment_matches = match_employee_to_review(
            row.get('comment', ''),
            restaurant_name,
            employee_dict
        )

        if comment_matches:
            matches_found += 1
            mentioned = [m['potential_name'] for m in comment_matches]
            matched = [m['matched_employee'] for m in comment_matches]
            confidence = [f"{m['confidence']:.2f}" for m in comment_matches]

            df.at[idx, 'mentioned_employees'] = '; '.join(mentioned)
            df.at[idx, 'employee_matches'] = '; '.join(matched)
            df.at[idx, 'employee_confidence'] = '; '.join(confidence)

    print(f"✓ Found employee mentions in {matches_found} recent reviews")

    # Generate summary for recent matches only
    if matches_found > 0:
        print(f"\n👥 Employee Mention Summary (Last 6 Months):")

        # Count mentions per employee from recent reviews only
        all_matches = []
        for idx in recent_df.index:
            matches_str = df.at[idx, 'employee_matches']
            if matches_str:
                all_matches.extend(matches_str.split('; '))

        if all_matches:
            employee_counts = pd.Series(all_matches).value_counts()
            for employee, count in employee_counts.head(10).items():
                # Show which restaurant(s) they work at
                first_name = employee.split()[0].lower()
                if first_name in employee_dict:
                    restaurants = ', '.join(employee_dict[first_name]['restaurants'])
                    print(f"  - {employee} ({restaurants}): {count} mentions")
                else:
                    print(f"  - {employee}: {count} mentions")

    return df

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

def analyze_reviews(df):
    """Generate basic analysis of reviews"""
    print("\n📊 REVIEW ANALYSIS")
    print("=" * 50)
    
    # Overall stats
    print(f"\n📈 Overall Statistics:")
    print(f"Total reviews: {len(df)}")
    print(f"Average rating: {df['rating'].mean():.2f}")
    print(f"Reviews with responses: {(df['response'] != '').sum()}")
    
    # By restaurant
    print(f"\n🍽️  By Restaurant:")
    for restaurant in df['restaurant'].unique():
        rest_df = df[df['restaurant'] == restaurant]
        print(f"\n{restaurant}:")
        print(f"  - Total reviews: {len(rest_df)}")
        print(f"  - Average rating: {rest_df['rating'].mean():.2f}")
        print(f"  - Response rate: {(rest_df['response'] != '').sum() / len(rest_df) * 100:.1f}%")
        
        # Rating distribution
        rating_dist = rest_df['rating'].value_counts().sort_index()
        print(f"  - Rating distribution:")
        for rating, count in rating_dist.items():
            stars = '⭐' * int(rating)
            print(f"    {rating}: {stars} ({count} reviews)")
    
    # Recent trends
    if 'published_datetime' in df.columns:
        df['year_month'] = df['published_datetime'].dt.tz_convert(None).dt.to_period('M')
        recent_cutoff = pd.Timestamp.now() - pd.DateOffset(months=6)
        recent = df[df['published_datetime'].dt.tz_convert(None) >= recent_cutoff]
        if len(recent) > 0:
            print(f"\n📅 Last 6 Months:")
            print(f"  - Reviews: {len(recent)}")
            print(f"  - Average rating: {recent['rating'].mean():.2f}")

def main(employee_file=None):
    print("=== Google Business Profile Review Processor ===\n")

    # Load employee dictionary if provided
    employee_dict = {}
    if employee_file:
        employee_dict = load_employee_list(employee_file)

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
        return
    
    # Process the most recent zip
    zip_path = sorted(zip_files)[-1]
    print(f"Processing: {zip_path.name}")
    
    # Extract
    extract_dir = extract_takeout_zip(zip_path)
    
    # Find review files
    review_files = find_review_files(extract_dir)
    
    if not review_files:
        print("❌ No review files found in the takeout data")
        return
    
    # Parse all reviews
    all_reviews = []
    for review_file in review_files:
        reviews = parse_reviews(review_file)
        all_reviews.extend(reviews)
    
    if not all_reviews:
        print("❌ No reviews found for your restaurants")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_reviews)
    
    # Parse dates (Google Business Profile uses ISO format)
    df['published_datetime'] = pd.to_datetime(df['published_date'], errors='coerce')
    df['updated_datetime'] = pd.to_datetime(df['updated_date'], errors='coerce')
    df['response_datetime'] = pd.to_datetime(df['response_date'], errors='coerce')

    # Add employee matching
    df = add_employee_matches_to_dataframe(df, employee_dict)

    # Save processed data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/reviews_processed_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved processed reviews to: {output_file}")
    
    # Analyze
    analyze_reviews(df)
    
    return df

if __name__ == '__main__':
    # Check for employee file argument
    import sys
    employee_file = None
    if len(sys.argv) > 1:
        employee_file = sys.argv[1]

    df = main(employee_file)
