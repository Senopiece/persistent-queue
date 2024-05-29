from persistent_queue import PersistentQueue


q = PersistentQueue("pq", 20, 1)
print(q.capacity)

q.put(b"3")
