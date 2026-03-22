import httpx

from polymarket.config import settings


class PolymarketClient:
    def __init__(self, base_url: str, timeout: int | None = None):
        self._base_url = base_url
        self._timeout = timeout or settings.request_timeout
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=self._timeout,
            headers={"Accept": "application/json"},
        )

    def get(self, path: str, params: dict | None = None) -> dict | list:
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "PolymarketClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()


def gamma_client() -> PolymarketClient:
    return PolymarketClient(base_url=settings.gamma_api_base_url)


def clob_client() -> PolymarketClient:
    return PolymarketClient(base_url=settings.clob_api_base_url)
