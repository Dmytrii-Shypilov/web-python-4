from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
import json
import logging
import mimetypes
import pathlib
import socket
import urllib.parse

logging.basicConfig(level=logging.DEBUG,
                        format='%(threadName)s %(asctime)s %(message)s')

BASE_DIR = pathlib.Path() 
IP = "127.0.0.1"
PORT = 5000
SERVER_ADDRESS = ('', 3000)
BUFFER = 1024

def send_data_to_socket(data, ip, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(data,(ip, port))
    client_socket.close()

    

class MyHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case "/":
                self.send_html('index.html')
            case "/message.html":
                self.send_html('message.html')
            case _:
               
                if BASE_DIR.joinpath(route.path[1:]).exists:
                    self.send_static(route.path[1:])
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(data, IP, PORT)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def send_html(self, html_file, status=200):
        self.send_response(status)
        self.send_header("Content-Type", 'text/html')
        self.end_headers()
        with open(html_file, 'rb') as f:
            self.wfile.write(f.read())

    def send_static(self, filename):
        self.send_response(200)
        mt = mimetypes.guess_type(filename)
        self.send_header('Content/Type', 'text/html')
        self.end_headers()
        with open(f"{filename}", 'rb') as file:
            self.wfile.write(file.read())

def update_data(data_part, timestamp):
    with open(BASE_DIR.joinpath('storage/data.json'), 'r', encoding='utf-8') as file:
            raw_data = file.read()
            
    if not raw_data:
        return {timestamp: data_part}
    else:
        prev_data = json.loads(raw_data)
        prev_data[timestamp] = data_part
        return prev_data


def save_data_to_file(data):
    try:
        parsed_data = urllib.parse.unquote_plus(data.decode())
        dict_data = {key: value for key, value in [el.split('=') for el in parsed_data.split('&')]}
        timestamp = str(datetime.now())
        updated_data = update_data(dict_data, timestamp)
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as file:
            json.dump(updated_data, file, ensure_ascii=False)
    except ValueError as err:
        logging.error(f"Something is wrong with parsing: {data}")
    except OSError as err:
        logging.error(f"Writing error {dict_data}")

def run_socket_server(ip, port):

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((ip, port))
    try: 
        while True:
            data, address = server_socket.recvfrom(BUFFER)
            save_data_to_file(data)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()



def run_server(server=HTTPServer, handler=MyHTTPHandler):
    address = SERVER_ADDRESS
    http_server = server(address, handler)
    http_server.serve_forever()
    


if __name__ == "__main__":
    

    app_thread = Thread(target=run_server)
    app_thread.start()
    

    socket_thread = Thread(target=run_socket_server, args=(IP, PORT))
    socket_thread.start()
    
    