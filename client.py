from datetime import datetime
from multiprocessing import Process, Queue
from socket import socket
from threading import Thread
from tkinter import Label, Button, StringVar, Entry, Listbox, END, SINGLE

from utils.config import ADDRESS, PORT, BUF_READ_SIZE, GET_ARGS
from utils.utils import encode_data, decode_data, get_tk_root, Tk


class ChatClient:

    def __init__(self, login, password):
        self.login, self.password = login, password
        self.send_queue = Queue()
        self.read_queue = Queue()
        self.token = None
        self.jim_handler = self.JIMHandler(self)
        self.s = socket()

    def connect(self) -> None:
        self.s.connect((ADDRESS, PORT))

    def close(self) -> None:
        self.s.close()

    def send_data(self) -> None:
        while True:
            self.s.send(encode_data(self.send_queue.get()))

    def read_data(self) -> None:
        while True:
            self.read_queue.put(decode_data(self.s.recv(BUF_READ_SIZE)))

    def create_presence(self) -> dict:
        return {
            "action": "presence",
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "login": self.login,
            "password": self.password
        }

    def send_presence(self, presence) -> dict:
        self.s.send(encode_data(presence))
        return decode_data(self.s.recv(BUF_READ_SIZE))

    def run(self) -> None:

        self.connect()
        resp = self.send_presence(self.create_presence())

        if resp["response"] == 200:
            self.token = resp["token"]
        else:
            raise Exception(f"{resp['response']} {resp['alert']}")

        self.run_processes()

        print(self.login)

        root = get_tk_root()
        chat = self.ChatView(root, self)
        Thread(target=chat.print_data, daemon=True).start()

        root.mainloop()

    def run_processes(self) -> None:
        t1 = Process(target=self.send_data)
        t1.daemon = True
        t1.start()

        t2 = Process(target=self.read_data)
        t2.daemon = True
        t2.start()

    class JIMHandler:

        def __init__(self, client):
            self.client = client

        def get_jim_template(self) -> dict:
            return {
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "token": self.client.token
            }

        def get_update_contacts(self) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "update_contacts",
            })
            return buf

        def get_probe(self) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "probe",
            })
            return buf

        def get_msg(self, message: str, to: str) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "msg",
                "to": to,
                "from": self.client.login,
                "message": message,
            })
            return buf

        def get_quit(self) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "quit",
            })

            return buf

        def get_authenticate(self, login: str, password: str) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "authenticate",
                "login": login,
                "password": password
            })

            return buf

        def get_join(self, room: str) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "join",
                "room": room
            })

            return buf

        def get_leave(self, room: str) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "leave",
                "room": room
            })

            return buf

        def get_check_contact(self, login: str) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "check_contact",
                "login": login
            })

            return buf

        def get_delete_chat(self, room: str) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "delete_chat",
                "room": room
            })

            return buf

        def get_create_chat(self, room: str) -> dict:
            buf = {}
            buf.update(self.get_jim_template())
            buf.update({
                "action": "create_chat",
                "room": room
            })

            return buf

    class ChatView:

        def get_data(self) -> None:
            if self.my_msg.get() == "quit":
                self.master.destroy()
            if self.contact_list.curselection():
                self.client.send_queue.put(self.client.jim_handler.get_msg(message=self.my_msg.get(),
                                                                           to=self.contact_list.get(
                                                                               self.contact_list.curselection())))
                self.my_msg.set("")

        def print_data(self) -> None:
            while True:
                msg = self.client.read_queue.get()
                if "action" in msg:
                    self.msg_list.insert(END, self.format_message(msg))
                elif "response" in msg:
                    self.msg_list.insert(END, self.format_error_message(msg))
                elif "contacts" in msg:
                    self.contact_list.delete(0, END)
                    for i in msg["contacts"]:
                        self.contact_list.insert(END, i)
                else:
                    pass

        def update_contacts(self):
            self.client.send_queue.put(self.client.jim_handler.get_update_contacts())

        def create_chat(self):
            self.client.send_queue.put(self.client.jim_handler.get_create_chat(self.chat.get()))

        def join_chat(self):
            self.client.send_queue.put(self.client.jim_handler.get_join(self.chat_join.get()))

        def __init__(self, master: Tk, client):
            self.format_message = lambda msg: f"{ msg['time']}: {msg['from']}>{msg['message']}"
            self.format_error_message = lambda msg: f"Error {msg['response']}: {msg['error']}"

            self.client = client
            self.master = master
            master.title(client.login)

            self.label_my_msg = Label(master, text="Your message")
            self.label_my_msg.grid(row=0, column=0)

            self.my_msg = StringVar()
            self.entry = Entry(self.master, textvariable=self.my_msg)
            self.entry.grid(row=0, column=1)

            self.label_to = Label(master, text="Chat name")
            self.label_to.grid(row=5, column=0)

            self.chat = StringVar()
            self.entry_chat = Entry(self.master, textvariable=self.chat)
            self.entry_chat.grid(row=5, column=1)

            self.btn_create_chat = Button(master=self.master, text='Create chat', command=self.create_chat)
            self.btn_create_chat.grid(row=5, column=2)

            self.label_join = Label(master, text="Chat name")
            self.label_join.grid(row=6, column=0)

            self.chat_join = StringVar()
            self.entry_chat_join = Entry(self.master, textvariable=self.chat_join)
            self.entry_chat_join.grid(row=6, column=1)

            self.btn_join_chat = Button(master=self.master, text='Join chat', command=self.join_chat)
            self.btn_join_chat.grid(row=6, column=2)

            self.button = Button(master=self.master, text='Send', command=self.get_data)
            self.button.grid(row=4, column=1)

            self.msg_list = Listbox(self.master, height=15, width=50)
            self.msg_list.grid(row=3, column=0, columnspan=2)

            self.label_contacts = Label(master, text="Contacts")
            self.label_contacts.grid(row=0, column=3)

            self.contact_list = Listbox(self.master, height=15, width=30, selectmode=SINGLE)

            self.contact_list.grid(row=1, column=3, rowspan=4)

            self.btn_update_contacts = Button(master=self.master, text='Update', command=self.update_contacts)
            self.btn_update_contacts.grid(row=4, column=4)

            self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        def on_closing(self) -> None:
            self.master.destroy()
            self.client.s.close()


if __name__ == '__main__':
    ChatClient(*GET_ARGS()).run()