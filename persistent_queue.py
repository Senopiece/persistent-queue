import os
from typing import IO


class AtomicValue:
    def __init__(self, file: IO[bytes], offset: int, size: int) -> None:
        self._file = file
        self._offset = offset
        self._size = size
        self._raw_read()

    def _read_selector(self) -> int:
        self._file.seek(self._offset)
        return int.from_bytes(self._file.read(1))

    def _seek_to_second(self) -> None:
        self._file.seek(self._offset + 1 + self._size)

    def _seek_to_first(self) -> None:
        self._file.seek(self._offset + 1)

    def _raw_read(self) -> int:
        selector = self._read_selector()

        if selector != 0:
            self._seek_to_second()

        value = int.from_bytes(self._file.read(self._size))

        self._cached_selector = selector
        self._cached_value = value

        return value

    def read(self) -> int:
        return self._cached_value

    def write(self, value: int) -> None:
        """Atomic operation"""
        new_selector = 0

        if self._cached_selector == 0:
            new_selector = 1
            self._seek_to_second()
        else:
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
    def head(self) -> int:
        return self._head_section.read()

    @property
    def tail(self) -> int:
        return self._tail_section.read()

    @property
    def size(self) -> int:
        """In bytes"""
        return self._head_section.size + self._tail_section.size

    def write_head(self, value: int) -> None:
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
        self._mod = self._capacity + 1
        assert (
            self._capacity > 0
        ), "too small bounds, try increasing max_file_size or decreasing elem_size"
        assert (
            pow(256, self._address_size) >= self._capacity
        ), "too big bounds, try decreasing max_file_size or increasing elem_size"

    @property
    def capacity(self) -> int:
        return self._capacity

    def __del__(self) -> None:
        self._file.close()

    @property
    def _head(self) -> int:
        return self._metadata_region.head

    @property
    def _tail(self) -> int:
        return (self._metadata_region.tail + 1) % self._mod

    def _write_head(self, v: int) -> None:
        self._metadata_region.write_head(v % self._mod)

    def _write_tail(self, v: int) -> None:
        self._metadata_region.write_tail((v - 1) % self._mod)

    @property
    def length(self) -> int:
        return (self._tail - 1 - self._head) % self._mod

    @property
    def is_empty(self) -> bool:
        return self.length == 0

    def put(self, value: bytes) -> None:
        assert len(value) == self._elem_size, "Incorrect value length"
        assert self._capacity > self.length, "Insufficient capacity"

        old_tail = self._tail

        self._file.seek(self._metadata_region.size + old_tail * self._elem_size)
        self._file.write(value)

        self._write_tail(old_tail + 1)

        self._file.flush()
        os.fsync(self._file.fileno())

    @property
    def head(self) -> bytes:
        assert not self.is_empty

        self._file.seek(self._metadata_region.size + self._head * self._elem_size)
        return self._file.read(self._elem_size)

    def pop(self) -> None:
        assert not self.is_empty

        self._write_head(self._head + 1)
