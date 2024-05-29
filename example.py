from persistent_queue import PersistentQueue


q = PersistentQueue("pq", 20, 1)
print(q.capacity)

while True:
    r = input()
    if r == "pop":
        q.pop()
    elif r == "head":
        print(">", q.head.decode())
    else:
        q.put(r.encode())
