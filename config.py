import argparse


def get_args() -> tuple:
    arg = argparse.ArgumentParser()
    arg.add_argument("--login", type=str)
    arg.add_argument("--pasword", type=str)
    res = vars(arg.parse_args())
    return res["login"], res["password"]


def get_args_from_input() -> tuple:
    login = input("Enter login: ")
    password = input("Enter password: ")
    return login, password


ADDRESS = 'localhost'
PORT = 9090
ENCODING = "utf-8"
SERVER_TIMEOUT = 0
LISTEN = 10
BUF_READ_SIZE = 1024
GET_ARGS = get_args