import socket
import threading
from datetime import datetime

# Server setup
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 404

# Storage for active connections and messages
connected_users = {}

message_board = []
chat_rooms = {f"Room{i + 1}": {"participants": {}, "logs": []} for i in range(5)}

# Lock for thread safety
thread_lock = threading.Lock()

def client_handler(user_conn, client_addr):
    """Manages interaction with a single client."""
    user_id = None
    try:
        user_conn.sendall("Welcome to the Interactive Bulletin Board! Use '!register [username]' to join.\nUse !help for additional help.\n".encode())
        while True:
            data = user_conn.recv(1024).decode().strip()
            if not data:
                break

            result, user_id = process_client_input(data, user_id, user_conn)
            if result == "DISCONNECT":
                break
            user_conn.sendall(result.encode())
    except Exception as e:
        print(f"Error communicating with {client_addr}: {e}")
    finally:
        if user_id:
            with thread_lock:
                connected_users.pop(user_id, None)
                for room in chat_rooms.values():
                    room["participants"].pop(user_id, None)
            global_message(f"{user_id} has left the server.\n", None)
        user_conn.close()

def process_client_input(input_cmd, user_id, user_conn):
    """Handles parsing and executing client commands."""
    tokens = input_cmd.split()
    if not tokens:
        return "Invalid command. Use '!help' for a list of available commands.\n", user_id

    command = tokens[0]
    commands = {
        "!help": help_menu,
        "!register": register_user,
        "!send": send_message,
        "!retrieve": get_message,
        "!active": list_active_users,
        "!rooms": show_rooms,
        "!joinroom": join_room,
        "!roommsg": send_room_message,
        "!roomretrieve": retrieve_room_message,
        "!roomusers": room_user_list,
        "!leaveroom": exit_room,
        "!quit": disconnect_user,
    }

    if command not in commands:
        return "Unrecognized command. Use '!help' for assistance.\n", user_id

    try:
        return commands[command](tokens, user_id, user_conn)
    except Exception as err:
        return f"Error processing command: {err}\n", user_id

# Command Handlers
def register_user(tokens, user_id, user_conn):
    if user_id:
        return "You are already connected.\n", user_id
    if len(tokens) != 2:
        return "Usage: !register [username]\n", user_id

    new_user = tokens[1]
    with thread_lock:
        if new_user in connected_users:
            return "Username is taken. Please choose another.\n", user_id
        connected_users[new_user] = user_conn

    global_message(f"{new_user} joined the server!\n", new_user)
    return f"Welcome to the server, {new_user}!\n", new_user

def disconnect_user(tokens, user_id, user_conn):
    return "DISCONNECT", user_id

def send_message(tokens, user_id, user_conn):
    if not user_id:
        return "Register first with '!register [username]'.\n", user_id
    if len(tokens) < 2:
        return "Usage: !send [message]\n", user_id

    msg = {
        "user": user_id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "text": " ".join(tokens[1:]),
    }
    with thread_lock:
        message_board.append(msg)
        if len(message_board) > 5:  # Keep the last 5 messages
            message_board.pop(0)

    global_message(f"[{msg['time']}] {msg['user']} said: {msg['text']}\n", None)
    return "Message sent successfully.\n", user_id

def get_message(tokens, user_id, user_conn):
    if not user_id:
        return "Register first with '!register [username]'.\n", user_id
    if len(tokens) != 2:
        return "Usage: !retrieve [id]\n", user_id

    try:
        msg_index = int(tokens[1]) - 1
        with thread_lock:
            if 0 <= msg_index < len(message_board):
                msg = message_board[msg_index]
                return f"[{msg['time']}] {msg['user']} said: {msg['text']}\n", user_id
            return "Message ID not found.\n", user_id
    except ValueError:
        return "Invalid message ID. Must be a number.\n", user_id

def list_active_users(tokens, user_id, user_conn):
    with thread_lock:
        user_list = "\n".join(connected_users.keys())
    return f"Active users:\n{user_list}\n", user_id

def show_rooms(tokens, user_id, user_conn):
    room_list = "\n".join(chat_rooms.keys())
    return f"Available Rooms:\n{room_list}\n", user_id
    
def join_room(tokens, user_id, user_conn):
    if len(tokens) != 2:
        return "Usage: !joinroom [room]\n", user_id
    room_name = tokens[1]
    with thread_lock:
        if room_name in chat_rooms:
            chat_rooms[room_name]["participants"][user_id] = user_conn
            join_message = f"{user_id} has joined {room_name}.\n"
            for member_conn in chat_rooms[room_name]["participants"].values():
                if member_conn != user_conn:  # Avoid sending to the user themselves
                    try:
                        member_conn.sendall(join_message.encode())
                    except:
                        pass
            return f"You joined {room_name}.\n", user_id
        return "Room does not exist.\n", user_id

def send_room_message(tokens, user_id, user_conn):
    if len(tokens) < 3:
        return "Usage: !roommsg [room] [message]\n", user_id
    room_name, content = tokens[1], " ".join(tokens[2:])
    with thread_lock:
        if room_name in chat_rooms and user_id in chat_rooms[room_name]["participants"]:
            msg = {
                "user": user_id,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "text": content,
            }
            chat_rooms[room_name]["logs"].append(msg)
            for member, conn in chat_rooms[room_name]["participants"].items():
                if conn != user_conn:
                    try:
                        conn.sendall(f"Message in {room_name}: [{msg['time']}] {msg['user']} said: {msg['text']}\n".encode())
                    except:
                        pass
            return f"Message sent to {room_name}.\n", user_id
        return "Room does not exist or you are not a participant.\n", user_id

def retrieve_room_message(tokens, user_id, user_conn):
    if len(tokens) != 3:
        return "Usage: !roomretrieve [room] [id]\n", user_id
    room_name, msg_id = tokens[1], int(tokens[2]) - 1
    with thread_lock:
        if room_name in chat_rooms and user_id in chat_rooms[room_name]["participants"]:
            if 0 <= msg_id < len(chat_rooms[room_name]["logs"]):
                msg = chat_rooms[room_name]["logs"][msg_id]
                return f"[{msg['time']}] {msg['user']} said: {msg['text']}\n", user_id
            return "Message ID not found in the room.\n", user_id
        return "Room does not exist or you are not a participant.\n", user_id

def room_user_list(tokens, user_id, user_conn):
    if len(tokens) != 2:
        return "Usage: !roomusers [room]\n", user_id
    room_name = tokens[1]
    with thread_lock:
        if room_name in chat_rooms and user_id in chat_rooms[room_name]["participants"]:
            participants = "\n".join(chat_rooms[room_name]["participants"].keys())
            return f"Participants in {room_name}:\n{participants}\n", user_id
        return "Room does not exist or you are not a participant.\n", user_id
    
def exit_room(tokens, user_id, user_conn):
    if len(tokens) != 2:
        return "Usage: !leaveroom [room]\n", user_id
    room_name = tokens[1]
    with thread_lock:
        if room_name in chat_rooms and user_id in chat_rooms[room_name]["participants"]:
            leave_message = f"{user_id} has left {room_name}.\n"
            for member_conn in chat_rooms[room_name]["participants"].values():
                if member_conn != user_conn:
                    try:
                        member_conn.sendall(leave_message.encode())
                    except:
                        pass
            # Remove the user from the room
            chat_rooms[room_name]["participants"].pop(user_id)
            return f"You left {room_name}.\n", user_id
        return "Room does not exist or you are not a participant.\n", user_id

def global_message(msg, current_user):
    """Send a global message to all users in the board."""
    with thread_lock:
        for user, connection in connected_users.items():
            if user != current_user:
                try:
                    connection.sendall(msg.encode())
                except:
                    pass

def help_menu(tokens, user_id, user_conn):
    help_text = """
        Available Commands:
        - !help: Display this help menu.
        - !register [username]: Join the public board with a unique username.
        - !send [message]: Post a public message.
        - !retrieve [id]: View a specific public message by ID.
        - !active: See a list of active users.
        - !rooms: View available chat rooms.
        - !joinroom [room]: Join a private chat room.
        - !roommsg [room] [message]: Send a message to a chat room.
        - !roomretrieve [room] [id]: Retrieve a specific message from a chat room.
        - !roomusers [room]: List participants in a chat room.
        - !leaveroom [room]: Leave a chat room.
        - !quit: Disconnect from the server.
    """
    return help_text, user_id

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((SERVER_ADDRESS, SERVER_PORT))
        server_socket.listen()
        print(f"Server running on {SERVER_ADDRESS}:{SERVER_PORT}")
        while True:
            conn, addr = server_socket.accept()
            threading.Thread(target=client_handler, args=(conn, addr), daemon=True).start()