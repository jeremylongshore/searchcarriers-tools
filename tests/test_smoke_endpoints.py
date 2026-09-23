"""Live smoke tests for raw API endpoints used by skills — hits real SearchCarriers API."""

import httpx
import pytest
from conftest import save_artifact

BASE_URL = "https://searchcarriers.com/api/v1"
SEARCH_V3_URL = "https://searchcarriers.com/api/v3/search"
TEST_DOT = "299569"
TEST_DOCKET = "260340"


@pytest.mark.integration
class TestSmokeEndpoints:
    """Raw httpx smoke tests for API endpoints consumed by skills but not wrapped by MCP handlers."""

    async def test_inspections(self, live_api_key: str, smoke_reports_dir) -> None:
        """GET /company/{dot}/inspections — paginated inspection records."""
        headers = {"Authorization": f"Bearer {live_api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/company/{TEST_DOT}/inspections",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data, "Response JSON must not be empty"
        save_artifact(smoke_reports_dir, "raw_inspections", data)

    async def test_oos_orders(self, live_api_key: str, smoke_reports_dir) -> None:
        """GET /company/{dot}/out-of-service-orders — OOS order history."""
        headers = {"Authorization": f"Bearer {live_api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/company/{TEST_DOT}/out-of-service-orders",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data, "Response JSON must not be empty"
        save_artifact(smoke_reports_dir, "raw_oos_orders", data)

    async def test_authority_history(self, live_api_key: str, smoke_reports_dir) -> None:
        """GET /authority/{docket}/history — authority status change history."""
        headers = {"Authorization": f"Bearer {live_api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/authority/{TEST_DOCKET}/history",
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data, "Response JSON must not be empty"
        save_artifact(smoke_reports_dir, "raw_authority_history", data)

    async def test_export(self, live_api_key: str, smoke_reports_dir) -> None:
        """GET /export — bulk export for a single DOT in JSON format."""
        headers = {"Authorization": f"Bearer {live_api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BASE_URL}/export",
                params={"dot_numbers[]": TEST_DOT, "file_format": "json"},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data, "Response JSON must not be empty"
        save_artifact(smoke_reports_dir, "raw_export", data)

    async def test_mc_search(self, live_api_key: str, smoke_reports_dir) -> None:
        """GET v3 search with docketNumber — lookup carrier by MC docket."""
        headers = {"Authorization": f"Bearer {live_api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                SEARCH_V3_URL,
                params={"docketNumber": TEST_DOCKET},
                headers=headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data, "Response JSON must not be empty"
        save_artifact(smoke_reports_dir, "raw_mc_search", data)
