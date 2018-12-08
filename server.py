import select
import time
import uuid
from socket import socket
from threading import Thread

from utils.config import ADDRESS, PORT, LISTEN, BUF_READ_SIZE
from utils.utils import encode_data, decode_data, get_name_by_value


class ChatServer:

    def __init__(self):
        self.clients = []
        self.contacts = dict()
        self.s = socket()
        self.jim_handler = self.JIMHandler(self)

    def connect(self) -> None:
        self.s.bind((ADDRESS, PORT))
        self.s.listen(LISTEN)

    def select_clients(self):
        while True:
            time.sleep(0.1)
            try:
                readable, writable, err = select.select(self.clients, self.clients, [])
                if len(readable) > 0:
                    self.handle_read_sockets(readable)

            except Exception as error:
                pass

    def run(self) -> None:
        self.connect()
        print("Server started")
        Thread(target=self.select_clients, daemon=True).start()
        while True:
            client, addr = self.s.accept()

            if self.handle_presence(client):
                self.clients.append(client)
                self.send_contacts()
                print("Client connected:", addr)

    def write_to_socket(self, sock, data):
        try:
            sock.send(data)
        except:
            self.sock_disconnect(sock)

    def handle_read_sockets(self, readable: list) -> None:
        for read in readable:
            if read in self.clients:
                try:
                    self.parse_message(decode_data(read.recv(BUF_READ_SIZE)), read)
                except:
                    self.sock_disconnect(read)

    def sock_disconnect(self, sock: socket) -> None:
        sock_name = get_name_by_value(self.contacts, sock)
        print("Client disconnnected.", sock_name)
        self.clients.remove(sock)
        self.contacts.pop(sock_name)
        self.send_contacts()

    def handle_presence(self, client: socket) -> bool:
        print("Handle presence")
        client.setblocking(True)
        data = decode_data(client.recv(BUF_READ_SIZE))

        response = {
            "response": 400,
            "alert": "Smth went wrong"
        }
        print("Presence received")

        if "action" in data and data["action"] == "presence":
            if "login" in data and "password" in data:

                if data["login"] in self.contacts:
                    response["alert"] = "This user is already exists"

                else:
                    self.contacts[data["login"]] = client
                    response["response"] = 200
                    response["token"] = str(uuid.uuid4())
                    print("All clear")

        print(self.contacts)

        self.write_to_socket(client, encode_data(response))

        return response["response"] == 200

    def send_contacts(self):
        for login, sock in self.contacts.items():
            if not isinstance(sock, list):
                self.jim_handler.handle_update_contacts(dict(), sock)

    def parse_message(self, message: dict, sender: socket) -> None:
        msg_handlers = self.jim_handler.get_handlers()

        if "action" in message and message["action"] in msg_handlers:
            msg_handlers[message["action"]](message, sender)
        else:
            msg_handlers["error"](message, sender)

    class JIMHandler:

        def __init__(self, server):
            self.server = server
            self.get_error_response = lambda code, error: {"response": code, "error": error}

        def handle_probe(self, message: dict, sender: socket) -> None:
            pass

        def handle_msg(self, message: dict, sender: socket) -> None:
            if message["to"] in self.server.contacts:
                if isinstance(self.server.contacts[message["to"]], list):

                    message["from"] = f'{message["to"]}:{message["from"]}'

                    for to in self.server.contacts[message["to"]]:
                        self.server.write_to_socket(to, encode_data(message))
                else:
                    to = self.server.contacts[message["to"]]
                    self.server.write_to_socket(to, encode_data(message))
            else:
                msg = self.get_error_response(404, f"User <{message['to']}> not found")
                self.server.write_to_socket(sender, encode_data(msg))

        def handle_quit(self, message: dict, sender: socket) -> None:
            pass

        def handle_authenticate(self, message: dict, sender: socket) -> None:
            pass

        def handle_join(self, message: dict, sender: socket) -> None:
            if message["room"] in self.server.contacts:
                self.server.contacts[message["room"]].append(sender)
                self.handle_update_contacts(dict(), sender)
            else:
                pass

        def handle_leave(self, message: dict, sender: socket) -> None:
            pass

        def handle_check_contact(self, message: dict, sender: socket) -> None:
            pass

        def handle_delete_chat(self, message: dict, sender: socket) -> None:
            pass

        def handle_create_chat(self, message: dict, sender: socket) -> None:
            if message["room"] not in self.server.contacts:
                self.server.contacts[message["room"]] = [sender]
                self.handle_update_contacts(dict(), sender)
            else:
                pass

        def handle_error(self, message: dict, sender: socket) -> None:
            response = {
                "response": 404,
                "error": "This action not found"
            }

            response.update(message)
            self.server.write_to_socket(sender, encode_data(response))

        def handle_update_contacts(self, message: dict, sender: socket) -> None:
            msg = {"contacts": [login for login in self.server.contacts]}
            self.server.write_to_socket(sender, encode_data(msg))

        def get_handlers(self):
            return {
                "probe": self.handle_probe,
                "msg": self.handle_msg,
                "quit": self.handle_quit,
                "authenticate": self.handle_authenticate,
                "join": self.handle_join,
                "leave": self.handle_leave,
                "check_contact": self.handle_check_contact,
                "delete_chat": self.handle_delete_chat,
                "create_chat": self.handle_create_chat,
                "error": self.handle_error,
                "update_contacts": self.handle_update_contacts
            }


if __name__ == '__main__':
    ChatServer().run()