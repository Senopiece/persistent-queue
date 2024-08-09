from persistent_queue import PersistentQueue


q = PersistentQueue("pq", 20, 1)
print(q.capacity)

while True:
    la = input().split()

    r = la[0]
    v = 1
    try:
        v = int(la[1])
    except IndexError:
        pass

    if r == "pop":
        q.pop(v)
    elif r == "head":
        print(">", q.head(v).decode())
    elif r == "len":
        print(">", q.length)
    else:
        q.put(r.encode())
