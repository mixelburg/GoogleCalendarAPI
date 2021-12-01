from __future__ import print_function

from termcolor import colored
import calendar
import datetime
import getopt
import os.path
import sys

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
YEAR_BOUNDS = (2000, datetime.datetime.now().year)
MONTH_BOUNDS = (1, 12)
DIGIT_BOUNDS = (0, 14)

HELP_TEXT = """
Usage:
    salary_calculator.py -p <hourly_payment> 
optional:
    --help
    -v --verbose display more stuff
    --payment <hourly_payment>
    -y --year <year> # year to count hours in, this year if not specified
    -m --month <month> # month to count hours in, this year if not specified 
    -d --digits <digits> # number of round digits, default = 2, 0 = display max
    -s --search "<words>" # words in event summary to search for, default = "work"
"""

REQUIRED_ARGS: list[tuple[str, str]] = [
    ('-p', '--payment')
]


def print_red(text):
    print(colored(text, "red"))


def print_green(text):
    print(colored(text, "green"))


def str_arg_to_num(arg: str, opt: str, bounds: tuple[int, int] = (-sys.maxsize, sys.maxsize)):
    try:
        val = float(arg)
        if val < bounds[0] or val > bounds[1]:
            print_red(f"invalid value for parameter {opt} : {arg}")
            print_red(f"value has to be between {bounds[0]} and {bounds[1]}")
            print(HELP_TEXT)
            sys.exit()

        return val
    except ValueError:
        print_red(f"invalid value for parameter {opt} : {arg}")
        print(HELP_TEXT)
        sys.exit()


def check_required(opts: list[tuple[str, str]]):
    for required_arg in REQUIRED_ARGS:
        if not any(arg_option in [val[0] for val in opts] for arg_option in required_arg):
            print_red(f"one of the required params {required_arg} has to be specified")
            print(HELP_TEXT)
            sys.exit()


def main():
    search_words = ["work"]
    current_date = datetime.datetime.now()
    digits = 2
    year = current_date.year
    month = current_date.month
    hourly_payment = 45
    verbose = False

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            "hvp:y:m:d:s:", ["verbose", "clear", "payment=", "year=", "month=", "digits=", "search="]
        )
    except getopt.GetoptError:
        sys.exit(2)

    check_required(opts)

    for opt, arg in opts:
        if opt == '-h':
            print(HELP_TEXT)
            sys.exit()
        elif opt in ("-p", "--payment"):
            hourly_payment = str_arg_to_num(arg, opt)
        elif opt in ("-y", "--year"):
            year = int(str_arg_to_num(arg, opt, YEAR_BOUNDS))
        elif opt in ("-m", "--month"):
            month = int(str_arg_to_num(arg, opt, MONTH_BOUNDS))
        elif opt in ("-d", "--digits"):
            digits = int(str_arg_to_num(arg, opt, DIGIT_BOUNDS))
        elif opt in ("-v", "--verbose"):
            verbose = True
        elif opt in ("-s", "--search"):
            search_words = arg.split(' ')
        elif opt == "--clear":
            if os.path.exists(TOKEN_FILE_NAME):
                os.remove(TOKEN_FILE_NAME)

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

    service = build('calendar', 'v3', credentials=creds)

    first_day = datetime.datetime(year=year, month=month, day=1)
    last_day = datetime.datetime(year=year, month=month, day=calendar.monthrange(year, month)[1])

    first_day_formatted = first_day.isoformat() + 'Z'
    last_day_formatted = last_day.isoformat() + 'Z'

    events_result = service.events().list(calendarId='primary',
                                          timeMin=first_day_formatted,
                                          timeMax=last_day_formatted,
                                          singleEvents=True,
                                          orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print_red("no events found")
        sys.exit()

    num_hours = 0
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['start'].get('date'))
        summary = event['summary']

        if any(word.lower() in summary.lower() for word in search_words):
            start_time = parser.parse(start)
            end_time = parser.parse(end)

            if verbose:
                print(f"{summary} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M %a %d-%m-%Y')}")
                print()

            length = end_time - start_time
            hours = length.total_seconds() / SECONDS_IN_HOUR
            num_hours += hours
    print()
    print_green(f"Summary for {calendar.month_name[3]} {year}")
    print_green(f"hourly payment: {hourly_payment}")
    print_green(f"total work hours: {round(num_hours, digits)}")
    print_green(f"total revenue: {round(num_hours * hourly_payment, digits)}")


if __name__ == '__main__':
    main()
