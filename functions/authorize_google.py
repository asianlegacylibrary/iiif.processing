from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from functools import reduce
import pandas as pd
from classes import Timer

# If modifying these scopes, delete the file token.pickle.
# SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly',
#           'https://www.googleapis.com/auth/drive',
#           'https://www.googleapis.com/auth/drive.metadata.readonly'
#           ]

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def filter_data(data):
    # data = data[data['title'].str.len() > 0]
    # data = data[data[['title', 'workuid']].apply(lambda x: f(*x), axis=1)]
    return data[(data['title'].str.len() > 0) & (data['workuid'].str.len() > 0)]


def clean_columns(data):
    # df = pd.DataFrame.from_records(worksheet_name.get_all_values())
    df = pd.DataFrame(data)
    df = df.rename(columns=df.iloc[0]).drop(df.index[0])
    df.columns = df.columns \
        .str.strip() \
        .str.replace(r'[^\x00-\x7f]', r'') \
        .str.lower() \
        .str.replace(r'[()#,\';]', r'') \
        .str.strip() \
        .str.replace(' ', '_')

    return df


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
                kwargs["credentials"]["acip"], SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    return sheets_service, drive_service


# @Timer(name="input data")
def get_sheet_data(service, **kwargs):
    sheet_range = f"{kwargs['sheet_input_name']}!A1:AZ"
    # get data, transform to data frame
    result = (
        service.spreadsheets().values().get(
            spreadsheetId=kwargs['spreadsheet_input_id'], range=sheet_range, majorDimension="ROWS"
        ).execute()
    )
    data = result.get("values", [])
    data = clean_columns(data)
    data = filter_data(data)

    return data


def get_all_sheet_data(service, sheet_listing):
    data_list = []
    for s in sheet_listing:
        sheet_range = f"{s['sheet_name']}!A1:Z"
        # get data, transform to data frame
        result = (
            service.spreadsheets().values().get(
                spreadsheetId=s['spreadsheet_id'], range=sheet_range, majorDimension="ROWS"
            ).execute()
        )
        data = result.get("values", [])
        data = clean_columns(data)
        data = filter_data(data)

        # print(f"{name}: {data.shape[0]}, {data.shape[1]}")
        data_list.append(data)
        del data

    final_data = pd.concat(data_list)
    del data_list

    return final_data


def write_sheet_data(service, data, output_name=None, **kwargs):
    if isinstance(data, pd.DataFrame):
        values = [data.columns.values.tolist()]
        values.extend(data.values.tolist())
    elif isinstance(data, pd.Series):
        values = [data.values.tolist()]
    else:
        return None

    if output_name is None:
        output_name = kwargs['sheet_output_name']

    sheets_meta = (service.spreadsheets().get(spreadsheetId=kwargs['spreadsheet_output_id']).execute())
    sheets = sheets_meta.get("sheets", "")

    # res = next((s for s in sheets if s['properties']['title'] == sheet_config['sheet_input_name']), None)
    if not any((s for s in sheets if s['properties']['title'] == output_name)):
        body = {
            'requests': [{
              "addSheet": {
                "properties": {
                  "title": output_name
                }
              }
            }]
        }
        sheets_batch_update(service, body, kwargs['spreadsheet_output_id'])

    body = {
        'value_input_option': 'RAW',
        'data': [{'range': output_name, 'values': values}]
    }

    sheets_batch_update(service, body, kwargs['spreadsheet_output_id'], value_update=True)


def sheets_batch_update(service, body, spreadsheet_id, value_update=False):
    if value_update:
        service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()
    else:
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet_id, body=body).execute()


def copy_input(service, **sheet_config):

    copy_sheet_to_another_spreadsheet_request_body = {
        # The ID of the spreadsheet to copy the sheet to.
        'destination_spreadsheet_id': sheet_config['spreadsheet_output_id']

        # TODO: Add desired entries to the request body.
    }

    request = service.spreadsheets().sheets().copyTo(spreadsheetId=sheet_config['spreadsheet_input_id'],
                                                     sheetId=sheet_config['sheet_input_id'],
                                                     body=copy_sheet_to_another_spreadsheet_request_body)
    response = request.execute()
    print(response)

    return {
        **sheet_config,
        **{
            'sheet_input_name': response['title'],
            'spreadsheet_input_id': sheet_config['spreadsheet_output_id']
        }
    }


def set_google_sheets(input_name=None, output_name=None, **kwargs):
    if input_name is None:
        # The ID of the spreadsheet containing the sheet to copy.
        spreadsheet_input_id = kwargs['sheets']['test_input']['spreadsheet_id']
        sheet_input_name = kwargs['sheets']['test_input']['sheet_name']
    else:
        spreadsheet_input_id = kwargs['sheets'][input_name]['spreadsheet_id']
        sheet_input_name = kwargs['sheets'][input_name]['sheet_name']

    if output_name is None:
        spreadsheet_output_id = kwargs['sheets']['test_output']['spreadsheet_id']
        sheet_output_name = kwargs['sheets']['test_output']['sheet_name']
    else:
        spreadsheet_output_id = kwargs['sheets'][output_name]['spreadsheet_id']
        sheet_output_name = kwargs['sheets'][output_name]['sheet_name']

    return {'sheet_input_name': sheet_input_name, 'sheet_output_name': sheet_output_name,
            'sheet_input_id': None, 'spreadsheet_input_id': spreadsheet_input_id,
            'spreadsheet_output_id': spreadsheet_output_id}


def get_sheet_ids(service, **sheet_config):
    # Call the Sheets API
    sheets_meta = (service.spreadsheets().get(spreadsheetId=sheet_config['spreadsheet_id']).execute())
    sheets = sheets_meta.get("sheets", "")
    dict_keys = ["properties", "title"]
    wks_list = []

    for s in sheets:
        current_sheet = reduce(dict.get, dict_keys, s)
        if sheet_config['sheet_name'] in current_sheet.lower():
            print({'sheet_id': s['properties']['sheetId'], 'sheet_name': s['properties']['title']})
            sheet_config['sheet_id'] = s['properties']['sheetId']
            wks_list.append(sheet_config)
    return wks_list


def get_sheet_id(service, **sheet_config):
    # Call the Sheets API
    sheets_meta = (service.spreadsheets().get(spreadsheetId=sheet_config['spreadsheet_input_id']).execute())
    sheets = sheets_meta.get("sheets", "")
    res = next((s for s in sheets if s['properties']['title'] == sheet_config['sheet_input_name']), None)
    if res is not None:
        sheet_config['sheet_input_id'] = res['properties']['sheetId']
    return sheet_config
