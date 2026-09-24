"""Run the trusted scanner without network or LLM provider access."""

import socket
import sys


def deny_network(*args, **kwargs):
    raise PermissionError("Network is disabled for the local static audit")


socket.socket.connect = deny_network
socket.socket.connect_ex = deny_network
socket.create_connection = deny_network
socket.getaddrinfo = deny_network

from skillspector.cli import app

if __name__ == "__main__":
    app()
