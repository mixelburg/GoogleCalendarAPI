import calendar
import os
import sys
from datetime import datetime
from typing import Any

from tap import Tap
from termcolor import colored

from dateutil import parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

CLIENT_CONFIG = {
    "installed": {
        "client_id": "178991169831-vdlao4hqsaehsockujlsdgfqd6ufjl61.apps.googleusercontent.com",
        "project_id": "upbeat-legacy-279407",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": [
            "urn:ietf:wg:oauth:2.0:oob",
            "http://localhost"
        ]
    }
}

TOKEN_FILE_NAME = "token.json"

SECONDS_IN_HOUR = 3600


def get_red(text: str):
    return colored(text, "red")


def get_green(text: str):
    return colored(text, "green")


class Parser(Tap):
    add_help = True
    _current_date = datetime.now()
    payment: int = 45
    verbose: bool = False
    year: int = _current_date.year
    month: int = _current_date.month
    search: list = ['work']
    ignore_case: bool = True

    def configure(self) -> None:
        self.add_argument('-v', '--verbose',
                          help='Be verbose.')
        self.add_argument('-p', '--payment',
                          help='hourly payment')
        self.add_argument('-y', '--year',
                          help='year to count hours in, this year if not specified')
        self.add_argument('-m', '--month',
                          help='month to count hours in, this year if not specified ')
        self.add_argument('-s', '--search',
                          help='words in event summary to search for, default = "work"')
        self.add_argument('-i', '--ignore_case',
                          help='ignore case in search words')

    def process_args(self) -> None:
        if self.month < 1 or self.month > 12:
            raise ValueError('month has to be between 1 and 12')
        if self.year < 1900:
            raise ValueError('you are not so old')
        if self.payment <= 35:
            raise ValueError('Bad joke')


def get_creds() -> Any:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE_NAME):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE_NAME, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_config(CLIENT_CONFIG, SCOPES)
            # flow = InstalledAppFlow.from_client_secrets_file(
            #     'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(TOKEN_FILE_NAME, 'w') as token:
            token.write(creds.to_json())

    return creds


def main():
    try:
        args = Parser().parse_args()
    except ValueError as e:
        print(get_red(str(e)))
        return

    service = build('calendar', 'v3', credentials=get_creds())

    first_day = datetime(year=args.year, month=args.month,
                         day=1) \
                    .isoformat() + 'Z'
    last_day = datetime(year=args.year, month=args.month,
                        day=calendar.monthrange(args.year, args.month)[1])\
                   .isoformat() + 'Z'

    events_result = service.events().list(calendarId='primary',
                                          timeMin=first_day,
                                          timeMax=last_day,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print(get_red("no events found"))
        sys.exit()

    num_hours = 0
    for event in events:
        start_time = parser.parse(event['start'].get('dateTime', event['start'].get('date')))
        end_time = parser.parse(event['end'].get('dateTime', event['start'].get('date')))
        summary = event['summary']

        if any(word.lower() in summary.lower() for word in args.search):
            if args.verbose:
                print(f"{summary} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M %a %d-%m-%Y')}")
                print()

            length = end_time - start_time
            hours = length.total_seconds() / SECONDS_IN_HOUR
            num_hours += hours
    print()
    print(get_green("Summary for {calendar.month_name[3]} {year}"))
    print(get_green("hourly payment: {hourly_payment}"))
    print(get_green(f"total work hours: {round(num_hours, 2)}"))
    print(get_green(f"total revenue: {round(num_hours * args.payment, 2)}"))


if __name__ == '__main__':
    main()
