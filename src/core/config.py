#!/usr/bin/env python3
"""
Configuration management for the Review Analysis system.
Loads settings from YAML and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class RestaurantConfig:
    """Configuration for a single restaurant"""
    name: str
    sheet_name: str
    location_id: str


class Config:
    """Central configuration manager"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config_dir = self.project_root / "config"
        self.credentials_dir = self.config_dir / "credentials"

        # Load YAML settings
        settings_path = self.config_dir / "settings.yaml"
        with open(settings_path, 'r') as f:
            self.settings = yaml.safe_load(f)

        # Load environment variables
        self._load_env()

    def _load_env(self):
        """Load environment variables from .env file if it exists"""
        env_file = self.project_root / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()

    @property
    def google_credentials_path(self) -> Path:
        """Path to Google OAuth credentials"""
        return self.credentials_dir / "google_oauth.json"

    @property
    def google_token_path(self) -> Path:
        """Path to Google OAuth token"""
        return self.credentials_dir / "google_token.pickle"

    @property
    def sheet_id(self) -> str:
        """Google Sheet ID from environment"""
        sheet_id = os.getenv('SHEET_ID')
        if not sheet_id:
            raise ValueError("SHEET_ID not set in environment")
        return sheet_id

    @property
    def sevenshift_api_key(self) -> str:
        """7shifts API key from environment"""
        api_key = os.getenv('SEVENSHIFT_API_KEY')
        if not api_key:
            raise ValueError("SEVENSHIFT_API_KEY not set in environment")
        return api_key

    @property
    def sevenshift_company_id(self) -> str:
        """7shifts company ID from environment"""
        company_id = os.getenv('SEVENSHIFT_COMPANY_ID')
        if not company_id:
            raise ValueError("SEVENSHIFT_COMPANY_ID not set in environment")
        return company_id

    @property
    def google_business_account_id(self) -> str:
        """Google Business Profile account ID from environment"""
        account_id = os.getenv('GOOGLE_BUSINESS_ACCOUNT_ID')
        if not account_id:
            raise ValueError("GOOGLE_BUSINESS_ACCOUNT_ID not set in environment")
        return account_id

    def get_restaurants(self) -> List[RestaurantConfig]:
        """Get list of configured restaurants"""
        restaurants = []
        for r in self.settings['restaurants']:
            location_id = os.getenv(r['location_id_env'])
            if not location_id:
                raise ValueError(f"{r['location_id_env']} not set in environment")

            restaurants.append(RestaurantConfig(
                name=r['name'],
                sheet_name=r['sheet_name'],
                location_id=location_id
            ))
        return restaurants

    @property
    def review_columns(self) -> List[str]:
        """Column headers for review sheets"""
        return self.settings['sheets']['review_columns']

    @property
    def employee_tab_name(self) -> str:
        """Name of employee tab in sheet"""
        return self.settings['sheets']['employee_tab']

    @property
    def dashboard_tab_name(self) -> str:
        """Name of dashboard tab in sheet"""
        return self.settings['sheets']['dashboard_tab']

    @property
    def employee_roles(self) -> List[str]:
        """Roles to include from 7shifts"""
        return self.settings['sevenshift']['employee_roles']

    @property
    def trend_periods(self) -> List[int]:
        """Analysis trend periods in days"""
        return self.settings['analysis']['trend_periods']


# Global config instance
config = Config()
