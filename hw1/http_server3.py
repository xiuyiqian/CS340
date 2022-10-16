import socket
import json

from http_server2 import Send_response

def isint(x):
    try:
        a = float(x)
        b = int(a)
    except (TypeError, ValueError):
        return False
    else:
        return a == b


def process_query(sock, path_components):
    parameters_list = path_components[1].split("&")
    param_list = []
    result = 1.0
    for param in parameters_list:
        operand = param.split("=")[1]
        print("param ====", operand + "\n")
        if not operand.isnumeric():
            print("not numberic ======", operand)
            Send_response(sock, "", "400")
            break
        if operand.isdigit():
            print("digit ====", operand + "\n")
            param_list.append(int(operand))
        else:
            param_list.append(float(operand))
        result *= float(operand)
    print("params_list===", param_list)
    response = {
        "operation": "product",
        "operands": param_list,
        "result": result
    }

    if abs(result) == float('inf'):
        response["result"] = "inf"
    elif isint(result):
        response["result"] = int(result)

    response = json.dumps(response)
    print("json=====", response, "str====", response)
    Send_response(sock, response, "200")


def receive_request():
    host, port = "localhost", 8080  # host -> socket.gethostname() use to set machine IP
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
        print("get_request", get_request)
        path_components = get_request[1].split("?")
        print("path_components", path_components)
        if "/product" not in request_list[0]:
            Send_response(sock, "", "404")
        if len(path_components) <= 1:
            Send_response(sock, "", "400")
        else:
            process_query(sock, path_components)

if __name__ == '__main__':
    receive_request()
