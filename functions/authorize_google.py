from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from functools import reduce
from config.config import conf_gs

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# 'https://www.googleapis.com/auth/drive',
# 'https://www.googleapis.com/auth/drive.metadata.readonly'


def authorize_google(**kwargs):
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                kwargs["credentials"]["nlm"], SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    return sheets_service, drive_service


def get_sheet_data():
    # 1. Connectors ##################################
    # connect to GS -----------------------------------------------
    # authorize google, for google sheets and google drive
    SHEETS, DRIVE = authorize_google(**conf_gs)

    # Call the Sheets API
    sheet = SHEETS.spreadsheets()
    spreadsheet_name = conf_gs['sheet_mongolia_test']
    sheets_meta = (
        SHEETS.spreadsheets().get(spreadsheetId=spreadsheet_name).execute()
    )
    sheets = sheets_meta.get("sheets", "")
    print(sheets)
    dict_keys = ["properties", "title"]
    wks_list = []
    ramachandra = None
    for s in sheets:
        current_sheet = reduce(dict.get, dict_keys, s)
        if conf_gs["sheet_names_filter"] in current_sheet.lower():
            wks_list.append(current_sheet)
            print(current_sheet)
    data_list = []
    for name in wks_list:
        sheet_range = f"{name}!A1:Z"
        # get data, transform to data frame
        result = (
            sheet.values()
                .get(
                spreadsheetId=spreadsheet_name, range=sheet_range, majorDimension="ROWS"
            )
                .execute()
        )
        data = result.get("values", [])
    # for s in sheets:
    #     print(s)
    #     current_sheet = reduce(dict.get, dict_keys, s)
    #     if conf_gs["sheet_mongolia_filter"] == current_sheet.lower():
    #         ramachandra = current_sheet

    # data_list = []
    # sheet_range = f"{ramachandra}!A1:Z"
    # print(sheet_range)
    # # get data, transform to data frame
    # # result = SHEETS.spreadsheets().values().get(spreadsheetId=s, range=sheet_range, majorDimension="ROWS").execute()
    # result = SHEETS.spreadsheets().values().get(spreadsheetId=s, range=sheet_range).execute()
    # print(result)
    # data = result.get("values", [])

    print(data)
    quit()
