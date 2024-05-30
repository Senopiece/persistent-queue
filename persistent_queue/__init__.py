import os
from typing import IO

from persistent_queue.exceptions import (
    IncorrectValueLength,
    QueueIsEmpty,
    TooBigBounds,
    TooSmallBounds,
)


class AtomicValue:
    def __init__(self, file: IO[bytes], offset: int, size: int) -> None:
        self._file = file
        self._offset = offset
        self._size = size
        self._raw_read()
        self._E = (0).to_bytes(self._size)

    def _read_selector(self) -> int:
        self._file.seek(self._offset)
        return int.from_bytes(self._file.read(1))

    def _seek_to_second(self) -> None:
        self._file.seek(self._offset + 1 + self._size)

    def _seek_to_first(self) -> None:
        self._file.seek(self._offset + 1)

    def _raw_read(self) -> int | None:
        selector = self._read_selector()

        if selector not in (1, 2):
            value = None
        else:
            if selector == 2:
                self._seek_to_second()
            else:
                pass  # already at the first

            value = int.from_bytes(self._file.read(self._size))

        self._cached_selector = selector
        self._cached_value = value

        return value

    def read(self) -> int | None:
        return self._cached_value

    def write(self, value: int | None) -> None:
        """Atomic operation"""

        if value is None:
            # write invalid selector
            self._file.seek(self._offset)
            self._file.write(self._E)

            self._cached_selector = 0
            self._cached_value = None

            return

        if self._cached_selector == 1:
            new_selector = 2
            self._seek_to_second()
        else:
            new_selector = 1
            self._seek_to_first()

        self._file.write(value.to_bytes(self._size))

        self._file.seek(self._offset)
        self._file.write(new_selector.to_bytes())

        self._cached_selector = new_selector
        self._cached_value = value

    @property
    def size(self) -> int:
        """In bytes"""
        return 1 + 2 * self._size


# TODO: can be rewritten to use 3*(n + 1) instead of 1 + 4*8*n bits
class PersistentQueueMetadataRegion:
    def __init__(self, file: IO[bytes], address_size: int) -> None:
        self._file = file
        self._address_size = address_size
        self._head_section = AtomicValue(file, 0, address_size)
        self._tail_section = AtomicValue(file, self._head_section.size, address_size)

    @property
    def head(self) -> int | None:
        return self._head_section.read()

    @property
    def tail(self) -> int | None:
        return self._tail_section.read()

    @property
    def size(self) -> int:
        """In bytes"""
        return self._head_section.size + self._tail_section.size

    def write_head(self, value: int | None) -> None:
        """Atomic operation"""
        self._head_section.write(value)

    def write_tail(self, value: int) -> None:
        """Atomic operation"""
        self._tail_section.write(value)


class PersistentQueue:
    def __init__(
        self,
        filename: str,
        max_file_size: int,  # in bytes
        elem_size: int,  # in bytes
    ) -> None:
        # TODO: dynamic address_size depending on elem_size and max_file_size
        self._file = open(filename, "r+b" if os.path.isfile(filename) else "w+b")
        self._address_size = 4  # supports up to ~100 GB max file size
        self._metadata_region = PersistentQueueMetadataRegion(
            self._file,
            self._address_size,
        )
        self._elem_size = elem_size
        self._capacity = (max_file_size - self._metadata_region.size) // elem_size

        if self._capacity <= 0:
            raise TooSmallBounds()

        # TODO: remove after adding dynamic address_size
        if self._capacity > pow(256, self._address_size):
            raise TooBigBounds()

    @property
    def capacity(self) -> int:
        return self._capacity

    def __del__(self) -> None:
        self._file.close()

    @property
    def _head(self) -> int | None:
        return self._metadata_region.head

    @property
    def _tail(self) -> int | None:
        return self._metadata_region.tail

    def _write_head(self, v: int | None) -> None:
        self._metadata_region.write_head(None if v is None else v % self._capacity)

    def _write_tail(self, v: int) -> None:
        self._metadata_region.write_tail(v % self._capacity)

    @property
    def length(self) -> int:
        if self._tail is None or self._head is None:
            return 0

        return ((self._tail - self._head) % self._capacity) + 1

    @property
    def is_empty(self) -> bool:
        return self.length == 0

    @property
    def is_full(self) -> bool:
        return self.length == self._capacity

    def put(self, value: bytes) -> None:
        if len(value) != self._elem_size:
            raise IncorrectValueLength()

        if self._tail is None or self._head is None:
            new_tail = self._head or 0
        else:
            new_tail = (self._tail + 1) % self._capacity

            # rewrite the head when not enough space
            # NOTE: to prevent this check is_full before calling put
            if new_tail == self._head:  # self.length == self._capacity
                self._write_head(new_tail + 1)

        if self._head is None:
            self._write_head(new_tail)

        self._file.seek(self._metadata_region.size + new_tail * self._elem_size)
        self._file.write(value)

        self._write_tail(new_tail)

        self._file.flush()
        os.fsync(self._file.fileno())

    @property
    def head(self) -> bytes:
        if self._tail is None or self._head is None:
            raise QueueIsEmpty()

        self._file.seek(self._metadata_region.size + self._head * self._elem_size)
        return self._file.read(self._elem_size)

    def pop(self) -> None:
        if self._tail is None or self._head is None:
            raise QueueIsEmpty()

        if self.length == 1:
            self._write_head(None)
        else:
            self._write_head(self._head + 1)
