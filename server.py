import asyncio
import websockets
import json

PLAYERS = set()

async def on_connect(websocket):
    if len(PLAYERS) < 4:
        await register_player(websocket)
        # Welcome message is sent here
        await websocket.send("welcome_message")
    else:
        print("Session is full")

async def register_player(websocket):
    PLAYERS.add(websocket)
    message = "player_pos"
    await notify_players(message)

async def notify_players(websocket):
    if PLAYERS:
        message = 'test'
        await asyncio.wait([player.send(message) for player in PLAYERS])

async def add_player(websocket):
    print("tetystr")
    if len(PLAYERS) < 4:
        if PLAYERS.add(websocket):
            await notify_players(websocket)

async def server(websocket, path):
    async for message in websocket:
        data = json.loads(message)
        if data["msg_code"] == "connect":
            # Add new player on connect
            await add_player(websocket)
            print(f'Number of players: {len(PLAYERS)}')
        elif data["msg_code"] == "player_move":
            pass
        elif data["msg_code"] == "player_plant_bomb":
            pass
        elif data["msg_code"] == "disconnect":
            # Remove player
            pass
        else:
            print("Unknown message.")

        await websocket.send(f'Server got your message: {message}')


start_server = websockets.serve(server, "localhost", 5000)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()