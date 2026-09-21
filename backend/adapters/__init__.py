from typing import Dict, Type, Optional
from backend.adapters.base import SourceAdapter, RawRecord
from backend.adapters.manual_import import ManualImportAdapter, ManualImportError
from backend.adapters.play_store import GooglePlayStoreAdapter
from backend.adapters.app_store import AppStoreAdapter
from backend.adapters.reddit import RedditAdapter
from backend.adapters.youtube import YouTubeAdapter
from backend.adapters.forum import ForumAdapter

ADAPTER_REGISTRY: Dict[str, Type[SourceAdapter]] = {
    "manual_import": ManualImportAdapter,
    "manual_csv": ManualImportAdapter,
    "manual_json": ManualImportAdapter,
    "play_store": GooglePlayStoreAdapter,
    "google_play": GooglePlayStoreAdapter,
    "app_store": AppStoreAdapter,
    "apple_app_store": AppStoreAdapter,
    "reddit": RedditAdapter,
    "youtube": YouTubeAdapter,
    "forum": ForumAdapter,
}


def get_adapter(platform: str) -> Optional[SourceAdapter]:
    """
    Factory function to retrieve an initialized adapter instance for a given platform name.
    """
    adapter_cls = ADAPTER_REGISTRY.get(platform.lower().strip())
    if adapter_cls:
        return adapter_cls()
    return None


def list_supported_adapters() -> list[str]:
    """
    Returns list of supported platform adapter keys.
    """
    return sorted(list(ADAPTER_REGISTRY.keys()))


__all__ = [
    "SourceAdapter",
    "RawRecord",
    "ManualImportAdapter",
    "ManualImportError",
    "GooglePlayStoreAdapter",
    "AppStoreAdapter",
    "RedditAdapter",
    "YouTubeAdapter",
    "ForumAdapter",
    "ADAPTER_REGISTRY",
    "get_adapter",
    "list_supported_adapters",
]
