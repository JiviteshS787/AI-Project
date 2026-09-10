from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly"
]

creds = Credentials.from_authorized_user_file("data/google_token.json", SCOPES)

try:
    creds.refresh(Request())
    print("Valid — refreshed OK, new access token expires:", creds.expiry)
except Exception as e:
    print("Dead:", e)