import socket
import threading
import tkinter as tk
from tkinter import scrolledtext


SERVER_HOST = '127.0.0.1'
SERVER_PORT = 12345

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_HOST, SERVER_PORT))


root = tk.Tk()
root.title("TCP Chat Client")

chat_window = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', width=50, height=20, bg='lightgray')
chat_window.pack(padx=10, pady=10)

entry = tk.Entry(root, width=40, font=('Arial', 12))
entry.pack(side=tk.LEFT, padx=(10, 0), pady=(0, 10))

def send_message():
    msg = entry.get()
    if msg:
        client.send(msg.encode('utf-8'))
        entry.delete(0, tk.END)

def receive_messages():
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            chat_window.configure(state='normal')
            chat_window.insert(tk.END, message + "\n")
            chat_window.configure(state='disabled')
        except:
            break

send_button = tk.Button(root, text="Відправити", command=send_message)
send_button.pack(side=tk.LEFT, padx=(5, 10), pady=(0, 10))


receive_thread = threading.Thread(target=receive_messages)
receive_thread.daemon = True
receive_thread.start()

root.mainloop()

