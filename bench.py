import tempfile
import time
from persistent_queue import PersistentQueue

BENCHMARK_COUNT = 100


def time_it(func):
    def _exec(*args, **kwargs):
        start = time.time()
        func(*args, **kwargs)
        end = time.time()
        print(
            "\t{} => time used: {:.4f} seconds.".format(
                func.__doc__,
                (end - start)))

    return _exec

max_file_size = 1024 # in bytes

class PersistentQueueBench(object):
    """Benchmark PersistentQueue performance."""

    def __init__(self, prefix=None):
        self.path = prefix

    @time_it
    def benchmark_persistent_write(self):
        """Writing <BENCHMARK_COUNT> items."""

        self.path = tempfile.mktemp('b_persistent_10000')
        q = PersistentQueue(self.path, max_file_size, 5)
        for i in range(BENCHMARK_COUNT):
            q.put(b'bench')
        assert q.length == BENCHMARK_COUNT

    @time_it
    def benchmark_persistent_read_write(self):
        """Reading-Writing <BENCHMARK_COUNT> items."""

        self.path = tempfile.mktemp('b_persistent_10000')
        q = PersistentQueue(self.path, max_file_size, 5)
        for i in range(BENCHMARK_COUNT):
            q.put(b'bench')

        for i in range(BENCHMARK_COUNT):
            q.pop()
        assert q.length == 0

    @classmethod
    def run(cls):
        print(cls.__doc__)
        ins = cls()
        for name in sorted(cls.__dict__):
            if name.startswith('benchmark'):
                func = getattr(ins, name)
                func()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        BENCHMARK_COUNT = int(sys.argv[1])
    print("<BENCHMARK_COUNT> = {}".format(BENCHMARK_COUNT))
    persistent_bench = PersistentQueueBench()
    persistent_bench.run()
