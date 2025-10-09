#!/usr/bin/env python3
"""
Google Sheets API client for writing review data.
"""

from typing import List, Dict, Any
from datetime import datetime


class GoogleSheetsClient:
    """Client for Google Sheets API"""

    def __init__(self, auth_manager, sheet_id: str):
        self.auth_manager = auth_manager
        self.sheet_id = sheet_id
        self._service = None

    @property
    def service(self):
        """Lazy-load the API service"""
        if not self._service:
            self._service = self.auth_manager.get_sheets_service()
        return self._service

    def create_or_clear_sheet(self, tab_name: str, headers: List[str] = None):
        """Create a new tab or clear existing one, optionally add headers"""
        try:
            # Try to get the sheet
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            sheets = sheet_metadata.get('sheets', [])
            sheet_exists = any(s['properties']['title'] == tab_name for s in sheets)

            if sheet_exists:
                # Clear existing sheet
                print(f"🧹 Clearing existing sheet: {tab_name}")
                self.service.spreadsheets().values().clear(
                    spreadsheetId=self.sheet_id,
                    range=tab_name
                ).execute()
            else:
                # Create new sheet
                print(f"📝 Creating new sheet: {tab_name}")
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.sheet_id,
                    body={
                        'requests': [{
                            'addSheet': {
                                'properties': {'title': tab_name}
                            }
                        }]
                    }
                ).execute()

            # Add headers if provided
            if headers:
                self.write_rows(tab_name, [headers], start_row=1)
                self.format_header_row(tab_name)

        except Exception as e:
            print(f"❌ Error creating/clearing sheet {tab_name}: {e}")
            raise

    def write_rows(self, tab_name: str, rows: List[List[Any]], start_row: int = 1):
        """Write rows to a sheet tab"""
        if not rows:
            return

        try:
            range_name = f"{tab_name}!A{start_row}"

            self.service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=range_name,
                valueInputOption='RAW',
                body={'values': rows}
            ).execute()

            print(f"✅ Wrote {len(rows)} rows to {tab_name}")

        except Exception as e:
            print(f"❌ Error writing to sheet {tab_name}: {e}")
            raise

    def format_header_row(self, tab_name: str):
        """Apply formatting to the header row"""
        try:
            # Get sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            sheet_id = None
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == tab_name:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                return

            # Format header row
            requests = [
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': 1
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                                'textFormat': {
                                    'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0},
                                    'bold': True
                                }
                            }
                        },
                        'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                    }
                },
                {
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheet_id,
                            'gridProperties': {'frozenRowCount': 1}
                        },
                        'fields': 'gridProperties.frozenRowCount'
                    }
                }
            ]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': requests}
            ).execute()

        except Exception as e:
            print(f"⚠️  Could not format header row: {e}")

    def add_data_validation(self, tab_name: str, column_letter: str, values: List[str], start_row: int = 2):
        """Add dropdown data validation to a column"""
        try:
            # Get sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            sheet_id = None
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == tab_name:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                return

            # Convert column letter to index
            col_index = ord(column_letter.upper()) - ord('A')

            # Create validation rule
            requests = [{
                'setDataValidation': {
                    'range': {
                        'sheetId': sheet_id,
                        'startRowIndex': start_row - 1,
                        'startColumnIndex': col_index,
                        'endColumnIndex': col_index + 1
                    },
                    'rule': {
                        'condition': {
                            'type': 'ONE_OF_LIST',
                            'values': [{'userEnteredValue': v} for v in values]
                        },
                        'showCustomUi': True,
                        'strict': False
                    }
                }
            }]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': requests}
            ).execute()

            print(f"✅ Added dropdown validation to column {column_letter} in {tab_name}")

        except Exception as e:
            print(f"⚠️  Could not add data validation: {e}")

    def apply_conditional_formatting(self, tab_name: str):
        """Apply conditional formatting for ratings"""
        try:
            # Get sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            sheet_id = None
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == tab_name:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                return

            # Rating is in column E (index 4) after column reorder
            requests = [
                # Red for 1-2 star reviews
                {
                    'addConditionalFormatRule': {
                        'rule': {
                            'ranges': [{
                                'sheetId': sheet_id,
                                'startColumnIndex': 4,
                                'endColumnIndex': 5,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'NUMBER_LESS_THAN_EQ',
                                    'values': [{'userEnteredValue': '2'}]
                                },
                                'format': {
                                    'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                                }
                            }
                        },
                        'index': 0
                    }
                },
                # Yellow for 3 star reviews
                {
                    'addConditionalFormatRule': {
                        'rule': {
                            'ranges': [{
                                'sheetId': sheet_id,
                                'startColumnIndex': 4,
                                'endColumnIndex': 5,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'NUMBER_EQ',
                                    'values': [{'userEnteredValue': '3'}]
                                },
                                'format': {
                                    'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.8}
                                }
                            }
                        },
                        'index': 1
                    }
                },
                # Green for 5 star reviews
                {
                    'addConditionalFormatRule': {
                        'rule': {
                            'ranges': [{
                                'sheetId': sheet_id,
                                'startColumnIndex': 4,
                                'endColumnIndex': 5,
                                'startRowIndex': 1
                            }],
                            'booleanRule': {
                                'condition': {
                                    'type': 'NUMBER_EQ',
                                    'values': [{'userEnteredValue': '5'}]
                                },
                                'format': {
                                    'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}
                                }
                            }
                        },
                        'index': 2
                    }
                }
            ]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': requests}
            ).execute()

            print(f"✅ Applied conditional formatting to {tab_name}")

        except Exception as e:
            print(f"⚠️  Could not apply conditional formatting: {e}")

    def format_review_sheet(self, tab_name: str):
        """
        Apply comprehensive formatting to review sheet:
        - Column widths (Restaurant auto-fit, Rating 60px, Running Avg columns 100px, Reviewer Name 140px, Review/Response Text 350px)
        - Text wrapping for Review Text and Response Text
        - Vertical align all cells to top
        - Conditional formatting for ratings
        """
        try:
            # Get sheet ID
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            sheet_id = None
            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == tab_name:
                    sheet_id = sheet['properties']['sheetId']
                    break

            if sheet_id is None:
                print(f"⚠️  Sheet {tab_name} not found")
                return

            # Column indices (0-based):
            # A=0: Date Posted
            # B=1: Date Updated
            # C=2: Review Month
            # D=3: Reviewer Name (140px)
            # E=4: Rating (60px)
            # F=5: Running Avg (100px)
            # G=6: Running Avg (3 dec) (100px)
            # H=7: Review Text (350px, wrap)
            # I=8: Response Text (350px, wrap)
            # J=9: Response Date
            # K=10: Notes
            # L=11: Review ID
            # M=12: Restaurant (auto-fit)

            requests = [
                # Set Rating column (E) width to 60px
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 4,
                            'endIndex': 5
                        },
                        'properties': {'pixelSize': 60},
                        'fields': 'pixelSize'
                    }
                },
                # Set Running Avg column (F) width to 100px
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 5,
                            'endIndex': 6
                        },
                        'properties': {'pixelSize': 100},
                        'fields': 'pixelSize'
                    }
                },
                # Set Running Avg (3 dec) column (G) width to 100px
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 6,
                            'endIndex': 7
                        },
                        'properties': {'pixelSize': 100},
                        'fields': 'pixelSize'
                    }
                },
                # Set Reviewer Name column (D) width to 140px
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 3,
                            'endIndex': 4
                        },
                        'properties': {'pixelSize': 140},
                        'fields': 'pixelSize'
                    }
                },
                # Set Review Text column (H) width to 350px
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 7,
                            'endIndex': 8
                        },
                        'properties': {'pixelSize': 350},
                        'fields': 'pixelSize'
                    }
                },
                # Set Response Text column (I) width to 350px
                {
                    'updateDimensionProperties': {
                        'range': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 8,
                            'endIndex': 9
                        },
                        'properties': {'pixelSize': 350},
                        'fields': 'pixelSize'
                    }
                },
                # Auto-resize Restaurant column (M)
                {
                    'autoResizeDimensions': {
                        'dimensions': {
                            'sheetId': sheet_id,
                            'dimension': 'COLUMNS',
                            'startIndex': 12,
                            'endIndex': 13
                        }
                    }
                },
                # Set text wrapping for Review Text column (H)
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startColumnIndex': 7,
                            'endColumnIndex': 8,
                            'startRowIndex': 1  # Skip header
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'wrapStrategy': 'WRAP',
                                'verticalAlignment': 'TOP'
                            }
                        },
                        'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'
                    }
                },
                # Set text wrapping for Response Text column (I)
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startColumnIndex': 8,
                            'endColumnIndex': 9,
                            'startRowIndex': 1  # Skip header
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'wrapStrategy': 'WRAP',
                                'verticalAlignment': 'TOP'
                            }
                        },
                        'fields': 'userEnteredFormat(wrapStrategy,verticalAlignment)'
                    }
                },
                # Set vertical alignment to TOP for all cells
                {
                    'repeatCell': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0
                        },
                        'cell': {
                            'userEnteredFormat': {
                                'verticalAlignment': 'TOP'
                            }
                        },
                        'fields': 'userEnteredFormat.verticalAlignment'
                    }
                }
            ]

            # Apply all formatting requests
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': requests}
            ).execute()

            # Apply conditional formatting for ratings
            self.apply_conditional_formatting(tab_name)

            print(f"✅ Applied formatting to {tab_name}")

        except Exception as e:
            print(f"⚠️  Could not apply formatting: {e}")

    def add_filter_view(self, tab_name: str):
        """
        Add a filter view to a sheet tab.
        This creates the basic filter with dropdowns on each column header.
        The frozen header row is already set by format_header_row().
        """
        try:
            # Get sheet ID and row count
            sheet_metadata = self.service.spreadsheets().get(
                spreadsheetId=self.sheet_id
            ).execute()

            sheet_id = None
            row_count = 1000  # Default
            col_count = 20    # Default

            for sheet in sheet_metadata.get('sheets', []):
                if sheet['properties']['title'] == tab_name:
                    sheet_id = sheet['properties']['sheetId']
                    grid_props = sheet['properties'].get('gridProperties', {})
                    row_count = grid_props.get('rowCount', 1000)
                    col_count = grid_props.get('columnCount', 20)
                    break

            if sheet_id is None:
                print(f"⚠️  Sheet {tab_name} not found")
                return

            # Set basic filter on the sheet
            # This applies to all rows starting from row 1 (header is row 0)
            requests = [{
                'setBasicFilter': {
                    'filter': {
                        'range': {
                            'sheetId': sheet_id,
                            'startRowIndex': 0,
                            'endRowIndex': row_count,
                            'startColumnIndex': 0,
                            'endColumnIndex': col_count
                        }
                    }
                }
            }]

            self.service.spreadsheets().batchUpdate(
                spreadsheetId=self.sheet_id,
                body={'requests': requests}
            ).execute()

            print(f"✅ Added filter view to {tab_name}")

        except Exception as e:
            print(f"⚠️  Could not add filter view: {e}")

    def get_sheet_url(self) -> str:
        """Get the URL to the Google Sheet"""
        return f"https://docs.google.com/spreadsheets/d/{self.sheet_id}"
