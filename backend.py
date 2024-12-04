import socket
import threading
import json
from datetime import datetime

# Server configuration
HOST = '127.0.0.1'
PORT = 65432

# Global data structures
users = {}  # Mapping of {username: connection}
messages = []  # Public messages
groups = {f"group{i+1}": [] for i in range(5)}  # Private groups with users

# Lock for thread safety
lock = threading.Lock()


def handle_client(conn, addr):
    """Handles a single client connection."""
    username = None
    try:
        while True:
            data = conn.recv(1024).decode()
            if not data:
                break

            # Parse the received data
            command = json.loads(data)
            action = command.get("command")

            if action == "connect":
                username = command.get("username")
                with lock:
                    if username in users:
                        conn.sendall(json.dumps({"status": "error", "message": "Username already taken"}).encode())
                        break
                    users[username] = conn
                    notify_all(f"{username} joined the group.")
                conn.sendall(json.dumps({"status": "success", "message": "Connected successfully"}).encode())

            elif action == "post":
                subject = command.get("subject")
                body = command.get("body")
                if username:
                    message_id = len(messages) + 1
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    message = {"id": message_id, "sender": username, "timestamp": timestamp, "subject": subject, "body": body}
                    with lock:
                        messages.append(message)
                        if len(messages) > 2:  # Keep only the last 2 messages
                            messages.pop(0)
                    notify_all(f"Message posted by {username}: {subject}")
                else:
                    conn.sendall(json.dumps({"status": "error", "message": "Not connected"}).encode())

            elif action == "users":
                user_list = list(users.keys())
                conn.sendall(json.dumps({"status": "success", "users": user_list}).encode())

            elif action == "leave":
                if username:
                    with lock:
                        del users[username]
                        notify_all(f"{username} left the group.")
                    break

            elif action == "message":
                message_id = command.get("id")
                with lock:
                    message = next((msg for msg in messages if msg["id"] == message_id), None)
                if message:
                    conn.sendall(json.dumps({"status": "success", "message": message}).encode())
                else:
                    conn.sendall(json.dumps({"status": "error", "message": "Message not found"}).encode())

            elif action == "groups":
                conn.sendall(json.dumps({"status": "success", "groups": list(groups.keys())}).encode())

            elif action == "groupjoin":
                group_name = command.get("group")
                if group_name in groups:
                    with lock:
                        groups[group_name].append(username)
                    conn.sendall(json.dumps({"status": "success", "message": f"Joined {group_name}"}).encode())
                else:
                    conn.sendall(json.dumps({"status": "error", "message": "Group not found"}).encode())

            elif action == "grouppost":
                group_name = command.get("group")
                subject = command.get("subject")
                body = command.get("body")
                if group_name in groups:
                    message = {"sender": username, "subject": subject, "body": body}
                    with lock:
                        groups[group_name].append(message)
                    conn.sendall(json.dumps({"status": "success", "message": f"Posted in {group_name}"}).encode())
                else:
                    conn.sendall(json.dumps({"status": "error", "message": "Group not found"}).encode())

    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        conn.close()
        if username:
            with lock:
                if username in users:
                    del users[username]
                notify_all(f"{username} left the group.")


def notify_all(message):
    """Sends a message to all connected users."""
    for conn in users.values():
        conn.sendall(json.dumps({"status": "notification", "message": message}).encode())


def start_server():
    """Starts the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen()
        print(f"Server listening on {HOST}:{PORT}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr)).start()


if __name__ == "__main__":
    start_server()
