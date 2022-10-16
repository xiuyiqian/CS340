import socket
import sys
import errno

def process_query(website):
    components = website.split("/")
    host = components[2]
    path = ""
    path = b"/" + str.encode(path.join(components[3:]))
    port = 80  # default port is 80
    if len(components[2].split(":")) != 1:
        port = int(components[2].split(":")[1])
        host = components[2].split(":")[0]
    return host, port, path

def run_socket(website):
    try:
        check_https(website)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)  # 5 seconds
        host, port, path = process_query(website)
        sock.connect((host, port))
        host = b"" + host.encode()
        # print("host:", host, "path:", path, "port:", port)
        request = b"GET / HTTP/1.0\r\nHost:" + host + b"\r\n\r\n" + path
        sock.sendall(request)

        response = b""
        while True:
            chunk = sock.recv(4096)
            if len(chunk) == 0:  # No more data received, quitting
                break
            response = response + chunk

        sock.close()
    except socket.error or socket.timeout:
        print("sys.exit", errno.EACCES)
        return socket.error or socket.timeout
    return response.decode(encoding="ISO-8859-1")

def check_https(website):
    if not website.startswith("http://"):
        print("sys.exit", errno.EACCES)
        sys.exit(errno.EACCES)
    if website.startswith("https://"):
        sys.stderr.write("Vist HTTPS \n")
        print("sys.exit", errno.EACCES)
        sys.exit(errno.EACCES)

def check_response(text, count):
    if count >= 10:
        sys.stderr.write("Too many redirect chains")
        print("sys.exit", errno.EACCES)
        sys.exit(errno.EACCES)
    text = run_socket(text)
    if text == socket.error or text == socket.timeout or text == errno.EACCES:
        sys.exit(errno.EACCES)
    text = text.split('\r\n\r\n')  # split the header and body by two new lines
    header_list = text[0].split("\n")
    body = text[1]
    status_code = ""
    location = ""
    content_type = ""
    for h in header_list:
        if h.startswith("HTTP"):
            status_code = h.split(" ")[1]
        if h.startswith("Location"):
            location = h.split(" ")[1]
        if h.startswith("Content-Type"):
            content_type = h.split(" ")[1]
    print("status_code ===", status_code, "content_type ===", content_type)
    if "200" == status_code:
        if content_type.startswith("text/html"):
            print(body)
        sys.exit(0)
    else:
        if status_code >= "400":
            print(body)
            print("sys.exit", errno.EACCES)
            sys.exit(errno.EACCES)
        if "302" == status_code or "301" == status_code:
            # take action to redirect
            sys.stderr.write("Redirected to: " + location + "\n")
            check_response(location, count+1)
    sys.exit(0)

if __name__ == '__main__':
    n = len(sys.argv)
    if n <= 1:
        sys.stderr.write("Please type in website")
        sys.exit(errno.EACCES)
    website = sys.argv[1]
    check_response(website, 1)