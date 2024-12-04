import socket
import json

HOST = '127.0.0.1'
PORT = 65432


def send_command(client, command):
    """Sends a command to the server and receives the response."""
    client.send(json.dumps(command).encode())
    response = client.recv(1024).decode()
    return json.loads(response)


def display_menu():
    """Displays the command menu."""
    print("\n=== Bulletin Board Commands ===")
    print("1. Post a message")
    print("2. View active users")
    print("3. Fetch a message by ID")
    print("4. Leave the board")
    print("5. View groups")
    print("6. Join a group")
    print("7. Post in a group")
    print("0. Exit")


def client_program():
    """Runs the client program."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((HOST, PORT))
        print("Connected to the Bulletin Board.")

        username = input("Enter your username: ")
        response = send_command(client, {"command": "connect", "username": username})
        if response.get("status") == "error":
            print(response.get("message"))
            return

        while True:
            display_menu()
            choice = input("Select an option: ")

            if choice == "1":
                subject = input("Enter message subject: ")
                body = input("Enter message body: ")
                response = send_command(client, {"command": "post", "subject": subject, "body": body})

            elif choice == "2":
                response = send_command(client, {"command": "users"})

            elif choice == "3":
                message_id = int(input("Enter message ID: "))
                response = send_command(client, {"command": "message", "id": message_id})

            elif choice == "4":
                response = send_command(client, {"command": "leave"})
                print(response.get("message"))
                break

            elif choice == "5":
                response = send_command(client, {"command": "groups"})

            elif choice == "6":
                group_name = input("Enter group name: ")
                response = send_command(client, {"command": "groupjoin", "group": group_name})

            elif choice == "7":
                group_name = input("Enter group name: ")
                subject = input("Enter message subject: ")
                body = input("Enter message body: ")
                response = send_command(client, {"command": "grouppost", "group": group_name, "subject": subject, "body": body})

            elif choice == "0":
                print("Exiting...")
                break
            else:
                print("Invalid option.")

            print("Server Response:", response)


if __name__ == "__main__":
    client_program()
