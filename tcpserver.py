import socket
import json

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind( ('127.0.0.1', 8080) )

server.listen(5)

print('connected!')

conn, client_addr = server.accept()

while 1:
# for k in range(0,200):
    data = conn.recv(20000)
    print(data)

    # print(json.loads(data))

conn.close()