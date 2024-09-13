import os
import pickle
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v1.api.synthetics_api import SyntheticsApi
from google_auth_oauthlib.flow import InstalledAppFlow
from prettytable import PrettyTable
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Load environment variables
load_dotenv()
configuration = Configuration()
configuration.api_key['apiKeyAuth'] = os.getenv('DATADOG_API_KEY')
configuration.api_key['appKeyAuth'] = os.getenv('DATADOG_APP_KEY')

# Explicitly define the Datadog URL
configuration.host = "https://us5.datadoghq.com/"

# Create an API client and use it to list synthetics tests
with ApiClient(configuration) as api_client:
    api_instance = SyntheticsApi(api_client)
    response = api_instance.list_tests()

    # Create a PrettyTable object for formatted output
    table = PrettyTable()
    table.field_names = [
        "Test Name", "Locations Count", "Retry Count",
        "Retry Interval", "Min Failure Duration", "Min Location Failed", "Tags", "Message"
    ]

    rows = []
    for test in response['tests']:
        options = test.get('options', {})
        retry = options.get('retry', {})
        monitor_options = options.get('monitor_options', {})

        rows.append([
            test['name'],  # Test Name
            len(test['locations']), # Location Count
            retry.get('count', ''),  # Retry Count
            retry.get('interval', ''),  # Retry Interval
            options.get('min_failure_duration', ''),  # Min Failure Duration
            options.get('min_location_failed', ''),  # Min Location Failed
            ', '.join(test.get('tags', [])),  # Tags
            test.get('message', '')  # Message
        ])

    # Add rows to PrettyTable
    table.add_rows(rows)

    # Print the table
    print(table)

    # Save data to Google Sheet
    # Replace 'YOUR_SPREADSHEET_ID' with your actual Google Sheets spreadsheet ID
    SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'
    RANGE_NAME = 'Sheet1!A1'  # Adjust as needed

    # Authenticate and build the service
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', ['https://www.googleapis.com/auth/spreadsheets']
            )
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Prepare data for Google Sheets
    values = [table.field_names] + rows

    # Update the Google Sheet
    body = {
        'values': values
    }
    result = service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=RANGE_NAME,
        valueInputOption='RAW',
        body=body
    ).execute()

    print(f"{result.get('updatedCells')} cells updated.")
