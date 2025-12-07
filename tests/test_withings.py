"""Tests for Withings integration."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timedelta
import httpx

from app.services import withings_service


class TestWithingsService:
    """Tests for withings_service functions."""

    @pytest.mark.asyncio
    async def test_get_tokens_empty(self, test_db):
        """Test get_tokens when no tokens exist."""
        tokens = await withings_service.get_tokens()
        assert tokens is None

    @pytest.mark.asyncio
    async def test_save_and_get_tokens(self, test_db):
        """Test saving and retrieving tokens."""
        expires_at = datetime.utcnow() + timedelta(hours=3)

        await withings_service.save_tokens(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
            withings_user_id="12345",
        )

        tokens = await withings_service.get_tokens()
        assert tokens is not None
        assert tokens.access_token == "test_access"
        assert tokens.refresh_token == "test_refresh"
        assert tokens.withings_user_id == "12345"
        assert tokens.status == "active"

    @pytest.mark.asyncio
    async def test_set_status(self, test_db):
        """Test updating token status."""
        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        await withings_service.set_status("needs_reauth")

        tokens = await withings_service.get_tokens()
        assert tokens.status == "needs_reauth"

    @pytest.mark.asyncio
    async def test_is_token_valid_no_tokens(self, test_db):
        """Test is_token_valid when no tokens exist."""
        result = await withings_service.is_token_valid()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_token_valid_expired(self, test_db):
        """Test is_token_valid with expired token."""
        expires_at = datetime.utcnow() - timedelta(hours=1)
        await withings_service.save_tokens(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        result = await withings_service.is_token_valid()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_token_valid_active(self, test_db):
        """Test is_token_valid with valid token."""
        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        result = await withings_service.is_token_valid()
        assert result is True

    def test_verify_signature_valid(self, monkeypatch):
        """Test signature verification with valid signature."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")

        import hmac
        import hashlib
        body = b"test_body"
        signature = hmac.new(b"test_secret", body, hashlib.sha256).hexdigest()

        result = withings_service.verify_signature(body, signature)
        assert result is True

    def test_verify_signature_invalid(self, monkeypatch):
        """Test signature verification with invalid signature."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")

        result = withings_service.verify_signature(b"test_body", "invalid_sig")
        assert result is False

    def test_verify_signature_no_secret(self, monkeypatch):
        """Test signature verification with no client secret configured."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_secret", None)

        result = withings_service.verify_signature(b"test_body", "any_sig")
        assert result is False

    @pytest.mark.asyncio
    async def test_refresh_tokens_success(self, test_db, monkeypatch):
        """Test successful token refresh."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")

        # Save initial tokens
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Expired
        await withings_service.save_tokens(
            access_token="old_access",
            refresh_token="old_refresh",
            expires_at=expires_at,
        )

        # Mock the HTTP response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 0,
            "body": {
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "expires_in": 10800,
                "userid": "12345",
            },
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            tokens = await withings_service.refresh_tokens()

        assert tokens is not None
        assert tokens.access_token == "new_access"
        assert tokens.status == "active"

    @pytest.mark.asyncio
    async def test_refresh_tokens_failure(self, test_db, monkeypatch):
        """Test token refresh failure sets needs_reauth."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")

        expires_at = datetime.utcnow() + timedelta(hours=1)
        await withings_service.save_tokens(
            access_token="old_access",
            refresh_token="old_refresh",
            expires_at=expires_at,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 401}  # Auth error

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            tokens = await withings_service.refresh_tokens()

        assert tokens is None

        # Check status was updated
        stored = await withings_service.get_tokens()
        assert stored.status == "needs_reauth"

    @pytest.mark.asyncio
    async def test_refresh_tokens_no_tokens(self, test_db):
        """Test refresh when no tokens exist."""
        tokens = await withings_service.refresh_tokens()
        assert tokens is None

    @pytest.mark.asyncio
    async def test_get_valid_token_refreshes_if_expired(self, test_db, monkeypatch):
        """Test get_valid_token refreshes expired tokens."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")

        expires_at = datetime.utcnow() - timedelta(hours=1)
        await withings_service.save_tokens(
            access_token="old_access",
            refresh_token="old_refresh",
            expires_at=expires_at,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 0,
            "body": {
                "access_token": "new_access",
                "refresh_token": "new_refresh",
                "expires_in": 10800,
            },
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            token = await withings_service.get_valid_token()

        assert token == "new_access"

    @pytest.mark.asyncio
    async def test_get_valid_token_returns_existing(self, test_db):
        """Test get_valid_token returns existing valid token."""
        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="valid_access",
            refresh_token="refresh",
            expires_at=expires_at,
        )

        token = await withings_service.get_valid_token()
        assert token == "valid_access"

    @pytest.mark.asyncio
    async def test_exchange_code_success(self, test_db, monkeypatch):
        """Test exchanging authorization code for tokens."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 0,
            "body": {
                "access_token": "access123",
                "refresh_token": "refresh123",
                "expires_in": 10800,
                "userid": 12345,
            },
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            tokens = await withings_service.exchange_code("auth_code_123")

        assert tokens is not None
        assert tokens.access_token == "access123"
        assert tokens.withings_user_id == "12345"

    @pytest.mark.asyncio
    async def test_exchange_code_failure(self, test_db, monkeypatch):
        """Test exchange code failure."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 500, "error": "invalid_code"}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            with pytest.raises(withings_service.TokenExchangeError) as exc_info:
                await withings_service.exchange_code("bad_code")

        assert exc_info.value.status == 500
        assert exc_info.value.error == "invalid_code"

    @pytest.mark.asyncio
    async def test_subscribe_webhook_success(self, test_db, monkeypatch):
        """Test subscribing to webhook."""
        from app.config import settings
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="valid_access",
            refresh_token="refresh",
            expires_at=expires_at,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 0}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await withings_service.subscribe_webhook(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_webhook_already_subscribed(self, test_db, monkeypatch):
        """Test subscribing when already subscribed (status 294)."""
        from app.config import settings
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="valid_access",
            refresh_token="refresh",
            expires_at=expires_at,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 294}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await withings_service.subscribe_webhook(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_subscribe_webhook_no_token(self, test_db):
        """Test subscribing without valid token."""
        result = await withings_service.subscribe_webhook(1)
        assert result is False

    @pytest.mark.asyncio
    async def test_unsubscribe_webhook_success(self, test_db, monkeypatch):
        """Test unsubscribing from webhook."""
        from app.config import settings
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="valid_access",
            refresh_token="refresh",
            expires_at=expires_at,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 0}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            result = await withings_service.unsubscribe_webhook(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_subscriptions_success(self, test_db, monkeypatch):
        """Test getting list of subscriptions."""
        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="valid_access",
            refresh_token="refresh",
            expires_at=expires_at,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": 0,
            "body": {
                "profiles": [
                    {"appli": 1},
                    {"appli": 4},
                    {"appli": 16},
                ],
            },
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            subs = await withings_service.get_subscriptions()

        assert subs == [1, 4, 16]

    @pytest.mark.asyncio
    async def test_get_subscriptions_no_token(self, test_db):
        """Test getting subscriptions without token."""
        subs = await withings_service.get_subscriptions()
        assert subs == []

    @pytest.mark.asyncio
    async def test_disconnect(self, test_db, monkeypatch):
        """Test disconnecting Withings integration."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="valid_access",
            refresh_token="refresh",
            expires_at=expires_at,
        )

        mock_response = MagicMock()
        mock_response.json.return_value = {"status": 0}

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            count = await withings_service.disconnect()

        # Should have unsubscribed from 4 webhooks
        assert count == 4

        # Tokens should be deleted
        tokens = await withings_service.get_tokens()
        assert tokens is None


class TestWithingsEndpoints:
    """Tests for Withings API endpoints."""

    @pytest.mark.asyncio
    async def test_get_auth_url(self, client, auth_headers, monkeypatch):
        """Test getting Withings auth URL."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", "test_client_id")
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        response = await client.get("/withings/auth", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert "auth_url" in data
        assert "test_client_id" in data["auth_url"]
        assert "user.metrics" in data["auth_url"]

    @pytest.mark.asyncio
    async def test_get_auth_url_not_configured(self, client, auth_headers, monkeypatch):
        """Test getting auth URL when not configured."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_id", None)

        response = await client.get("/withings/auth", headers=auth_headers)
        assert response.status_code == 500
        assert "not configured" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_status_not_connected(self, client, auth_headers):
        """Test status when not connected."""
        response = await client.get("/withings/status", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["connected"] is False

    @pytest.mark.asyncio
    async def test_get_status_connected(self, client, auth_headers, test_db, monkeypatch):
        """Test status when connected."""
        # Save tokens first
        expires_at = datetime.utcnow() + timedelta(hours=3)
        await withings_service.save_tokens(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
            withings_user_id="12345",
        )

        # Mock get_subscriptions to avoid API call
        with patch.object(withings_service, 'get_subscriptions', new_callable=AsyncMock) as mock_subs:
            mock_subs.return_value = [1, 4, 16, 44]

            response = await client.get("/withings/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is True
        assert data["status"] == "active"
        assert data["withings_user_id"] == "12345"

    @pytest.mark.asyncio
    async def test_disconnect_no_tokens(self, client, auth_headers):
        """Test disconnect when not connected."""
        response = await client.delete("/withings/disconnect", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["message"] == "Withings disconnected"

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature(self, client, monkeypatch):
        """Test webhook with invalid signature."""
        from app.config import settings
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")

        response = await client.post(
            "/withings/webhook",
            data={"appli": "1", "userid": "12345"},
            headers={"X-Withings-Signature": "invalid"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_backfill_requires_auth(self, client):
        """Test backfill endpoint requires authentication."""
        response = await client.post(
            "/withings/backfill",
            json={"start_date": "2024-01-01", "end_date": "2024-01-31"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_callback_success(self, client, test_db, monkeypatch):
        """Test OAuth callback success."""
        from app.config import settings
        from app.services import withings_service

        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        # Mock exchange_code to return tokens
        mock_tokens = MagicMock()
        mock_tokens.withings_user_id = "12345"

        with patch.object(withings_service, 'exchange_code', new_callable=AsyncMock) as mock_exchange:
            mock_exchange.return_value = mock_tokens
            with patch.object(withings_service, 'subscribe_all', new_callable=AsyncMock) as mock_subs:
                mock_subs.return_value = [1, 4, 16, 44]

                response = await client.get("/withings/callback?code=test_code&state=health-tracker")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Withings connected successfully"
        assert data["withings_user_id"] == "12345"

    @pytest.mark.asyncio
    async def test_callback_exchange_failure(self, client, monkeypatch):
        """Test OAuth callback when exchange fails."""
        from app.config import settings
        from app.services import withings_service

        monkeypatch.setattr(settings, "withings_client_id", "test_id")
        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")
        monkeypatch.setattr(settings, "base_url", "https://test.example.com")

        with patch.object(withings_service, 'exchange_code', new_callable=AsyncMock) as mock_exchange:
            mock_exchange.side_effect = withings_service.TokenExchangeError(
                status=503, error="Invalid code", raw={"status": 503}
            )

            response = await client.get("/withings/callback?code=bad_code&state=health-tracker")

        assert response.status_code == 400
        assert "Withings error 503" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_success(self, client, auth_headers, test_db, monkeypatch):
        """Test force token refresh success."""
        from app.services import withings_service

        mock_tokens = MagicMock()
        mock_tokens.expires_at = datetime.utcnow() + timedelta(hours=3)

        with patch.object(withings_service, 'refresh_tokens', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = mock_tokens

            response = await client.post("/withings/refresh", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["message"] == "Token refreshed successfully"

    @pytest.mark.asyncio
    async def test_refresh_failure(self, client, auth_headers, test_db, monkeypatch):
        """Test force token refresh failure."""
        from app.services import withings_service

        with patch.object(withings_service, 'refresh_tokens', new_callable=AsyncMock) as mock_refresh:
            mock_refresh.return_value = None

            response = await client.post("/withings/refresh", headers=auth_headers)

        assert response.status_code == 400
        assert "Failed to refresh" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_webhook_valid_signature(self, client, test_db, monkeypatch):
        """Test webhook with valid signature."""
        from app.config import settings
        from app.services import withings_service
        import hmac
        import hashlib

        monkeypatch.setattr(settings, "withings_client_secret", "test_secret")

        # Create valid signature
        body = b"appli=1&userid=12345"
        signature = hmac.new(b"test_secret", body, hashlib.sha256).hexdigest()

        with patch.object(withings_service, 'verify_signature', return_value=True):
            response = await client.post(
                "/withings/webhook",
                content=body,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-Withings-Signature": signature,
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    @pytest.mark.asyncio
    async def test_backfill_success(self, client, auth_headers, test_db, monkeypatch):
        """Test backfill endpoint success."""
        from app.services import withings_sync

        with patch.object(withings_sync, 'backfill_all', new_callable=AsyncMock) as mock_backfill:
            mock_backfill.return_value = {
                "body_measurements": 10,
                "blood_pressure": 5,
                "daily_activity": 30,
                "sleep": 25,
            }

            response = await client.post(
                "/withings/backfill",
                json={"start_date": "2024-01-01", "end_date": "2024-01-31"},
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Backfill completed"
        assert data["counts"]["body_measurements"] == 10
