#!/usr/bin/env python3
"""
Initial setup script for Google Business Profile API authentication
Run this once to authenticate and save your token
"""

import os
import pickle
from pathlib import Path
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# API Scopes needed for reading reviews
SCOPES = [
    'https://www.googleapis.com/auth/business.manage',
]

def authenticate():
    """Handles the OAuth flow and returns authenticated service"""
    creds = None
    token_path = Path('config/token.pickle')
    creds_path = Path('config/credentials.json')
    
    # Check if we have a saved token
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
            print("✓ Found existing authentication token")
    
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Token expired, refreshing...")
            creds.refresh(Request())
        else:
            if not creds_path.exists():
                print("❌ ERROR: credentials.json not found!")
                print("Please ensure you've copied your OAuth credentials to config/credentials.json")
                return None
                
            print("Starting authentication flow...")
            print("A browser window will open for Google sign-in")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
            print("✓ Authentication successful!")
        
        # Save the credentials for the next run
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
            print("✓ Token saved for future use")
    
    return creds

def list_accounts(creds):
    """List all accessible Google Business Profile accounts"""
    try:
        # Build the account management service
        service = build('mybusinessaccountmanagement', 'v1', credentials=creds)
        
        # List accounts
        print("\n📍 Finding your business accounts...")
        accounts = service.accounts().list().execute()
        
        if 'accounts' not in accounts:
            print("No accounts found. Make sure you're logged in with the correct Google account.")
            return None
            
        print(f"\nFound {len(accounts['accounts'])} account(s):")
        for acc in accounts['accounts']:
            print(f"  - {acc['accountName']}")
            print(f"    Name: {acc.get('accountDisplayName', 'N/A')}")
            print(f"    Type: {acc.get('type', 'N/A')}")
            
        return accounts['accounts']
        
    except Exception as e:
        print(f"❌ Error accessing accounts: {e}")
        return None

def main():
    print("=== Google Business Profile API Setup ===\n")
    
    # Authenticate
    creds = authenticate()
    if not creds:
        return
    
    # List available accounts
    accounts = list_accounts(creds)
    
    if accounts:
        print("\n✅ Setup complete! You can now use these credentials in your scripts.")
        print("Next step: Create a script to fetch reviews for your locations.")

if __name__ == '__main__':
    main()
