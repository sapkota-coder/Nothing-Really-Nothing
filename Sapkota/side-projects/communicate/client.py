import socket
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel, Label, Button
import os
import wave
import pyaudio
import tempfile
import time
from PIL import Image, ImageTk, ImageGrab
import cv2
import numpy as np
import struct

# --- Configuration ---
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "chat")
SERVER_IP = '192.168.1.4'  # replace with your server IP
PORT = 12345
BUFFER_SIZE = 4096
VIDEO_FPS = 15
SCREEN_FPS = 5

class ClientApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Global Chat (Dark Mode)")
        self.geometry("850x650")
        self.configure(bg="#222")
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)

        # Socket connection
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((SERVER_IP, PORT))
        except Exception as e:
            messagebox.showerror("Connection Error", f"Cannot connect: {e}")
            self.destroy()
            return

        # State flags
        self.username = None
        self.recording = False
        self.video_streaming = False
        self.screen_streaming = False

        # Build UI
        self.build_login()
        self.build_chat()

        # Start listener
        threading.Thread(target=self.listen_thread, daemon=True).start()

    def build_login(self):
        self.login_frame = tk.Frame(self, bg="#222")
        self.login_frame.pack(pady=20)
        tk.Label(self.login_frame, text="Username", fg="white", bg="#222").pack()
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack()
        tk.Label(self.login_frame, text="Password", fg="white", bg="#222").pack()
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.pack()
        tk.Button(self.login_frame, text="Login", command=self.try_login).pack(pady=10)

    def build_chat(self):
        self.chat_frame = tk.Frame(self, bg="#222")
        # start hidden until login
        self.chat_log = tk.Text(self.chat_frame, state='disabled', bg="#333", fg="white")
        self.chat_log.pack(expand=True, fill='both')

        self.msg_entry = tk.Entry(self.chat_frame, bg="#444", fg="white")
        self.msg_entry.pack(fill='x', pady=5)
        self.msg_entry.bind("<Return>", self.send_msg)

        btn_frame = tk.Frame(self.chat_frame, bg="#222")
        btn_frame.pack(pady=5)
        Button(btn_frame, text="Send", command=self.send_msg).grid(row=0, column=0, padx=5)
        Button(btn_frame, text="File", command=lambda: self.offer_transfer('FILE')).grid(row=0, column=1)
        Button(btn_frame, text="Folder", command=lambda: self.offer_transfer('FOLDER')).grid(row=0, column=2)
        Button(btn_frame, text="Start Voice", command=self.start_voice).grid(row=0, column=3)
        Button(btn_frame, text="Stop Voice", command=self.stop_voice).grid(row=0, column=4)
        Button(btn_frame, text="Start Video", command=self.request_video).grid(row=0, column=5)
        Button(btn_frame, text="Stop Video", command=self.stop_video).grid(row=0, column=6)
        Button(btn_frame, text="Request Screen", command=self.request_screen).grid(row=0, column=7)
        Button(btn_frame, text="Stop Screen", command=self.stop_screen).grid(row=0, column=8)

        self.online_flag = tk.Canvas(self, width=20, height=20, bg="#222", highlightthickness=0)
        self.online_flag.place(x=810, y=10)
        self.flag = self.online_flag.create_oval(2, 2, 18, 18, fill="red")

    def try_login(self):
        user = self.username_entry.get().strip()
        pwd = self.password_entry.get().strip()
        if not user or not pwd:
            messagebox.showwarning("Input error", "Please enter username and password")
            return
        # send login
        self.sock.send(f"LOGIN::{user}::{pwd}".encode())
        resp = self.sock.recv(1024).decode()
        if resp.startswith("MSG::Server::") and "joined" in resp:
            self.username = user
            self.login_frame.pack_forget()
            self.chat_frame.pack(expand=True, fill='both')
            self.set_online(True)
            self.add_msg(f"Logged in as {user}")
        else:
            messagebox.showerror("Login Failed", resp)

    def set_online(self, online):
        color = "green" if online else "red"
        self.online_flag.itemconfig(self.flag, fill=color)

    def add_msg(self, msg):
        self.chat_log.config(state='normal')
        self.chat_log.insert('end', msg + "\n")
        self.chat_log.see('end')
        self.chat_log.config(state='disabled')

    def send_msg(self, event=None):
        text = self.msg_entry.get().strip()
        if text:
            self.sock.send(f"MSG::{self.username}::{text}".encode())
            self.add_msg(f"You: {text}")
            self.msg_entry.delete(0, 'end')

    def offer_transfer(self, typ):
        path = filedialog.askopenfilename() if typ == 'FILE' else filedialog.askdirectory()
        if not path:
            return
        name = os.path.basename(path)
        size = os.path.getsize(path)
        # request
        self.sock.send(f"{typ}_REQ::{name}::{size}".encode())
        resp = self.sock.recv(1024).decode()
        if resp != f"{typ}_ACCEPT":
            self.add_msg(f"{typ} transfer denied")
            return
        # send data
        self.sock.send(b"READY")
        with open(path, 'rb') as f:
            while chunk := f.read(BUFFER_SIZE):
                self.sock.sendall(chunk)
        self.add_msg(f"Sent {typ.lower()}: {name}")

    def start_voice(self):
        # request voice
        self.sock.send(b"VOICE_REQ")
        resp = self.sock.recv(1024)
        if resp != b"VOICE_ACCEPT":
            self.add_msg("Voice denied")
            return
        # record
        self.recording = True
        threading.Thread(target=self._voice_thread, daemon=True).start()

    def stop_voice(self):
        self.recording = False

    def _voice_thread(self):
        self.add_msg("Recording voice...")
        CH, fmt, ch, rate = 1024, pyaudio.paInt16, 1, 44100
        p = pyaudio.PyAudio()
        stream = p.open(format=fmt, channels=ch, rate=rate, input=True, frames_per_buffer=CH)
        frames = []
        while self.recording:
            frames.append(stream.read(CH))
        stream.stop_stream(); stream.close(); p.terminate()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        wf = wave.open(tmp.name, 'wb')
        wf.setnchannels(ch); wf.setsampwidth(p.get_sample_size(fmt)); wf.setframerate(rate)
        wf.writeframes(b''.join(frames)); wf.close()
        self.add_msg("Sending voice...")
        # send as file
        self.sock.send(f"VOICE_DATA::{os.path.basename(tmp.name)}::{os.path.getsize(tmp.name)}".encode())
        self.sock.recv(1024)
        with open(tmp.name, 'rb') as f:
            while chunk := f.read(BUFFER_SIZE):
                self.sock.sendall(chunk)
        os.unlink(tmp.name)

    def request_video(self):
        self.sock.send(b"VIDEO_REQ")
        resp = self.sock.recv(1024)
        if resp != b"VIDEO_ACCEPT":
            self.add_msg("Video denied")
            return
        self.video_streaming = True
        threading.Thread(target=self._video_thread, daemon=True).start()

    def stop_video(self):
        self.video_streaming = False

    def _video_thread(self):
        cap = cv2.VideoCapture(0)
        self.sock.send(b"VIDEO_START")
        while self.video_streaming:
            ret, frame = cap.read()
            if not ret: break
            data = cv2.imencode('.jpg', frame)[1].tobytes()
            self.sock.send(struct.pack('!I', len(data)) + data)
            time.sleep(1/VIDEO_FPS)
        cap.release()
        self.sock.send(b"VIDEO_END")

    def request_screen(self):
        self.sock.send(b"SCREEN_REQ")
        resp = self.sock.recv(1024)
        if resp != b"SCREEN_ACCEPT":
            self.add_msg("Screen denied")
            return
        self.screen_streaming = True
        threading.Thread(target=self._screen_thread, daemon=True).start()

    def stop_screen(self):
        self.screen_streaming = False

    def _screen_thread(self):
        self.sock.send(b"SCREEN_START")
        while self.screen_streaming:
            img = ImageGrab.grab()
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)
            data = cv2.imencode('.jpg', frame)[1].tobytes()
            self.sock.send(struct.pack('!I', len(data)) + data)
            time.sleep(1/SCREEN_FPS)
        self.sock.send(b"SCREEN_END")

    def listen_thread(self):
        while True:
            data = self.sock.recv(BUFFER_SIZE)
            if not data:
                break
            # text message
            if data.startswith(b"MSG::"):
                self.add_msg(data.decode()[5:])
            # file/folder request
            elif data.startswith(b"FILE_REQ::") or data.startswith(b"FOLDER_REQ::"):
                typ, name, size = data.decode().split("::")
                size = int(size)
                allow = messagebox.askyesno(f"{typ} Request", f"Accept {name} ({size} bytes)?")
                self.sock.send(f"{typ}_ACCEPT".encode() if allow else f"{typ}_DENY".encode())
                if allow:
                    self.sock.recv(1024)  # READY
                    path = os.path.join(DOWNLOAD_DIR, name)
                    with open(path, 'wb') as f:
                        rec = 0
                        while rec < size:
                            chunk = self.sock.recv(min(BUFFER_SIZE, size-rec))
                            rec += len(chunk)
                            f.write(chunk)
                    self.add_msg(f"Received {typ.lower()}: {name}")
                    self.preview(path)
            # voice request
            elif data == b"VOICE_REQ":
                allow = messagebox.askyesno("Voice Request", "Accept voice message?")
                self.sock.send(b"VOICE_ACCEPT" if allow else b"VOICE_DENY")
                if allow:
                    header = self.sock.recv(BUFFER_SIZE).decode()
                    _, name, size = header.split("::")
                    size = int(size)
                    self.sock.send(b"READY")
                    path = os.path.join(DOWNLOAD_DIR, name)
                    with open(path, 'wb') as f:
                        rec = 0
                        while rec < size:
                            chunk = self.sock.recv(min(BUFFER_SIZE, size-rec))
                            rec += len(chunk)
                            f.write(chunk)
                    self.add_msg("Received voice message")
                    self.play_audio(path)
            # video request
            elif data == b"VIDEO_REQ":
                allow = messagebox.askyesno("Video Request", "Accept video stream?")
                self.sock.send(b"VIDEO_ACCEPT" if allow else b"VIDEO_DENY")
                if allow:
                    self.add_msg("Incoming video...")
                    threading.Thread(target=self._receive_video, daemon=True).start()
            # screen request
            elif data == b"SCREEN_REQ":
                allow = messagebox.askyesno("Screen Request", "Accept screen share?")
                self.sock.send(b"SCREEN_ACCEPT" if allow else b"SCREEN_DENY")
                if allow:
                    self.add_msg("Incoming screen...")
                    threading.Thread(target=self._receive_screen, daemon=True).start()

    def preview(self, path):
        ext = os.path.splitext(path)[1].lower()
        try:
            if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
                win = Toplevel(self)
                img = Image.open(path)
                img.thumbnail((300,300))
                tkimg = ImageTk.PhotoImage(img)
                lbl = Label(win, image=tkimg)
                lbl.image = tkimg
                lbl.pack()
            elif ext == '.wav':
                threading.Thread(target=self.play_audio, args=(path,), daemon=True).start()
        except Exception as e:
            self.add_msg(f"Preview error: {e}")

    def play_audio(self, path):
        CHUNK = 1024
        wf = wave.open(path, 'rb')
        p = pyaudio.PyAudio()
        stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        output=True)
        data = wf.readframes(CHUNK)
        while data:
            stream.write(data)
            data = wf.readframes(CHUNK)
        stream.stop_stream(); stream.close(); p.terminate()

    def _receive_video(self):
        # implement receive video logic here
        pass

    def _receive_screen(self):
        # implement receive screen logic here
        pass

if __name__ == '__main__':
    app = ClientApp()
    app.mainloop()
