
# Helper methods

def convert_message_to_command(client, message):
    parsed_message = parse(message)

    if client.state == PlayerState.LOGGING_IN:
        return while_not_logged(client, parsed_message)
    
    if client.state == PlayerState.PLACING_SHIPS:
        return while_placing_ships(client, parsed_message)
            
    if client.state == PlayerState.CAN_JOIN_GAMES:
        return while_in_lobby(client, parsed_message)
        
    if client.state == PlayerState.IN_GAME:
        return while_playing(client, parsed_message)

    if client.state == PlayerState.SENDING_LAYOUT:
        return while_game_ended(client, parsed_message)

    return ErrorCommand(client, "client has no state")

def while_not_logged(client, parsed_message):
    fingerprint = NickParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        return LogInCommand(client, fingerprint.get_nick(), fingerprint.get_salt())
    else:
        return ErrorCommand(client, "could not log in")


def while_placing_ships(client, parsed_message):
    fingerprint = PutShipParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        if client.player.add_ship_to_board(*fingerprint.get_params()):
            return MessageCommand(client ,"Ship placed")
    return ErrorCommand(client, "could not parse ship placement")

def while_game_ended(client, parsed_message):
    fingerprint = LayoutParseFingerPrint(parsed_message)
    if fingerprint.is_valid():
        game_id = fingerprint.get_game_id()
        game = Battleship().get_game_by_id(game_id)
        if game is not None:
            return game.check_for_cheating_by_layout(client.player, fingerprint.get_layout())
    return ErrorCommand(client, "layout not parsed")

def while_in_lobby(client, parsed_message):
    start_attempt = try_to_start(client, parsed_message)
    if start_attempt is not None:
        return start_attempt

    join_attempt = try_to_join(client, parsed_message)
    if join_attempt is not None:
        return join_attempt

    auto_attempt = try_to_auto(client, parsed_message)
    if auto_attempt is not None:
        return auto_attempt    

    list_attempt = try_to_list(client, parsed_message)
    if list_attempt is not None:
        return list_attempt

    return ErrorCommand(client, "could not join or start game")
        
    def try_to_start(client, parsed_message):
        fingerprint = StartParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            return Battleship.start_game(client, fingerprint.get_hash())       
        
    def try_to_list(client, parsed_message):
        fingerprint = ListParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            return Battleship.list_games(client)

    def try_to_join(client, parsed_message):
        fingerprint = JoinParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            _hash = fingerprint.get_hash
            if game is not None:
                return game.join_peer(client, _hash)

    
    def try_to_auto(client, parsed_message):
        fingerprint = AutoParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            return Battleship().get_auto_game(client)
            

def while_playing(client, parsed_message):
    
    shoot_attempt = try_to_shoot(client, parsed_message)
    if shoot_attempt is not None:
        return shoot_attempt    

    feedback_attempt = try_to_declare_hit(client, parsed_message)
    if feedback_attempt is not None:
        return feedback_attempt  
    
    def try_to_declare_hit():
        fingerprint = ShootParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                return game.hit() # TODO

    def try_to_declare_miss():
        fingerprint = ShootParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                return game.miss() # TODO
    
    def try_to_shoot():
        fingerprint = ShootParseFingerPrint(parsed_message)
        if fingerprint.is_valid():
            game_id = fingerprint.get_game_id()
            game = Battleship().get_game_by_id(game_id)
            if game is not None:
                return client.player.shoot(fingerprint.get_x, fingerprint.get_y, game_id)

def get_hash(server_salt, client_salt, ships):
    return 1


# Battleship main class


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Battleship(metaclass=Singleton):

    def __init__(self):
        self.game_server = Server()
        self.server_salt = random.randint(0,999999999999999999999)
        self.players = set()
        self.games = set()

    def list_games(self, client):
        message ="(games"
        for g in self.games:
            message += " " + g.game_to_text
        message += ")"
        return MessageCommand(client, message)

    def get_player_by_nick(self, nick):
        for p in self.players:
            if p.nick == nick:
                return p

    def get_game_by_id(self, id):
        for g in self.games:
            if g.id == id:
                return g

    def remove_game(self, game):
        for g in self.games:
            if g.id == game.id:
                self.games.remove(g)
                del g

    def add_player(self, player):
        self.players.add(player)

    def remove_player(self, player):
        for p in self.players:
            if p.nick == player.nick:
                self.players.remove(p)
                
    def nickname_in_use(self, nick):
        for p in self.players:
            if nick == p.nick:
                return True
        return False

    def get_first_free_game_by_nick(self, nick):
        pass

    def get_auto_game(self, client, _hash):
        for g in self.games:
            if g.state == GameState.WAITING:
                return g.join_peer(client, _hash)
        return self.start_game(client, _hash)

    def start_game(self, client, _hash):
        game = Game(client, _hash)
        self.games.add(game)
        return MessageCommand(client, "Game Started, ID: " + game.id)




# Code shared between the client and server.


import random
import asyncio

from lisp import *
from fingerprints import *
from enumerators import *
from communication import *
from game_classes import *
from shipserv import *

windows = True

asyncio.run(Battleship().game_server.start_server())
