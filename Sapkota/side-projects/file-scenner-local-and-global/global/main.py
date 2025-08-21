import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import threading
import socket
import os

PORT = 65432
BUFFER_SIZE = 4096

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 Peer-to-Peer File Search & Transfer")
        self.root.geometry("800x600")
        self.root.configure(bg="#2e3f4f")

        label_fg = "#e0e0e0"
        entry_bg = "#1c2b36"
        btn_bg = "#4a90e2"
        btn_fg = "white"
        list_bg = "#16222a"
        list_fg = "#a0c4ff"
        preview_bg = "#0f1820"
        preview_fg = "#cfd8dc"

        tk.Label(root, text="Peer IP:", fg=label_fg, bg=root["bg"]).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ip_entry = tk.Entry(root, bg=entry_bg, fg=label_fg)
        self.ip_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        tk.Button(root, text="Test Conn", bg=btn_bg, fg=btn_fg, command=self.test_connection).grid(row=0, column=2, padx=10)

        tk.Label(root, text="Filename:", fg=label_fg, bg=root["bg"]).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.filename_entry = tk.Entry(root, bg=entry_bg, fg=label_fg)
        self.filename_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        tk.Button(root, text="Search 🔍", bg=btn_bg, fg=btn_fg, command=self.search_files).grid(row=1, column=2, padx=10)

        tk.Label(root, text="Remote Path:", fg=label_fg, bg=root["bg"]).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.path_entry = tk.Entry(root, bg=entry_bg, fg=label_fg)
        self.path_entry.insert(0, os.getcwd())
        self.path_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        tk.Button(root, text="Send File 📤", bg="#7ab317", fg=btn_fg, command=self.send_request).grid(row=2, column=2, padx=10)

        self.result_listbox = tk.Listbox(root, bg=list_bg, fg=list_fg, selectbackground="#89CFF0")
        self.result_listbox.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)
        self.result_listbox.bind("<Double-Button-1>", self.preview_remote_file)

        self.preview_text = scrolledtext.ScrolledText(root, bg=preview_bg, fg=preview_fg, state="disabled")
        self.preview_text.grid(row=4, column=0, columnspan=3, sticky="nsew", padx=10, pady=5)

        self.status_label = tk.Label(root, text="Status: Waiting...", fg=label_fg, bg=root["bg"])
        self.status_label.grid(row=5, column=0, columnspan=3, sticky="w", padx=10)

        root.grid_columnconfigure(1, weight=1)
        root.grid_rowconfigure(3, weight=1)
        root.grid_rowconfigure(4, weight=1)

        self.files_found = []
        threading.Thread(target=self.start_server, daemon=True).start()

    def log_status(self, msg):
        self.status_label.config(text=f"Status: {msg}")

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.bind(("", PORT))
            srv.listen()
            self.log_status(f"Listening on port {PORT}")
            while True:
                conn, addr = srv.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

    def handle_client(self, conn, addr):
        with conn:
            try:
                cmd = conn.recv(1024).decode()
                if cmd == "HELLO":
                    conn.sendall("ACK".encode())
                    return
                if cmd == "REQ_SEARCH":
                    fn = conn.recv(1024).decode()
                    rp = conn.recv(1024).decode()
                    allow = messagebox.askyesno("Search Request",
                        f"{addr[0]} wants to search '{fn}' in:\n{rp}\nAllow?")
                    conn.sendall(("ACCEPT" if allow else "DENY").encode())
                    if not allow: return
                    matches = []
                    if os.path.isdir(rp):
                        for rd, _, files in os.walk(rp):
                            for f in files:
                                if fn.lower() == "all" or fn.lower() in f.lower():
                                    p = os.path.join(rd, f)
                                    matches.append(f"{p}|{os.path.getsize(p)}")
                    resp = "\n".join(matches) if matches else "NOFILES"
                    conn.sendall(resp.encode())
                    idx = conn.recv(1024).decode()
                    if idx.isdigit():
                        i = int(idx) - 1
                        if 0 <= i < len(matches):
                            path = matches[i].split("|")[0]
                            with open(path, "rb") as F:
                                data = F.read(BUFFER_SIZE)
                                while data:
                                    conn.sendall(data)
                                    data = F.read(BUFFER_SIZE)
                if cmd == "REQ_SEND":
                    name = conn.recv(1024).decode()
                    size = int(conn.recv(1024).decode())
                    allow = messagebox.askyesno("Send Request",
                        f"{addr[0]} wants to send:\n{name} ({size} bytes)\nAllow?")
                    conn.sendall(("ACCEPT" if allow else "DENY").encode())
                    if not allow: return
                    save = os.path.join(os.getcwd(), name)
                    with open(save, "wb") as F:
                        rec = 0
                        while rec < size:
                            chunk = conn.recv(min(BUFFER_SIZE, size-rec))
                            if not chunk: break
                            F.write(chunk)
                            rec += len(chunk)
                    messagebox.showinfo("Received", f"Saved {name}")
            except:
                pass

    def test_connection(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showwarning("Input Error", "Enter IP")
            return
        try:
            with socket.socket() as s:
                s.connect((ip, PORT))
                s.sendall("HELLO".encode())
                if s.recv(1024).decode() == "ACK":
                    messagebox.showinfo("Connected", f"{ip} online")
                    self.log_status("Handshake OK")
                else:
                    raise
        except:
            messagebox.showerror("Failed", "No ACK")
            self.log_status("Handshake failed")

    def search_files(self):
        ip = self.ip_entry.get().strip()
        fn = self.filename_entry.get().strip()
        rp = self.path_entry.get().strip()
        if not ip or not fn or not rp:
            messagebox.showwarning("Input Error", "Fill all fields")
            return
        threading.Thread(target=self._search, args=(ip, fn, rp), daemon=True).start()

    def _search(self, ip, fn, rp):
        try:
            with socket.socket() as s:
                s.connect((ip, PORT))
                s.sendall("REQ_SEARCH".encode())
                s.sendall(fn.encode())
                s.sendall(rp.encode())
                resp = s.recv(4096).decode()
                if resp == "DENY":
                    messagebox.showinfo("Denied", "Request denied")
                    return
                if resp == "NOFILES":
                    messagebox.showinfo("No Files", "No matches")
                    return
                self.files_found = resp.split("\n")
                self.result_listbox.delete(0, tk.END)
                for i, line in enumerate(self.files_found, 1):
                    p, sz = line.split("|")
                    self.result_listbox.insert(tk.END, f"{i}. {os.path.basename(p)} {(int(sz)/1024):.2f} KB")
                choice = simpledialog.askinteger("Download", "Number to download?")
                if not choice: return
                s.sendall(str(choice).encode())
                save = os.path.basename(self.files_found[choice-1].split("|")[0])
                with open(save, "wb") as F:
                    data = s.recv(BUFFER_SIZE)
                    while data:
                        F.write(data)
                        data = s.recv(BUFFER_SIZE)
                messagebox.showinfo("Downloaded", f"Saved {save}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_status("Search failed")

    def send_request(self):
        ip = self.ip_entry.get().strip()
        path = self.filename_entry.get().strip()
        if not ip or not os.path.isfile(path):
            messagebox.showwarning("Error", "Enter IP & valid file")
            return
        threading.Thread(target=self._send, args=(ip, path), daemon=True).start()

    def _send(self, ip, path):
        try:
            name = os.path.basename(path)
            size = os.path.getsize(path)
            with socket.socket() as s:
                s.connect((ip, PORT))
                s.sendall("REQ_SEND".encode())
                s.sendall(name.encode())
                s.sendall(str(size).encode())
                resp = s.recv(1024).decode()
                if resp == "DENY":
                    messagebox.showinfo("Denied", "Peer declined")
                    return
                with open(path, "rb") as F:
                    data = F.read(BUFFER_SIZE)
                    while data:
                        s.sendall(data)
                        data = F.read(BUFFER_SIZE)
                messagebox.showinfo("Sent", f"{name} sent")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.log_status("Send failed")

    def preview_remote_file(self, event):
        idx = self.result_listbox.curselection()
        if not idx:
            return
        p, sz = self.files_found[idx[0]].split("|")
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", f"{p}\n{int(sz)} bytes")
        self.preview_text.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchApp(root)
    root.mainloop()
