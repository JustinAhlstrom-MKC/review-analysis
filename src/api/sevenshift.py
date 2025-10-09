#!/usr/bin/env python3
"""
7shifts API client for fetching employee data.
"""

import requests
from typing import List, Dict, Any


class SevenShiftClient:
    """Client for 7shifts API"""

    BASE_URL = "https://api.7shifts.com/v2"

    def __init__(self, api_key: str, company_id: str):
        self.api_key = api_key
        self.company_id = company_id
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def fetch_employees(self, roles: List[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch employees from 7shifts with their role and location assignments.

        Args:
            roles: List of role names to filter (e.g., ['Server', 'Bartender'])

        Returns:
            List of employee dictionaries
        """
        print("👥 Fetching employee list from 7shifts...")

        try:
            # Fetch all active users of type 'employee'
            url = f"{self.BASE_URL}/company/{self.company_id}/users"
            params = {
                'active': 'true',
                'type': 'employee',  # Only fetch employees, not employers
                'limit': 100
            }

            all_users = []
            cursor = None

            # Handle pagination
            while True:
                if cursor:
                    params['cursor'] = cursor

                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                users = data.get('data', [])
                all_users.extend(users)

                # Check for next page
                meta = data.get('meta', {})
                cursor_data = meta.get('cursor', {})
                cursor = cursor_data.get('next')

                if not cursor:
                    break

            # Filter to only active users (double-check since API param may not always work)
            active_users = [u for u in all_users if u.get('active', False)]

            print(f"   Fetched {len(active_users)} active users (filtered from {len(all_users)} total), enriching with assignments...")

            # Parse employees and fetch their assignments
            employees = []
            for i, user in enumerate(active_users):
                # Show progress for large datasets
                if (i + 1) % 50 == 0:
                    print(f"   Processing {i + 1}/{len(active_users)}...")

                employee = self._parse_employee_with_assignments(user)

                # Filter by role if specified
                if roles:
                    employee_roles = employee.get('role', '')
                    if not any(role.lower() in employee_roles.lower() for role in roles):
                        continue

                employees.append(employee)

            print(f"✅ Fetched {len(employees)} employees from 7shifts")
            if roles and len(employees) < len(all_users):
                print(f"   Filtered by roles: {', '.join(roles)}")

            return employees

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching employees from 7shifts: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"   Response: {e.response.text}")
            raise

    def _parse_employee_with_assignments(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse employee data and fetch their assignments"""

        # Get basic user info
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()
        phone = user_data.get('mobile_number', '')
        user_id = user_data.get('id', '')

        # Fetch assignments for this user
        assignments = self._fetch_user_assignments(user_id)

        # Extract locations and roles from assignments
        locations = []
        roles = []

        if assignments:
            # Get location names
            for loc in assignments.get('locations', []):
                locations.append(loc.get('name', ''))

            # Get role names, prioritize primary role
            role_list = assignments.get('roles', [])
            primary_roles = [r for r in role_list if r.get('is_primary', False)]
            other_roles = [r for r in role_list if not r.get('is_primary', False)]

            # Add primary roles first, then others
            for role in primary_roles + other_roles:
                role_name = role.get('name', '')
                if role_name and role_name not in roles:
                    roles.append(role_name)

        return {
            'id': user_id,
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'role': ', '.join(roles) if roles else 'Employee',
            'locations': ', '.join(locations) if locations else '',
            'email': user_data.get('email', ''),
            'phone': phone,
        }

    def _fetch_user_assignments(self, user_id: str) -> Dict[str, Any]:
        """Fetch assignments (locations, departments, roles) for a specific user"""
        try:
            url = f"{self.BASE_URL}/company/{self.company_id}/users/{user_id}/assignments"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            else:
                # If assignments not found, return empty
                return {}

        except Exception as e:
            # Silently handle errors for individual assignment fetches
            return {}

    def _parse_employee(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse a single employee from API response (without assignments)"""

        # Get name - 7shifts uses first_name/last_name (not firstname/lastname)
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        full_name = f"{first_name} {last_name}".strip()

        # Role information is not included in the user endpoint
        # Would need to fetch from /roles endpoint and cross-reference
        # For now, using user type
        user_type = user_data.get('type', 'employee')

        # Phone number field
        phone = user_data.get('mobile_number', '')

        return {
            'id': user_data.get('id', ''),
            'first_name': first_name,
            'last_name': last_name,
            'full_name': full_name,
            'role': user_type,  # This will be 'employee' or 'employer'
            'locations': '',  # Location data not available in users endpoint
            'email': user_data.get('email', ''),
            'phone': phone,
        }

    def get_locations(self) -> List[Dict[str, Any]]:
        """Fetch all locations for the company"""
        try:
            url = f"{self.BASE_URL}/company/{self.company_id}/locations"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            data = response.json()
            return data.get('data', [])

        except requests.exceptions.RequestException as e:
            print(f"⚠️  Could not fetch locations: {e}")
            return []
