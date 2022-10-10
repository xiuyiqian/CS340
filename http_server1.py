import socket
import os
import sys

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
    print("response ====", response)
    connection, address = sock.accept()
    connection.sendall(b""+response.encode())
    connection.close()

def receive_request(port):
    host= socket.gethostname()  # host -> socket.gethostname() use to set machine IP
    print(host, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen()  # listen to all ip addresses

    while True:
        connection, address = sock.accept()

        request = b""
        while not request.endswith(b"\r\n\r\n"):
            request += connection.recv(1024)
        request = request.decode()
        print(request)  # Get print in our python console.

        # parse request
        request_list = request.split("\r\n")
        get_request = request_list[0].split(" ")
        if len(get_request) >= 3:
            file_name = get_request[1].split(".")[0]
            if file_name.startswith("/"):
                file_name = file_name[1:]
            print("file_name ====", file_name)
            found_file = "false"
            for filename in os.listdir('.'):
                print("traverse =====", filename)
                if filename.startswith(file_name):
                    if filename.endswith(".htm") or filename.endswith(".html"):
                        found_file = "true"
                        searchfile = open(filename, "r").read()
                        Send_response(sock, searchfile, "200")
                        break
                    else:
                        Send_response(sock, " ", "403")
            if not found_file:
                Send_response(sock, " ", "404")
        else:
            Send_response(sock, " ", "400")


if __name__ == '__main__':
    port = int(sys.argv[1])
    if port >= 1024:
        receive_request(port)
    else:
        sys.exit(1)

