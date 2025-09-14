#!/usr/bin/env python3
"""
Export summary analysis of review data.
Generates analysis reports from processed dataset.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

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

def generate_employee_summary(df):
    """Generate employee mention summary"""
    # Check if employee matching columns exist
    if 'employee_matches' not in df.columns or 'mentioned_employees' not in df.columns:
        print("\n⚠️  No employee matching data found in dataset")
        return

    # Filter to reviews with employee mentions
    employee_reviews = df[df['employee_matches'] != '']

    if len(employee_reviews) == 0:
        print("\n👥 No employee mentions found in dataset")
        return

    print(f"\n👥 Employee Mention Summary:")
    print(f"Total reviews with employee mentions: {len(employee_reviews)}")

    # Count mentions per employee
    all_matches = []
    for _, row in employee_reviews.iterrows():
        matches_str = row['employee_matches']
        if matches_str:
            all_matches.extend(matches_str.split('; '))

    if all_matches:
        employee_counts = pd.Series(all_matches).value_counts()
        print(f"\nTop mentioned employees:")
        for employee, count in employee_counts.head(10).items():
            print(f"  - {employee}: {count} mentions")

def generate_detailed_summary(df):
    """Generate detailed summary report"""
    summary = {}

    # Basic stats
    summary['total_reviews'] = len(df)
    summary['average_rating'] = df['rating'].mean()
    summary['response_rate'] = (df['response'] != '').sum() / len(df)

    # By restaurant
    summary['restaurants'] = {}
    for restaurant in df['restaurant'].unique():
        rest_df = df[df['restaurant'] == restaurant]
        summary['restaurants'][restaurant] = {
            'total_reviews': len(rest_df),
            'average_rating': rest_df['rating'].mean(),
            'response_rate': (rest_df['response'] != '').sum() / len(rest_df),
            'rating_distribution': rest_df['rating'].value_counts().to_dict()
        }

    # Recent trends
    if 'published_datetime' in df.columns:
        recent_cutoff = pd.Timestamp.now() - pd.DateOffset(months=6)
        recent = df[df['published_datetime'].dt.tz_convert(None) >= recent_cutoff]
        summary['recent_6_months'] = {
            'reviews': len(recent),
            'average_rating': recent['rating'].mean() if len(recent) > 0 else 0
        }

    # Employee mentions
    if 'employee_matches' in df.columns:
        employee_reviews = df[df['employee_matches'] != '']
        all_matches = []
        for _, row in employee_reviews.iterrows():
            matches_str = row['employee_matches']
            if matches_str:
                all_matches.extend(matches_str.split('; '))

        if all_matches:
            employee_counts = pd.Series(all_matches).value_counts()
            summary['employee_mentions'] = employee_counts.to_dict()
        else:
            summary['employee_mentions'] = {}

    return summary

def export_csv_summary(df, output_file):
    """Export summary data to CSV"""
    # Create summary table for restaurants
    restaurant_summary = []
    for restaurant in df['restaurant'].unique():
        rest_df = df[df['restaurant'] == restaurant]
        restaurant_summary.append({
            'restaurant': restaurant,
            'total_reviews': len(rest_df),
            'average_rating': rest_df['rating'].mean(),
            'response_rate': (rest_df['response'] != '').sum() / len(rest_df),
            'rating_1': (rest_df['rating'] == 1).sum(),
            'rating_2': (rest_df['rating'] == 2).sum(),
            'rating_3': (rest_df['rating'] == 3).sum(),
            'rating_4': (rest_df['rating'] == 4).sum(),
            'rating_5': (rest_df['rating'] == 5).sum(),
        })

    summary_df = pd.DataFrame(restaurant_summary)
    summary_df.to_csv(output_file, index=False)
    print(f"✓ CSV summary exported to: {output_file}")

def export_json_summary(summary_dict, output_file):
    """Export detailed summary to JSON"""
    import json

    # Convert numpy types to Python types for JSON serialization
    def convert_types(obj):
        if hasattr(obj, 'item'):
            return obj.item()
        elif isinstance(obj, dict):
            return {k: convert_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_types(v) for v in obj]
        else:
            return obj

    summary_dict = convert_types(summary_dict)

    with open(output_file, 'w') as f:
        json.dump(summary_dict, f, indent=2, default=str)

    print(f"✓ JSON summary exported to: {output_file}")

def main(input_file=None):
    print("=== Review Summary Exporter ===\n")

    # Find most recent dataset file if not specified
    if not input_file:
        dataset_files = list(Path('data').glob('dataset_*.csv'))
        if not dataset_files:
            print("❌ No dataset files found in data/")
            print("Please run create_dataset.py first")
            return None
        input_file = sorted(dataset_files)[-1]
        print(f"Using most recent dataset: {input_file}")
    else:
        input_file = Path(input_file)
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            return None

    # Load dataset
    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df)} reviews from {input_file}")

    # Ensure datetime columns are parsed
    for col in ['published_datetime', 'updated_datetime', 'response_datetime']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Generate analysis
    analyze_reviews(df)
    generate_employee_summary(df)

    # Export summaries
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # CSV summary
    csv_output = f"data/summary_{timestamp}.csv"
    export_csv_summary(df, csv_output)

    # JSON summary
    detailed_summary = generate_detailed_summary(df)
    json_output = f"data/summary_{timestamp}.json"
    export_json_summary(detailed_summary, json_output)

    print(f"\n✅ Summary export complete!")
    print(f"CSV summary: {csv_output}")
    print(f"JSON summary: {json_output}")

    return df

if __name__ == '__main__':
    import sys

    # Check for input file argument
    input_file = None
    if len(sys.argv) > 1:
        input_file = sys.argv[1]

    df = main(input_file)