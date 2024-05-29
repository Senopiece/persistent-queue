class PersistentQueueException(Exception):
    def __init__(self):
        assert self.__doc__ is not None
        super().__init__(self.__doc__)


class IncorrectBounds(PersistentQueueException):
    pass


class TooBigBounds(IncorrectBounds):
    "Too big bounds, try decreasing max_file_size or increasing elem_size"


class TooSmallBounds(IncorrectBounds):
    "Too small bounds, try increasing max_file_size or decreasing elem_size"


class CapacityError(PersistentQueueException):
    pass


class InsufficientCapacity(CapacityError):
    "Insufficient capacity"


class QueueIsEmpty(CapacityError):
    "Queue is empty"


class IncorrectValueLength(PersistentQueueException, ValueError):
    "Incorrect value length"
