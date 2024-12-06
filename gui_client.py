import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading

# Configuration
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 404

class InteractiveGUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Interactive Bulletin Board GUI")
        self.window.geometry("800x600")
        self.window.configure(bg="#222831")

        # Socket
        self.client_socket = None
        self.is_connected = False

        # Main Frame
        self.main_frame = tk.Frame(self.window, bg="#222831")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Command Feedback Section
        self.command_feedback_label = tk.Label(self.main_frame, text="Command Feedback", bg="#222831", fg="#EEEEEE", font=("Helvetica", 14, "bold"))
        self.command_feedback_label.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 5))

        self.command_feedback_area = scrolledtext.ScrolledText(self.main_frame, state='disabled', wrap=tk.WORD, bg="#393E46", fg="#EEEEEE", font=("Helvetica", 12), width=40)
        self.command_feedback_area.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=(0, 5))

        # Chat Display Section
        self.chat_label = tk.Label(self.main_frame, text="Chat Area", bg="#222831", fg="#EEEEEE", font=("Helvetica", 14, "bold"))
        self.chat_label.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(0, 5))

        self.chat_display = scrolledtext.ScrolledText(self.main_frame, state='disabled', wrap=tk.WORD, bg="#393E46", fg="#EEEEEE", font=("Helvetica", 12), width=60)
        self.chat_display.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=(0, 5))

        # Configure column and row weights for resizing
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=2)
        self.main_frame.rowconfigure(1, weight=1)

        # Message Input
        self.message_input = tk.Entry(self.window, bg="#00ADB5", fg="#EEEEEE", font=("Helvetica", 12))
        self.message_input.pack(fill=tk.X, padx=10, pady=(0, 10))
        self.message_input.bind("<Return>", self.send_message)

        # Buttons
        self.button_frame = tk.Frame(self.window, bg="#222831")
        self.button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.connect_button = tk.Button(self.button_frame, text="Connect", bg="#00ADB5", fg="#EEEEEE", font=("Helvetica", 12), command=self.connect_to_server)
        self.connect_button.pack(side=tk.LEFT, padx=5)

        self.disconnect_button = tk.Button(self.button_frame, text="Disconnect", bg="#F05454", fg="#EEEEEE", font=("Helvetica", 12), command=self.disconnect_from_server)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.quit_button = tk.Button(self.button_frame, text="Quit", bg="#393E46", fg="#EEEEEE", font=("Helvetica", 12), command=self.quit_application)
        self.quit_button.pack(side=tk.RIGHT, padx=5)

        self.display_feedback("Please Connect to the Server!")


    def connect_to_server(self):
        """Connect to the server."""
        if self.is_connected:
            self.display_feedback("Already connected to the server.")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((SERVER_ADDRESS, SERVER_PORT))
            self.is_connected = True
            self.display_feedback("Connected to the server.")
            threading.Thread(target=self.receive_messages, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Connection Error", f"Unable to connect: {e}")

    def disconnect_from_server(self):
        """Disconnect from the server."""
        if not self.is_connected:
            self.display_feedback("Not connected to the server.")
            return

        try:
            self.client_socket.sendall("!quit".encode())
            self.client_socket.close()
        except:
            pass
        self.is_connected = False
        self.display_feedback("Disconnected from the server.")

    def send_message(self, event=None):
        """Send a message to the server."""
        if not self.is_connected:
            self.display_feedback("Connect to the server first.")
            return

        msg = self.message_input.get().strip()
        if not msg:
            self.display_feedback("Cannot send an empty message.")
            return

        try:
            self.client_socket.sendall(msg.encode())
            self.display_feedback(f"Command sent: {msg}")
            self.message_input.delete(0, tk.END)
        except Exception as e:
            self.display_feedback(f"Error sending message: {e}")

    def receive_messages(self):
        """Continuously listen for messages from the server."""
        while self.is_connected:
            try:
                server_msg = self.client_socket.recv(1024).decode()
                if not server_msg:
                    break
                self.display_chat_message(server_msg)
            except Exception as e:
                self.display_feedback(f"Connection error: {e}")
                break
        self.disconnect_from_server()

    def display_chat_message(self, message):
        """Display a message in the chat area."""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, message + "\n")
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def display_feedback(self, feedback):
        """Display feedback or error messages in the command feedback area."""
        self.command_feedback_area.config(state='normal')
        self.command_feedback_area.insert(tk.END, feedback + "\n")
        self.command_feedback_area.config(state='disabled')
        self.command_feedback_area.see(tk.END)

    def quit_application(self):
        """Close the application."""
        self.disconnect_from_server()
        self.window.quit()

    def run(self):
        """Run the GUI application."""
        self.window.mainloop()


if __name__ == "__main__":
    app = InteractiveGUI()
    app.run()
