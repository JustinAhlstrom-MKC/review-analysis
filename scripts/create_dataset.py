#!/usr/bin/env python3
"""
Create analysis dataset with employee matching.
Processes imported reviews and adds employee information.
"""

import pandas as pd
from pathlib import Path
import re
from difflib import SequenceMatcher
from datetime import datetime

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

    return df

def main(employee_file=None, input_file=None):
    print("=== Review Dataset Creator ===\n")

    # Load employee dictionary if provided
    employee_dict = {}
    if employee_file:
        employee_dict = load_employee_list(employee_file)

    # Find most recent imported reviews file if not specified
    if not input_file:
        import_files = list(Path('data').glob('reviews_imported_*.csv'))
        if not import_files:
            print("❌ No imported review files found in data/")
            print("Please run import_reviews.py first")
            return None
        input_file = sorted(import_files)[-1]
        print(f"Using most recent import: {input_file}")
    else:
        input_file = Path(input_file)
        if not input_file.exists():
            print(f"❌ Input file not found: {input_file}")
            return None

    # Load imported reviews
    df = pd.read_csv(input_file)
    print(f"✓ Loaded {len(df)} reviews from {input_file}")

    # Ensure datetime columns are parsed
    for col in ['published_datetime', 'updated_datetime', 'response_datetime']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Add employee matching
    df = add_employee_matches_to_dataframe(df, employee_dict)

    # Save processed dataset
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"data/dataset_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\n✓ Saved analysis dataset to: {output_file}")

    return df

if __name__ == '__main__':
    import sys

    # Check for employee file argument
    employee_file = None
    input_file = None

    if len(sys.argv) > 1:
        employee_file = sys.argv[1]
    if len(sys.argv) > 2:
        input_file = sys.argv[2]

    df = main(employee_file, input_file)