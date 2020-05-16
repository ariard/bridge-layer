#!/usr/bin/env python3
from pyln.client import Plugin
import time
import threading
import os
import socket

plugin = Plugin()

from_bitcoind = []
from_clightning = []

def sendcustommsg(plugin, node_id):
    while True:
        time.sleep(1) 
        if len(from_bitcoind) != 0 :
            to_send = from_bitcoind.pop(0)
            plugin.log("Pluging layer-bridge.py sendcustommsg {}".format(to_send.hex()))
            plugin.rpc.dev_sendcustommsg(node_id, to_send.hex())

def peer_management(plugin, port):
    plugin.log("Plugin layer-bridge.py Waiting connections...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:    
        s.bind(('127.0.0.1', port))
        s.listen()
        conn, addr = s.accept()
        with conn:
            plugin.log("Pluging layer-bridge.py connection received!")
            while True:
                time.sleep(1)
                try:
                    data = conn.recv(1024, socket.MSG_DONTWAIT)
                    plugin.log("Pluging layer-bride.py received {}".format(data.hex()))
                    from_bitcoind.append(data)
                except BlockingIOError:
                    pass

                if len(from_clightning) != 0 :
                    to_send = from_clightning.pop(0)
                    plugin.log("Pluging layer-bride.py sending {msg} and stripped {stripped}".format(
                        msg=to_send,
                        stripped=to_send[8:]
                    ))
                    try:
                        conn.sendall(bytearray.fromhex(to_send[8:]))
                    except BrokenPipeError:
                        pass

@plugin.method("alice_on")
def alice_on(plugin, name="alice_on"):
    """This is the documentation string for the peering-function.

    It gets reported as the description when registering the function
    as a method with `lightningd`.

    """
    port = #your port
    t = threading.Thread(target=peer_management, args=[plugin, port])
    t.daemon = True
    t.start()
    node_id = # your node to_bob
    t = threading.Thread(target=sendcustommsg, args=[plugin, node_id])
    t.daemon = True
    t.start()
    plugin.log("Plugin layer-bridge.py alice_on")


@plugin.method("bob_on")
def bob_on(plugin, name="bob_on"):
    """This is the documentation string for the peering-function.

    It gets reported as the description when registering the function
    as a method with `lightningd`.

    """
    port = # your port
    t = threading.Thread(target=peer_management, args=[plugin, port])
    t.daemon = True
    t.start()
    node_id =  # your node to_alice
    t = threading.Thread(target=sendcustommsg, args=[plugin, node_id])
    t.daemon = True
    t.start()
    plugin.log("Plugin layer-bridge.py bob_on")

@plugin.init()
def init(options, configuration, plugin, **kwargs):

    # Start a bitcoin peer management thread
    plugin.log("Plugin layer-bridge.py initialized")

@plugin.hook("custommsg")
def on_custommsg(peer_id, message, plugin, **kwargs):
    plugin.log("Got a custom message {msg} from peer {peer_id}".format(
        msg=message,
        peer_id=peer_id
    ))
    from_clightning.append(message)
    return { 'return' : "continue" }

plugin.run()
