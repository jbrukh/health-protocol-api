#!/usr/bin/env python3
"""
Withings OAuth 2.0 Token Retrieval Script

This script handles the OAuth 2.0 authentication flow for the Withings API.
It will:
1. Open a browser for user authorization
2. Start a local server to receive the callback
3. Exchange the authorization code for access/refresh tokens
4. Save the tokens to a file

Usage:
    python withings_oauth.py

Environment variables required:
    WITHINGS_CLIENT_ID - Your Withings application client ID
    WITHINGS_CLIENT_SECRET - Your Withings application client secret
    WITHINGS_REDIRECT_URI - Your redirect URI (default: http://localhost:8080/callback)

To get client credentials, create an application at:
https://developer.withings.com/dashboard/
"""

import os
import sys
import json
import webbrowser
import secrets
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from datetime import datetime, timedelta

# Configuration
WITHINGS_AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"
WITHINGS_TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
DEFAULT_REDIRECT_URI = "http://localhost:8080/callback"
TOKEN_FILE = "withings_tokens.json"

# Available scopes
AVAILABLE_SCOPES = [
    "user.info",
    "user.metrics",
    "user.activity",
]


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    def do_GET(self):
        """Handle GET request from OAuth callback."""
        parsed_path = urlparse(self.path)

        if parsed_path.path == "/callback":
            query_params = parse_qs(parsed_path.query)

            if "code" in query_params:
                self.server.auth_code = query_params["code"][0]
                self.server.state = query_params.get("state", [None])[0]
                self._send_success_response()
            elif "error" in query_params:
                self.server.error = query_params.get("error", ["unknown"])[0]
                self.server.error_description = query_params.get(
                    "error_description", ["No description"]
                )[0]
                self._send_error_response()
            else:
                self._send_error_response("Unknown response")
        else:
            self.send_response(404)
            self.end_headers()

    def _send_success_response(self):
        """Send success HTML response."""
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Authorization Successful</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #4CAF50;">Authorization Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def _send_error_response(self, message=None):
        """Send error HTML response."""
        self.send_response(400)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        error_msg = message or getattr(self.server, "error_description", "Unknown error")
        html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Authorization Failed</title></head>
        <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
            <h1 style="color: #f44336;">Authorization Failed</h1>
            <p>{error_msg}</p>
            <p>Please close this window and try again.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def get_config():
    """Get configuration from environment variables."""
    client_id = os.environ.get("WITHINGS_CLIENT_ID")
    client_secret = os.environ.get("WITHINGS_CLIENT_SECRET")
    redirect_uri = os.environ.get("WITHINGS_REDIRECT_URI", DEFAULT_REDIRECT_URI)

    if not client_id:
        print("Error: WITHINGS_CLIENT_ID environment variable is required.")
        print("Get your client ID from: https://developer.withings.com/dashboard/")
        sys.exit(1)

    if not client_secret:
        print("Error: WITHINGS_CLIENT_SECRET environment variable is required.")
        print("Get your client secret from: https://developer.withings.com/dashboard/")
        sys.exit(1)

    return client_id, client_secret, redirect_uri


def generate_state():
    """Generate a random state parameter for CSRF protection."""
    return secrets.token_urlsafe(32)


def build_authorization_url(client_id, redirect_uri, state, scopes=None, demo_mode=False):
    """Build the Withings authorization URL."""
    if scopes is None:
        scopes = AVAILABLE_SCOPES

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": ",".join(scopes),
        "state": state,
    }

    if demo_mode:
        params["mode"] = "demo"

    return f"{WITHINGS_AUTH_URL}?{urlencode(params)}"


def start_callback_server(port=8080):
    """Start local HTTP server to receive OAuth callback."""
    server = HTTPServer(("localhost", port), OAuthCallbackHandler)
    server.auth_code = None
    server.state = None
    server.error = None
    server.error_description = None
    return server


def post_request(url, data):
    """Make a POST request using urllib (no external dependencies)."""
    encoded_data = urlencode(data).encode("utf-8")
    request = Request(url, data=encoded_data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"HTTP {e.code}: {error_body}")
    except URLError as e:
        raise Exception(f"URL Error: {e.reason}")


def exchange_code_for_tokens(client_id, client_secret, code, redirect_uri):
    """Exchange authorization code for access and refresh tokens."""
    data = {
        "action": "requesttoken",
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }

    result = post_request(WITHINGS_TOKEN_URL, data)

    if result.get("status") != 0:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"Token exchange failed: {error_msg} (status: {result.get('status')})")

    return result.get("body", {})


def refresh_tokens(client_id, client_secret, refresh_token):
    """Refresh access token using refresh token."""
    data = {
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }

    result = post_request(WITHINGS_TOKEN_URL, data)

    if result.get("status") != 0:
        error_msg = result.get("error", "Unknown error")
        raise Exception(f"Token refresh failed: {error_msg} (status: {result.get('status')})")

    return result.get("body", {})


def save_tokens(tokens, filename=TOKEN_FILE):
    """Save tokens to a JSON file."""
    token_data = {
        "access_token": tokens.get("access_token"),
        "refresh_token": tokens.get("refresh_token"),
        "expires_in": tokens.get("expires_in"),
        "token_type": tokens.get("token_type"),
        "scope": tokens.get("scope"),
        "userid": tokens.get("userid"),
        "obtained_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(seconds=tokens.get("expires_in", 10800))).isoformat(),
    }

    with open(filename, "w") as f:
        json.dump(token_data, f, indent=2)

    print(f"\nTokens saved to {filename}")
    return token_data


def load_tokens(filename=TOKEN_FILE):
    """Load tokens from a JSON file."""
    if not os.path.exists(filename):
        return None

    with open(filename, "r") as f:
        return json.load(f)


def main():
    """Main function to run the OAuth flow."""
    import argparse

    parser = argparse.ArgumentParser(description="Withings OAuth 2.0 Token Retrieval")
    parser.add_argument("--demo", action="store_true", help="Use demo mode for testing")
    parser.add_argument("--refresh", action="store_true", help="Refresh existing tokens")
    parser.add_argument(
        "--token-file",
        default=TOKEN_FILE,
        help=f"Token file path (default: {TOKEN_FILE})",
    )
    args = parser.parse_args()

    client_id, client_secret, redirect_uri = get_config()

    # Parse port from redirect URI
    parsed_uri = urlparse(redirect_uri)
    port = parsed_uri.port or 8080

    if args.refresh:
        # Refresh existing tokens
        tokens = load_tokens(args.token_file)
        if not tokens:
            print(f"Error: No existing tokens found in {args.token_file}")
            print("Run without --refresh to obtain new tokens.")
            sys.exit(1)

        print("Refreshing tokens...")
        try:
            new_tokens = refresh_tokens(client_id, client_secret, tokens["refresh_token"])
            save_tokens(new_tokens, args.token_file)
            print("\nTokens refreshed successfully!")
            print(f"  Access token expires in: {new_tokens.get('expires_in', 'unknown')} seconds")
        except Exception as e:
            print(f"Error refreshing tokens: {e}")
            sys.exit(1)
        return

    # Generate state for CSRF protection
    state = generate_state()

    # Build authorization URL
    auth_url = build_authorization_url(
        client_id, redirect_uri, state, demo_mode=args.demo
    )

    print("=" * 60)
    print("Withings OAuth 2.0 Authorization")
    print("=" * 60)

    if args.demo:
        print("\n[DEMO MODE] Using Withings demo account for testing.\n")

    print(f"\nStarting local server on port {port}...")

    # Start callback server
    server = start_callback_server(port)

    print(f"Opening browser for authorization...")
    print(f"\nIf the browser doesn't open, visit this URL manually:\n{auth_url}\n")

    # Open browser
    webbrowser.open(auth_url)

    print("Waiting for authorization callback...")

    # Wait for callback
    while server.auth_code is None and server.error is None:
        server.handle_request()

    if server.error:
        print(f"\nAuthorization failed: {server.error}")
        print(f"Description: {server.error_description}")
        sys.exit(1)

    # Verify state
    if server.state != state:
        print("\nError: State mismatch! Possible CSRF attack.")
        sys.exit(1)

    print("\nAuthorization code received. Exchanging for tokens...")

    # Exchange code for tokens
    try:
        tokens = exchange_code_for_tokens(
            client_id, client_secret, server.auth_code, redirect_uri
        )
    except Exception as e:
        print(f"\nError exchanging code for tokens: {e}")
        sys.exit(1)

    # Save tokens
    token_data = save_tokens(tokens, args.token_file)

    print("\n" + "=" * 60)
    print("Authorization Complete!")
    print("=" * 60)
    print(f"\nUser ID: {token_data.get('userid')}")
    print(f"Scope: {token_data.get('scope')}")
    print(f"Access token expires at: {token_data.get('expires_at')}")
    print(f"\nNote: Access tokens expire after 3 hours.")
    print(f"Use --refresh to refresh your tokens before they expire.")
    print(f"\nRefresh tokens expire after 1 year.")


if __name__ == "__main__":
    main()
