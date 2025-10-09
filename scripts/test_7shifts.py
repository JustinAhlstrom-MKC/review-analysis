#!/usr/bin/env python3
"""
Test script to debug 7shifts API connection.
"""

import sys
from pathlib import Path
import requests

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.config import config


def test_7shifts_connection():
    """Test the 7shifts API connection and debug issues"""

    print("=" * 60)
    print("🔍 Testing 7shifts API Connection")
    print("=" * 60)

    try:
        api_key = config.sevenshift_api_key
        company_id = config.sevenshift_company_id

        print(f"\n✓ API Key loaded: {api_key[:10]}...")
        print(f"✓ Company ID: {company_id}\n")

        # Test 1: Basic API authentication
        print("Test 1: Testing API authentication...")
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        # Try different endpoint variations to find the correct one
        print("Trying various API endpoints...\n")

        test_endpoints = [
            f"https://api.7shifts.com/v2/company/{company_id}",
            f"https://api.7shifts.com/v2/companies/{company_id}",
            "https://api.7shifts.com/v2/whoami",
            "https://api.7shifts.com/v2/users",
        ]

        for endpoint in test_endpoints:
            print(f"Testing: {endpoint}")
            response = requests.get(endpoint, headers=headers)
            print(f"  Status: {response.status_code}")
            if response.status_code == 200:
                print(f"  ✅ Success! Response: {response.json()}")
                break
            elif response.status_code in [401, 403]:
                print(f"  ❌ Auth error: {response.text}")
            elif response.status_code == 404:
                print(f"  ⚠️  Not found")
            else:
                print(f"  Response: {response.text}")
        print()

        # Test 2: Fetch users
        print("\nTest 2: Fetching users...")
        url = f"https://api.7shifts.com/v2/companies/{company_id}/users"
        params = {'active': 'true', 'limit': 100}

        print(f"Request URL: {url}")
        print(f"Params: {params}")

        response = requests.get(url, headers=headers, params=params)
        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Users endpoint accessible")
            print(f"Response structure: {list(data.keys())}")

            users = data.get('data', [])
            print(f"Number of users returned: {len(users)}\n")

            if users:
                print("Sample user data (first user):")
                print(f"Keys available: {list(users[0].keys())}")

                # Check for role information
                print("\nLooking for role information...")
                sample_user = users[0]
                print(f"Type: {sample_user.get('type')}")
                print(f"Permissions template ID: {sample_user.get('permissions_template_id')}")

                # Filter to only employees (not employers)
                employees = [u for u in users if u.get('type') == 'employee']
                print(f"\nFiltered to {len(employees)} employees (type='employee')")

                if employees:
                    print(f"\nSample employee:")
                    print(f"  Name: {employees[0].get('first_name')} {employees[0].get('last_name')}")
                    print(f"  Type: {employees[0].get('type')}")
            else:
                print("⚠️  No users returned in response")
                print(f"Full response: {data}\n")
        else:
            print(f"❌ Failed to fetch users")
            print(f"Response: {response.text}\n")

        # Test 3: Check for roles endpoint
        print("\nTest 3: Checking for roles/departments...")
        roles_endpoints = [
            f"https://api.7shifts.com/v2/companies/{company_id}/roles",
            f"https://api.7shifts.com/v2/companies/{company_id}/departments",
        ]

        for endpoint in roles_endpoints:
            print(f"Testing: {endpoint}")
            response = requests.get(endpoint, headers=headers)
            if response.status_code == 200:
                print(f"  ✅ {response.json()}")
            else:
                print(f"  Status: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_7shifts_connection()
