from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProfilingPreferences:
    relative_urls: list[str]
    repetitions: int
    tracemalloc_enabled: bool
    cprofile_enabled: bool
    ram_limit: int | None
    request_headers: dict[str, str]
