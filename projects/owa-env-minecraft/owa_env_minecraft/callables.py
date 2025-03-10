from javascript import require, On

from owa.registry import CALLABLES

mineflayer = require('mineflayer')
pathfinder = require('mineflayer-pathfinder')


@CALLABLES.register("mineflayer.createBot")
def create_bot(host, port, username):
    def is_valid_host(host):
        import socket
        try:
            socket.gethostbyname(host)
            return True
        except socket.error:
            return False

    assert is_valid_host(host)
    assert isinstance(host, str)

    assert isinstance(port, int)
    assert 1 <= port <= 65535

    assert isinstance(username, str)

    bot = mineflayer.createBot(
        {
            'host': host,
            'port': port,
            'username': username
        }
    )
    return bot
