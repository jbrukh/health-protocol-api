from datetime import datetime, timedelta, timezone
import httpx

from app.database import get_db
from app.config import settings
from app.models.withings import WithingsTokens

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


async def exchange_code(code: str) -> WithingsTokens | None:
    """Exchange authorization code for tokens."""
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
        return None

    body = data["body"]
    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=body["expires_in"])

    await save_tokens(
        access_token=body["access_token"],
        refresh_token=body["refresh_token"],
        expires_at=expires_at,
        withings_user_id=str(body.get("userid")),
    )

    return await get_tokens()


async def subscribe_webhook(appli: int) -> bool:
    """Subscribe to webhook notifications for a data type."""
    token = await get_valid_token()
    if not token:
        return False

    callback_url = f"{settings.base_url}/withings/webhook"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_NOTIFY_URL,
            data={
                "action": "subscribe",
                "callbackurl": callback_url,
                "appli": appli,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    data = response.json()
    # Status 0 = success, 294 = already subscribed (both ok)
    return data.get("status") in (0, 294)


async def unsubscribe_webhook(appli: int) -> bool:
    """Unsubscribe from webhook notifications for a data type."""
    token = await get_valid_token()
    if not token:
        return False

    callback_url = f"{settings.base_url}/withings/webhook"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_NOTIFY_URL,
            data={
                "action": "revoke",
                "callbackurl": callback_url,
                "appli": appli,
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    data = response.json()
    return data.get("status") == 0


async def subscribe_all() -> list[int]:
    """Subscribe to all supported data types. Returns list of successfully subscribed appli codes."""
    applis = [1, 4, 16, 44]  # Weight, BP, Activity, Sleep
    subscribed = []
    for appli in applis:
        if await subscribe_webhook(appli):
            subscribed.append(appli)
    return subscribed


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
    token = await get_valid_token()
    if not token:
        return []

    async with httpx.AsyncClient() as client:
        response = await client.post(
            WITHINGS_NOTIFY_URL,
            data={"action": "list"},
            headers={"Authorization": f"Bearer {token}"},
        )

    data = response.json()
    if data.get("status") != 0:
        return []

    profiles = data.get("body", {}).get("profiles", [])
    return [p["appli"] for p in profiles]


async def revoke_token() -> bool:
    """Revoke the current access token with Withings."""
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

    if not settings.withings_client_secret:
        return False

    expected = hmac.new(
        settings.withings_client_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)
