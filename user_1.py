import socket
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import time
from ttkthemes import ThemedTk
import sys

seq_num = 1
received_messages = set()
unacknowledged_messages = {}
def receive_messages(sock):
    global received_messages
    while True:
        data, addr = sock.recvfrom(1024)
        decoded = data.decode()
        if decoded.startswith("ACK:"):
            seq = decoded.split(': ', 1)[1]
            if int(seq) in unacknowledged_messages:  # Check if the key exists before deleting
                del unacknowledged_messages[int(seq)]
        else:
            seq, message = decoded.split(':', 1)
            if seq not in received_messages:
                received_messages.add(seq)
                chatbox.insert(tk.END, "**Received message: " + message + '\n')
            # Send an acknowledgement for the received message
            msg = "ACK: " + seq
            sock.sendto(msg.encode(), ('localhost', 12347))
            sys.stderr.write("Sent acknowledgement for message {}\n".format(seq))

def send_message(sock):
    global seq_num
    message = str(seq_num) + ':' + entry.get()
    entry.delete(0, 'end')
    
    sock.sendto(message.encode(), ('localhost', 12347))
    chatbox.insert(tk.END, "*Sent message: " + message + '\n')
    sys.stderr.write("Sent message {}\n".format(seq_num))
    
    # Store the message in the unacknowledged_messages dictionary
    unacknowledged_messages[seq_num] = seq_num,message
    
    seq_num += 1

# Function to check for unacknowledged messages and resend them
def check_acknowledgements(sock):
    while True:
        for seq, message in list(unacknowledged_messages.items()):
            if seq not in received_messages:
                sock.sendto((str(seq) + ':' + str(message)).encode(), ('localhost', 12347))
                chatbox.insert(tk.END, "*Resent message: " + str(message) + '\n')
                sys.stderr.write("Resent message {}\n".format(seq))
        time.sleep(3)  # Check for unacknowledged messages every second

# Function to receive a file
def receive_file():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 12341))
    server_socket.listen(1)

    while True:
        client_socket, addr = server_socket.accept()
        file_name_length_bytes = client_socket.recv(4)
    
        file_name_length = int.from_bytes(file_name_length_bytes, byteorder='big')

        file_name = client_socket.recv(file_name_length).decode()  # Receive the file name
        chatbox.insert(tk.END, "Receiving file: " + file_name + '\n')
        with open(file_name, 'wb') as f:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break
                f.write(data)
        chatbox.insert(tk.END, "File received: " + file_name + '\n')

# Function to send a file
def send_file():
    file_path = filedialog.askopenfilename()
    file_name = file_path.split('/')[-1]  # Get the file name from the file path
    chatbox.insert(tk.END, "Sending file: " + file_name + '\n')
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 12349))
    chatbox.insert(tk.END, "TCP connection opened..." + '\n')
     # Send the length of the file name first
    file_name_length = len(file_name)
    client_socket.sendall(file_name_length.to_bytes(4, byteorder='big'))

    # Send the file name
    client_socket.sendall(file_name.encode())

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            client_socket.send(data)

    client_socket.close()
    chatbox.insert(tk.END, "File sent: " + file_name + '\n')
    chatbox.insert(tk.END, "TCP connection closed..." + '\n')


sock1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock1.bind(('localhost', 12346))

threading.Thread(target=receive_messages, args=(sock1,)).start()
threading.Thread(target=check_acknowledgements, args=(sock1,)).start()
threading.Thread(target=receive_file).start()

root = ThemedTk(theme="arc") 
root.title("Chat App | User 1")

frame = ttk.Frame(root)
frame.pack()

chatbox = tk.Text(frame, width=100, height=30)
chatbox.pack(pady=10)

entry = ttk.Entry(root)
entry.bind("<Return>", lambda event: send_message(sock1))
entry.pack(ipadx=100, padx=10)

send_button = ttk.Button(root, text="Send", command=lambda: send_message(sock1))
send_button.pack(pady=5)

send_file_button = ttk.Button(root, text="Send File", command=send_file)
send_file_button.pack()

root.mainloop()
