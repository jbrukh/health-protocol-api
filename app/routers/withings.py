from datetime import datetime, date, timezone
from urllib.parse import urlencode
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks

from app.auth import verify_token
from app.config import settings
from app.models.withings import (
    WithingsAuthResponse,
    WithingsCallbackResponse,
    WithingsStatusResponse,
    WithingsRefreshResponse,
    WithingsDisconnectResponse,
    WithingsBackfillRequest,
    WithingsBackfillResponse,
)
from app.services import withings_service, withings_sync

router = APIRouter()

WITHINGS_AUTH_URL = "https://account.withings.com/oauth2_user/authorize2"


@router.get("/auth", response_model=WithingsAuthResponse)
async def get_auth_url(_: str = Depends(verify_token)):
    """Get Withings authorization URL."""
    if not settings.withings_client_id or not settings.base_url:
        raise HTTPException(status_code=500, detail="Withings integration not configured")

    params = {
        "response_type": "code",
        "client_id": settings.withings_client_id,
        "redirect_uri": f"{settings.base_url}/withings/callback",
        "scope": "user.metrics,user.activity",
        "state": "health-tracker",
    }
    auth_url = f"{WITHINGS_AUTH_URL}?{urlencode(params)}"
    return WithingsAuthResponse(auth_url=auth_url)


@router.get("/callback", response_model=WithingsCallbackResponse)
async def oauth_callback(code: str, state: str | None = None, background_tasks: BackgroundTasks = None):
    """OAuth callback - exchanges code for tokens, subscribes to webhooks, triggers backfill."""
    if not settings.withings_client_id or not settings.withings_client_secret:
        raise HTTPException(status_code=500, detail="Withings integration not configured")

    # Validate state parameter to prevent CSRF attacks
    if state != "health-tracker":
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Exchange code for tokens
    tokens = await withings_service.exchange_code(code)
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to exchange authorization code")

    # Subscribe to webhooks
    subscriptions = await withings_service.subscribe_all()

    # Trigger backfill in background
    backfill_started = False
    if background_tasks:
        background_tasks.add_task(withings_sync.backfill_full_history)
        backfill_started = True

    return WithingsCallbackResponse(
        message="Withings connected successfully",
        withings_user_id=tokens.withings_user_id or "",
        subscriptions=subscriptions,
        backfill_started=backfill_started,
    )


@router.get("/status", response_model=WithingsStatusResponse)
async def get_status(_: str = Depends(verify_token)):
    """Check Withings connection status."""
    tokens = await withings_service.get_tokens()
    if not tokens:
        return WithingsStatusResponse(connected=False)

    subscriptions = await withings_service.get_subscriptions()

    expires_in = int((tokens.expires_at - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds())

    return WithingsStatusResponse(
        connected=True,
        status=tokens.status,
        withings_user_id=tokens.withings_user_id,
        expires_at=tokens.expires_at,
        expires_in_seconds=max(0, expires_in),
        subscriptions=subscriptions,
    )


@router.post("/refresh", response_model=WithingsRefreshResponse)
async def refresh_token(_: str = Depends(verify_token)):
    """Force token refresh."""
    tokens = await withings_service.refresh_tokens()
    if not tokens:
        raise HTTPException(status_code=400, detail="Failed to refresh token")

    return WithingsRefreshResponse(
        message="Token refreshed successfully",
        expires_at=tokens.expires_at,
    )


@router.delete("/disconnect", response_model=WithingsDisconnectResponse)
async def disconnect(_: str = Depends(verify_token)):
    """Disconnect Withings integration."""
    count = await withings_service.disconnect()
    return WithingsDisconnectResponse(
        message="Withings disconnected",
        webhooks_unsubscribed=count,
    )


@router.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    """Receive Withings webhook notifications."""
    body = await request.body()
    signature = request.headers.get("X-Withings-Signature", "")

    # Verify signature
    if not withings_service.verify_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse form data
    form = await request.form()
    appli = int(form.get("appli", 0))
    startdate = form.get("startdate")
    enddate = form.get("enddate")

    # Dispatch sync in background
    start_ts = int(startdate) if startdate else None
    end_ts = int(enddate) if enddate else None
    background_tasks.add_task(withings_sync.sync_by_appli, appli, start_ts, end_ts)

    return {"status": "ok"}


@router.post("/backfill", response_model=WithingsBackfillResponse)
async def backfill(request: WithingsBackfillRequest, _: str = Depends(verify_token)):
    """Manual historical data backfill."""
    try:
        start = date.fromisoformat(request.start_date)
        end = date.fromisoformat(request.end_date)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {e}")

    counts = await withings_sync.backfill_all(start, end)

    return WithingsBackfillResponse(
        message="Backfill completed",
        counts=counts,
    )
