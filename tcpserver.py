import socket
import json

import scipy.io as sio

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind( ('127.0.0.1', 8080) )

server.listen(5)

print('connected!')

conn, client_addr = server.accept()

all_data = []
while 1:
# for k in range(0,200):
    length = conn.recv(5)
    # length = conn.recv(20000)
    print(length)
    # print(int(length))

    if length==b'':
        # print(len(all_data))
        # sio.savemat('testdata.mat', mdict={'data': all_data})
        break

    data = conn.recv(int(length))

    # data = conn.recv(20000)
    # print(data)
    # data = json.loads(data)

    # all_data.extend(data['dec_data'])

    # print(json.loads(data))

conn.close()