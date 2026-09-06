import aiohttp
import logging
from typing import Any
from config.settings import settings

logger = logging.getLogger(__name__)


class PotokAPIError(Exception):
    pass


class PotokClient:
    def __init__(self, base_url: str = None, token: str = None):
        self.base_url = base_url or settings.POTOK_API_BASE_URL
        self.token = token or settings.POTOK_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=self.headers, **kwargs) as response:
                if response.status in (200, 201):
                    return await response.json()
                text = await response.text()
                logger.error(f"Potok API error {response.status}: {text}")
                raise PotokAPIError(f"HTTP {response.status}: {text}")

    async def get_applicants(self, page: int = 1, per_page: int = 100) -> dict:
        return await self._request("GET", "/applicants.json", params={"page": page, "per_page": per_page})

    async def get_applicant(self, applicant_id: int) -> dict:
        return await self._request("GET", f"/applicants/{applicant_id}.json")

    async def get_jobs(self, page: int = 1, per_page: int = 100) -> dict:
        return await self._request("GET", "/jobs.json", params={"page": page, "per_page": per_page})

    async def update_applicant(self, applicant_id: int, data: dict) -> dict:
        return await self._request("PUT", f"/applicants/{applicant_id}.json", json=data)

    async def add_applicant_note(self, applicant_id: int, note: str) -> dict:
        return await self._request("POST", f"/applicants/{applicant_id}/notes.json", json={"text": note})

    async def get_employees(self) -> list[dict]:
        return await self._request("GET", "/employees.json")

    async def get_employee(self, employee_id: int) -> dict:
        return await self._request("GET", f"/employees/{employee_id}.json")

    async def create_notification(self, entity_type: str, entity_id: int, message: str) -> dict:
        return await self._request("POST", "/notifications.json", json={
            "entity_type": entity_type,
            "entity_id": entity_id,
            "message": message,
        })
