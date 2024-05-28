from typing import IO

class AtomicValue:
    def __init__(self, file: IO[bytes], offset: int, size: int) -> None: ...
    def _read_selector(self) -> int: ...
    def _seek_to_second(self) -> None: ...
    def _seek_to_first(self) -> None: ...
    def _raw_read(self) -> int: ...
    def read(self) -> int: ...
    def write(self, value: int) -> None: ...
    @property
    def size(self) -> int: ...

class PersistentQueueMetadataRegion:
    def __init__(self, file: IO[bytes], address_size: int) -> None: ...
    @property
    def head(self) -> int: ...
    @property
    def tail(self) -> int: ...
    @property
    def size(self) -> int: ...
    def write_head(self, value: int) -> None: ...
    def write_tail(self, value: int) -> None: ...

class PersistentQueue:
    def __init__(self, filename: str, max_file_size: int, elem_size: int) -> None: ...
    @property
    def capacity(self) -> int: ...
    def __del__(self) -> None: ...
    @property
    def _head(self) -> int: ...
    @property
    def _tail(self) -> int: ...
    def _write_head(self, v: int) -> None: ...
    def _write_tail(self, v: int) -> None: ...
    @property
    def length(self) -> int: ...
    @property
    def is_empty(self) -> bool: ...
    def put(self, value: bytes) -> None: ...
    @property
    def head(self) -> bytes: ...
    def pop(self) -> None: ...