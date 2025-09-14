#!/usr/bin/env python3
"""
Fetch reviews for Margie's Kitchen & Cocktails and Grackle
"""

import pickle
import pandas as pd
from pathlib import Path
from datetime import datetime
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

def load_credentials():
    """Load saved credentials"""
    token_path = Path('config/token.pickle')
    if not token_path.exists():
        print("❌ No authentication token found. Run setup_auth.py first!")
        return None
    
    with open(token_path, 'rb') as token:
        creds = pickle.load(token)
    
    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def find_locations(service, account_name):
    """Find location IDs for your restaurants"""
    # This will work once API quotas are fixed
    try:
        locations = service.accounts().locations().list(
            parent=f"accounts/{account_name}"
        ).execute()
        
        location_dict = {}
        for loc in locations.get('locations', []):
            name = loc.get('locationName', 'Unknown')
            location_id = loc.get('name', '')
            location_dict[name] = location_id
            print(f"Found: {name}")
        
        return location_dict
    except Exception as e:
        print(f"Error finding locations: {e}")
        return None

def fetch_reviews(service, location_id, restaurant_name):
    """Fetch all reviews for a location"""
    print(f"\n📊 Fetching reviews for {restaurant_name}...")
    
    try:
        reviews = []
        page_token = None
        
        while True:
            # Fetch a page of reviews
            if page_token:
                response = service.accounts().locations().reviews().list(
                    parent=location_id,
                    pageToken=page_token
                ).execute()
            else:
                response = service.accounts().locations().reviews().list(
                    parent=location_id
                ).execute()
            
            # Add reviews to list
            for review in response.get('reviews', []):
                reviews.append({
                    'restaurant': restaurant_name,
                    'reviewer': review.get('reviewer', {}).get('displayName', 'Anonymous'),
                    'rating': review.get('starRating', 'UNSPECIFIED'),
                    'comment': review.get('comment', ''),
                    'create_time': review.get('createTime', ''),
                    'update_time': review.get('updateTime', ''),
                    'reply': review.get('reviewReply', {}).get('comment', '')
                })
            
            # Check for more pages
            page_token = response.get('nextPageToken')
            if not page_token:
                break
        
        print(f"✓ Fetched {len(reviews)} reviews")
        return reviews
        
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return []

def save_reviews(reviews, filename):
    """Save reviews to CSV"""
    df = pd.DataFrame(reviews)
    
    # Convert star ratings to numbers
    rating_map = {
        'ONE': 1, 'TWO': 2, 'THREE': 3, 
        'FOUR': 4, 'FIVE': 5, 'UNSPECIFIED': None
    }
    df['rating_numeric'] = df['rating'].map(rating_map)
    
    # Parse dates
    df['create_date'] = pd.to_datetime(df['create_time'], errors='coerce')
    df['update_date'] = pd.to_datetime(df['update_time'], errors='coerce')
    
    # Save to CSV
    output_path = f"data/{filename}"
    df.to_csv(output_path, index=False)
    print(f"✓ Saved to {output_path}")
    
    return df

def main():
    print("=== Google Reviews Fetcher ===\n")
    
    # Load credentials
    creds = load_credentials()
    if not creds:
        return
    
    # Build service
    service = build('mybusiness', 'v4', credentials=creds)
    
    # For now, we'll need to manually set these after finding them
    # Replace these with your actual location IDs once API is working
    locations = {
        "Margie's Kitchen & Cocktails": "locations/YOUR_LOCATION_ID_1",
        "Grackle": "locations/YOUR_LOCATION_ID_2"
    }
    
    all_reviews = []
    
    for restaurant, location_id in locations.items():
        if "YOUR_LOCATION_ID" in location_id:
            print(f"⚠️  Need to update location ID for {restaurant}")
            continue
            
        reviews = fetch_reviews(service, location_id, restaurant)
        all_reviews.extend(reviews)
    
    if all_reviews:
        # Save all reviews
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df = save_reviews(all_reviews, f"reviews_{timestamp}.csv")
        
        # Basic stats
        print("\n📈 Quick Stats:")
        print(f"Total reviews: {len(df)}")
        print(f"Average rating: {df['rating_numeric'].mean():.2f}")
        print("\nRatings by restaurant:")
        print(df.groupby('restaurant')['rating_numeric'].agg(['count', 'mean']))

if __name__ == '__main__':
    main()
