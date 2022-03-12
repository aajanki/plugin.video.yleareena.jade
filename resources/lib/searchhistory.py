import hashlib
import os.path
import xbmcvfs
from .storage import Storage
from typing import List

_search_history = None


class SearchHistory():
    def __init__(self, storage_filename: str, max_item_count: int = 10):
        self.storage = Storage(storage_filename)
        self.max_item_count = max_item_count

    def update(self, search_text: str) -> None:
        self.storage.set(self._make_key(search_text), search_text)

        items = self.storage.get_all(reverse=True)
        for del_item in items[self.max_item_count:]:
            self.storage.delete(del_item[0])

    def remove(self, search_text: str) -> None:
        self.storage.delete(self._make_key(search_text))

    def list(self) -> List[str]:
        items = self.storage.get_all(reverse=True)
        items = items[:self.max_item_count]
        return [x[1] for x in items]

    def _make_key(self, text: str) -> int:
        # Use only the upper 64 bits of the MD5 hash, because the Storage class
        # (SQLite) supports at most 64 bit integers.
        m = hashlib.md5(text.lower().encode('utf-8'))
        i = int(m.hexdigest()[:16], base=16)

        # translate to signed 64 bit int range
        if i > 0x8000000000000000:
            i -= 0x10000000000000000

        return i


def get_search_history(addon):
    global _search_history

    if _search_history is None:
        data_path = xbmcvfs.translatePath(addon.getAddonInfo('profile'))
        if not xbmcvfs.exists(data_path):
            xbmcvfs.mkdir(data_path)

        _search_history = SearchHistory(os.path.join(data_path, 'search.sqlite'))

    return _search_history
