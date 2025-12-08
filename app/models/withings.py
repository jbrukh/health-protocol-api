from datetime import datetime
from pydantic import BaseModel


class WithingsTokens(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime
    withings_user_id: str | None = None
    status: str = "active"  # "active" or "needs_reauth"
    updated_at: datetime | None = None


class WithingsAuthResponse(BaseModel):
    auth_url: str


class WithingsCallbackResponse(BaseModel):
    message: str
    withings_user_id: str
    subscriptions: list[int]
    backfill_started: bool


class WithingsStatusResponse(BaseModel):
    connected: bool
    status: str | None = None
    withings_user_id: str | None = None
    expires_at: datetime | None = None
    expires_in_seconds: int | None = None
    subscriptions: list[int] | None = None


class WithingsRefreshResponse(BaseModel):
    message: str
    expires_at: datetime


class WithingsDisconnectResponse(BaseModel):
    message: str
    webhooks_unsubscribed: int


class WithingsSubscribeResponse(BaseModel):
    message: str
    subscriptions: list[int]
    debug: list[dict] | None = None


class WithingsBackfillRequest(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD


class WithingsBackfillResponse(BaseModel):
    message: str
    counts: dict[str, int]
