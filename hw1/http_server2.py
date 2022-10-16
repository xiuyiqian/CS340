import socket
import os
import select
import sys
import queue

def createSock(port):
    host= socket.gethostbyname(socket.gethostname())  # host -> socket.gethostname() use to set machine IP
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #print("sock")
    #print(sock)
    sock.setblocking(0)  # 0: close block  1:open block
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()  # listen to all ip addresses
    return sock

def Send_response(sock, body, status_code):
    response_proto = "HTTP/1.1"
    if status_code == "200":
        response_status_text = "OK"
    elif status_code == "404":
        response_status_text = "NOT FOUND"
    elif status_code == "400":
        response_status_text = "BAD REQUEST"
    first_line = response_proto + " " + status_code + " " + response_status_text
    content_type = "Content-Type: text/html"
    connection = "Connection: keep-alive"
    content_length = "Content-Length:" + str(len(body))
    header = first_line + "\n" + content_type + "\n" + connection + "\n" + content_length
    response = header+"\r\n\r\n"+body+"\r\n\r\n"
    return response.encode()

def receive_request(port):
    sock = createSock(port);

    while True:
        # Sockets from which we expect to read
        inputs = [sock]
        # Sockets to which we expect to write
        outputs = []
        # Outgoing message queues (socket:Queue)
        message_queues = {}

        while inputs:
            # Wait for at least one of the sockets to be
            # ready for processing
            #print('waiting for the next event', file=sys.stderr)
            readable, writable, exceptional = select.select(inputs,
                                                            outputs,
                                                            inputs)
            # Handle inputs
            for s in readable:

                if s is sock:
                    # A "readable" socket is ready to accept a connection
                    connection, client_address = s.accept()
                    #print('  connection from', client_address,file=sys.stderr)
                    connection.setblocking(0)
                    inputs.append(connection)

                    # Give the connection a queue for data
                    # we want to send
                    message_queues[connection] = queue.Queue()
                else:
                    data = b""
                    while not data.endswith(b"\r\n\r\n"):
                        data += connection.recv(1024)
                    data = data.decode()
                    ##print(data)
                    # parse request
                    request_list = data.split("\r\n")
                    get_request = request_list[0].split(" ")
                    if len(get_request) >= 3:
                        file_name = get_request[1].split(".")[0]
                        if file_name.startswith("/"):
                            file_name = file_name[1:]
                        #print("file_name ====", file_name)
                        found_file = "false"
                        for filename in os.listdir('.'):
                            #print("traverse =====", filename)
                            if filename.startswith(file_name):
                                if filename.endswith(".htm") or filename.endswith(".html"):
                                    found_file = "true"
                                    searchfile = open(filename, "r").read()
                                    data = Send_response(sock, searchfile, "200")
                                    break
                                else:
                                    data = Send_response(sock, " ", "403")
                        if not found_file:
                            data = Send_response(sock, " ", "404")
                    else:
                        data = Send_response(sock, " ", "400")

                    #print(data)  # Get print in our python console.
                    if len(data)>0:
                        # A readable client socket has data
                        #print('  received {!r} from {}'.format(data, s.getpeername()), file=sys.stderr)
                        message_queues[s].put(data)
                        # Add output channel for response
                        if s not in outputs:
                            outputs.append(s)
                    else:
                        # Interpret empty result as closed connection
                        #print('  closing', client_address, file=sys.stderr)
                        # Stop listening for input on the connection
                        if s in outputs:
                            outputs.remove(s)
                        inputs.remove(s)
                        s.close()

                        # Remove message queue
                        del message_queues[s]

            # Handle outputs
            for s in writable:
                try:
                    next_msg = message_queues[s].get_nowait()
                except queue.Empty:
                    # No messages waiting so stop checking
                    # for writability.
                    #print('  ', s.getpeername(), 'queue empty', file=sys.stderr)
                    outputs.remove(s)
                else:
                    #print('  sending {!r} to {}'.format(next_msg,s.getpeername()),file=sys.stderr)
                    #print(type(next_msg))
                    #print(next_msg)
                    s.send(b""+next_msg)
                    if s in outputs:
                        outputs.remove(s)
                    inputs.remove(s)
                    s.close()


if __name__ == '__main__':
    port = int(sys.argv[1])
    if port >= 1024:
        receive_request(port)
    else:
        sys.exit(1)
