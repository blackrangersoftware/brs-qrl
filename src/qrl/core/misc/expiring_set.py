# coding=utf-8
# Distributed under the MIT software license, see the accompanying
# file LICENSE or http://www.opensource.org/licenses/mit-license.php.
from collections import Set
import simplejson as json

from qrl.core.misc import ntp


class ExpiringSet(Set):
    def __init__(self, expiration_time, filename=None):
        super().__init__()
        self.expiration_time = expiration_time
        self._data = dict()
        self._filename = filename
        self._load()

    def __contains__(self, x: object) -> bool:
        self._refresh()
        return x in self._data

    def __len__(self) -> int:
        self._refresh()
        return len(self._data)

    def __iter__(self):
        self._refresh()
        return self._data.keys().__iter__()

    def add(self, x):
        current_time = ntp.getTime()
        self._data[x] = current_time + self.expiration_time

    def _refresh(self):
        # FIXME: refactored from banned peers. Rework to use a priority queue instead

        current_time = ntp.getTime()
        self._data = {k: v for k, v in self._data.items() if v < current_time}
        self._store()

    def _store(self):
        if self._filename is not None:
            with open(self._filename, 'w') as f:
                json.dump(self._data, f)

    def _load(self):
        if self._filename is not None:
            try:
                with open(self._filename, 'r') as f:
                    self._data = json.load(f)
                self._refresh()
            except FileNotFoundError:
                self._data = dict()