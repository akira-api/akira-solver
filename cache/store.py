from dataclasses import dataclass


@dataclass
class CacheEntry:
    cookie_string: str
    domain: str


class CookieStore:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def get(self, domain: str) -> CacheEntry | None:
        return self._store.get(domain)

    def set(self, domain: str, entry: CacheEntry) -> None:
        self._store[domain] = entry

    def invalidate(self, domain: str) -> None:
        self._store.pop(domain, None)

    def clear(self) -> None:
        self._store.clear()


cookie_store = CookieStore()