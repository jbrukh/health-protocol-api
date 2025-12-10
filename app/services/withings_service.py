from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
import httpx

from app.database import get_db
from app.config import settings
from app.models.withings import WithingsTokens


def generate_nonce() -> str:
    """Generate a random nonce for Withings API calls."""
    return secrets.token_hex(16)


def generate_signature(action: str, nonce: str) -> str:
    """Generate HMAC-SHA256 signature for Withings API calls."""
    if not settings.withings_client_secret:
        return ""
    data = f"{action},{settings.withings_client_id},{nonce}"
    return hmac.new(
        settings.withings_client_secret.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()

WITHINGS_TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
WITHINGS_NOTIFY_URL = "https://wbsapi.withings.net/notify"


async def get_tokens() -> WithingsTokens | None:
    """Fetch current tokens from database."""
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT access_token, refresh_token, expires_at, withings_user_id, status, updated_at "
            "FROM withings_tokens WHERE id = 1"
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return WithingsTokens(
            access_token=row["access_token"],
            refresh_token=row["refresh_token"],
            expires_at=datetime.fromisoformat(row["expires_at"]),
            withings_user_id=row["withings_user_id"],
            status=row["status"],
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )


async def save_tokens(
    access_token: str,
    refresh_token: str,
    expires_at: datetime,
    withings_user_id: str | None = None,
) -> None:
    """Store tokens in database (upsert)."""
    async with get_db() as db:
        await db.execute(
            """
            INSERT INTO withings_tokens (id, access_token, refresh_token, expires_at, withings_user_id, status, updated_at)
            VALUES (1, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                access_token = excluded.access_token,
                refresh_token = excluded.refresh_token,
                expires_at = excluded.expires_at,
                withings_user_id = COALESCE(excluded.withings_user_id, withings_tokens.withings_user_id),
                status = 'active',
                updated_at = CURRENT_TIMESTAMP
            """,
            (access_token, refresh_token, expires_at.isoformat(), withings_user_id),
        )
        await db.commit()


async def set_status(status: str) -> None:
    """Update token status to 'active' or 'needs_reauth'."""
    async with get_db() as db:
        await db.execute(
            "UPDATE withings_tokens SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1",
            (status,),
        )
        await db.commit()


async def is_token_valid() -> bool:
    """Check if access token is still valid (not expired)."""
    tokens = await get_tokens()
    if not tokens:
        return False
    # Add 60 second buffer
    return datetime.now(timezone.utc).replace(tzinfo=None) < tokens.expires_at - timedelta(seconds=60)


async def refresh_tokens() -> WithingsTokens | None:
    """Refresh the access token using the refresh token."""
    if not settings.withings_client_id or not settings.withings_client_secret:
        return None

    tokens = await get_tokens()
    if not tokens:
        return None

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_TOKEN_URL,
            data={
                "action": "requesttoken",
                "grant_type": "refresh_token",
                "client_id": settings.withings_client_id,
                "client_secret": settings.withings_client_secret,
                "refresh_token": tokens.refresh_token,
            },
        )

    data = response.json()
    if data.get("status") != 0:
        # Refresh failed - mark as needing reauth
        await set_status("needs_reauth")
        return None

    body = data["body"]
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=body["expires_in"])

    await save_tokens(
        access_token=body["access_token"],
        refresh_token=body["refresh_token"],
        expires_at=expires_at,
        withings_user_id=body.get("userid"),
    )

    return await get_tokens()


async def get_valid_token() -> str | None:
    """Return a valid access token, refreshing if needed."""
    if not await is_token_valid():
        tokens = await refresh_tokens()
        if not tokens:
            return None
        return tokens.access_token

    tokens = await get_tokens()
    return tokens.access_token if tokens else None


class TokenExchangeError(Exception):
    """Error during token exchange with details."""
    def __init__(self, status: int, error: str, raw: dict):
        self.status = status
        self.error = error
        self.raw = raw
        super().__init__(f"Withings error {status}: {error}")


async def exchange_code(code: str) -> WithingsTokens:
    """Exchange authorization code for tokens. Raises TokenExchangeError on failure."""
    redirect_uri = f"{settings.base_url}/withings/callback"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_TOKEN_URL,
            data={
                "action": "requesttoken",
                "grant_type": "authorization_code",
                "client_id": settings.withings_client_id,
                "client_secret": settings.withings_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )

    data = response.json()
    if data.get("status") != 0:
        raise TokenExchangeError(
            status=data.get("status"),
            error=data.get("error", "Unknown error"),
            raw=data,
        )

    body = data["body"]
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=body["expires_in"])

    await save_tokens(
        access_token=body["access_token"],
        refresh_token=body["refresh_token"],
        expires_at=expires_at,
        withings_user_id=str(body.get("userid")),
    )

    return await get_tokens()


async def subscribe_webhook(appli: int) -> tuple[bool, dict]:
    """Subscribe to webhook notifications for a data type. Returns (success, response)."""
    if not settings.withings_client_id or not settings.withings_client_secret:
        return False, {"error": "not_configured"}

    token = await get_valid_token()
    if not token:
        return False, {"error": "no_token"}

    callback_url = f"{settings.base_url}/withings/webhook"
    nonce = generate_nonce()
    signature = generate_signature("subscribe", nonce)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_NOTIFY_URL,
            data={
                "action": "subscribe",
                "callbackurl": callback_url,
                "appli": appli,
                "client_id": settings.withings_client_id,
                "nonce": nonce,
                "signature": signature,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    data = response.json()
    # Status 0 = success, 294 = already subscribed (both ok)
    success = data.get("status") in (0, 294)
    return success, data


async def unsubscribe_webhook(appli: int) -> bool:
    """Unsubscribe from webhook notifications for a data type."""
    if not settings.withings_client_id or not settings.withings_client_secret:
        return False

    token = await get_valid_token()
    if not token:
        return False

    callback_url = f"{settings.base_url}/withings/webhook"
    nonce = generate_nonce()
    signature = generate_signature("revoke", nonce)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_NOTIFY_URL,
            data={
                "action": "revoke",
                "callbackurl": callback_url,
                "appli": appli,
                "client_id": settings.withings_client_id,
                "nonce": nonce,
                "signature": signature,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    data = response.json()
    return data.get("status") == 0


async def subscribe_all() -> tuple[list[int], list[dict]]:
    """Subscribe to all supported data types. Returns (subscribed appli codes, all responses)."""
    applis = [1, 4, 16, 44]  # Weight, BP, Activity, Sleep
    subscribed = []
    responses = []
    for appli in applis:
        success, data = await subscribe_webhook(appli)
        responses.append({"appli": appli, "success": success, "response": data})
        if success:
            subscribed.append(appli)
    return subscribed, responses


async def unsubscribe_all() -> int:
    """Unsubscribe from all webhooks. Returns count of unsubscribed."""
    applis = [1, 4, 16, 44]
    count = 0
    for appli in applis:
        if await unsubscribe_webhook(appli):
            count += 1
    return count


async def get_subscriptions() -> list[int]:
    """List current webhook subscriptions."""
    if not settings.withings_client_id or not settings.withings_client_secret:
        return []

    token = await get_valid_token()
    if not token:
        return []

    nonce = generate_nonce()
    signature = generate_signature("list", nonce)

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_NOTIFY_URL,
            data={
                "action": "list",
                "client_id": settings.withings_client_id,
                "nonce": nonce,
                "signature": signature,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    data = response.json()
    if data.get("status") != 0:
        return []

    profiles = data.get("body", {}).get("profiles", [])
    return [p["appli"] for p in profiles]


async def revoke_token() -> bool:
    """Revoke the current access token with Withings."""
    if not settings.withings_client_id or not settings.withings_client_secret:
        return True

    tokens = await get_tokens()
    if not tokens:
        return True

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_TOKEN_URL,
            data={
                "action": "revoke",
                "client_id": settings.withings_client_id,
                "client_secret": settings.withings_client_secret,
                "token": tokens.access_token,
            },
        )

    return response.json().get("status") == 0


async def disconnect() -> int:
    """Disconnect Withings integration. Returns count of unsubscribed webhooks."""
    # Unsubscribe from webhooks
    count = await unsubscribe_all()

    # Revoke token
    await revoke_token()

    # Clear tokens from database
    async with get_db() as db:
        await db.execute("DELETE FROM withings_tokens WHERE id = 1")
        await db.commit()

    return count


def verify_signature(body: bytes, signature: str) -> bool:
    """Verify webhook signature using HMAC-SHA256."""
    import hmac
    import hashlib
    import base64

    if not settings.withings_client_secret:
        return False

    mac = hmac.new(
        settings.withings_client_secret.encode(),
        body,
        hashlib.sha256,
    ).digest()

    # Accept both hex and base64 encodings (Withings docs use base64)
    expected_hex = mac.hex()
    expected_b64 = base64.b64encode(mac).decode()

    return hmac.compare_digest(expected_hex, signature) or hmac.compare_digest(expected_b64, signature)
