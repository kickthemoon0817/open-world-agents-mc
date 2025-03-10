from javascript import require, On

from owa.registry import CALLABLES, LISTENERS, activate_module

activate_module("owa_env_minecraft")

host = '127.0.0.1'
port = 25565

bot_creator = CALLABLES["mineflayer.createBot"]
bot1 = bot_creator(host, port, 'firstman')
bot2 = bot_creator(host, port, 'secondman')

@On(bot1, 'spawn')
def test(*args):
    print('spawn succesfully!')

@On(bot2, 'spawn')
def test(*args):
    print('spawn succesfully!')
