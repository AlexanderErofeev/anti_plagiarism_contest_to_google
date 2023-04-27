from Anti_plagiarism_settings import *
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials


def connection_to_sheets():
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, SCOPES)
    return build('sheets', 'v4', credentials=credentials)


def update_value(service, cell, value):
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        valueInputOption='USER_ENTERED',
        range=LIST_NAME + '!' + cell,
        body={"values": [[value]]}
    ).execute()


def update_row(service, cell, values):
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        valueInputOption='USER_ENTERED',
        range=LIST_NAME + '!' + cell,
        body={"values": [values]}
    ).execute()


def alignment(service):
    body = {
        "requests": [
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheetId,
                        "dimension": "COLUMNS",
                    }
                }
            },
            {
                "autoResizeDimensions": {
                    "dimensions": {
                        "sheetId": sheetId,
                        "dimension": "ROWS",
                    }
                }
            }
        ]
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


def clear_table(service):
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=LIST_NAME,
    ).execute()


# update_value('A30', f'=ГИПЕРССЫЛКА("https://www.Google.com"; "Google")')
