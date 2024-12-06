import socket
import threading
import sys

# Connection configuration
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 404

# Command list
VALID_COMMANDS = {
    "!register",
    "!send",
    "!retrieve",
    "!active",
    "!rooms",
    "!joinroom",
    "!roommsg",
    "!roomretrieve",
    "!roomusers",
    "!leaveroom",
    "!quit",
    "!help",
}

client_socket = None


def listen_for_responses(sock):
    """Continuously listen for messages from the server."""
    while True:
        try:
            server_response = sock.recv(1024).decode()
            if server_response:
                print(server_response, end="")
            else:
                print("Connection to server closed.")
                sock.close()
                break
        except Exception as e:
            print(f"Error receiving data: {e}")
            sock.close()
            break


def main():
    global client_socket
    print("Welcome to the Interactive Bulletin Board Terminal Client!")
    print("Use '!help' to see available commands.")

    while True:
        user_input = input().strip()
        if not user_input:
            continue

        args = user_input.split()
        command = args[0]

        if command not in VALID_COMMANDS:
            print(f"Unknown command: {command}. Use '!help' for a list of valid commands.")
            continue

        if command == "!register" and len(args) != 2:
            print("Usage: !register [username]")
            continue

        if command == "!send" and len(args) < 2:
            print("Usage: !send [message]")
            continue

        if command == "!retrieve" and len(args) != 2:
            print("Usage: !retrieve [id]")
            continue

        if command == "!joinroom" and len(args) != 2:
            print("Usage: !joinroom [room]")
            continue

        if command == "!roommsg" and len(args) < 3:
            print("Usage: !roommsg [room] [message]")
            continue

        if command == "!roomretrieve" and len(args) != 3:
            print("Usage: !roomretrieve [room] [id]")
            continue

        if command == "!roomusers" and len(args) != 2:
            print("Usage: !roomusers [room]")
            continue

        if command == "!leaveroom" and len(args) != 2:
            print("Usage: !leaveroom [room]")
            continue

        # Connect to the server
        if command == "!help":
            print("""Available Commands:\n!register [username]: Join the server.\n!send [message]: Post a public message.\n!retrieve [id]: Get a public message by ID.\n!active: List active users.\n!rooms: Show available chat rooms.\n!joinroom [room]: Join a chat room.\n!roommsg [room] [message]: Send a message to a chat room.\n!roomretrieve [room] [id]: Retrieve a message from a chat room.\n!roomusers [room]: List chat room users.\n!leaveroom [room]: Leave a chat room.\n!quit: Disconnect from the server.""")
            continue

        if command == "!quit":
            if client_socket:
                client_socket.sendall(command.encode())
                client_socket.close()
            print("Disconnected from server.")
            break

        if not client_socket:
            try:
                client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_socket.connect((SERVER_ADDRESS, SERVER_PORT))
                print(f"Connected to server at {SERVER_ADDRESS}:{SERVER_PORT}")
                threading.Thread(target=listen_for_responses, args=(client_socket,), daemon=True).start()
            except Exception as e:
                print(f"Failed to connect to server: {e}")
                sys.exit()

        try:
            client_socket.sendall(user_input.encode())
        except Exception as e:
            print(f"Error sending data: {e}")
            client_socket.close()
            client_socket = None
            break


if __name__ == "__main__":
    main()
