import os
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

load_dotenv()

# Prevent error if user doesn't select all requested scopes
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# Simplified scopes to only what is needed for the current tools
SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly"
]

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    print("Error: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not found in .env file.")
    exit(1)

# Create flow instance
flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    },
    SCOPES
)

# Using a fixed port 8080 to make it easier to register in Google Cloud Console
# IMPORTANT: Add http://localhost:8080/ to "Authorized redirect URIs" in GCP Console
print("\n--- ACTION REQUIRED ---")
print("Make sure 'http://localhost:8080/' is added to 'Authorized redirect URIs' in your Google Cloud Console.")
print("Starting local server on port 8080...\n")

try:
    # prompt='consent' forces Google to provide a refresh token even if previously authorized
    creds = flow.run_local_server(
        port=8080, 
        authorization_prompt_params={'prompt': 'consent'}
    )
    
    # Print refresh token
    if creds.refresh_token:
        print("\nSuccess! Copy this Refresh Token to your .env file:")
        print(f"GOOGLE_REFRESH_TOKEN={creds.refresh_token}")
    else:
        print("\nWarning: No refresh token returned. Try revoking access at https://myaccount.google.com/permissions and try again.")
except Exception as e:
    print(f"\nError starting local server: {e}")
    print("If you get a 'redirect_uri_mismatch' error, ensure 'http://localhost:8080/' is added to your GCP Credentials.")