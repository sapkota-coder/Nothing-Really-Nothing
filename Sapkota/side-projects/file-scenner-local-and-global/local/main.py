import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from file_types import FILE_TYPES

class FileScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local File Scanner")
        self.root.geometry("700x500")
        self.root.config(bg="#1e1e2f")
        
        self.stop_scanning = threading.Event()
        self.files = []
        
        self.create_widgets()
        
        # Set default directory to C:\
        default_dir = "C:\\"
        if os.path.isdir(default_dir):
            self.dir_entry.insert(0, default_dir)
        
    def create_widgets(self):
        # Directory input
        tk.Label(self.root, text="Directory:", bg="#1e1e2f", fg="white").place(x=10, y=10)
        self.dir_entry = tk.Entry(self.root, width=50, bg="#2e2e3e", fg="white", insertbackground="white")
        self.dir_entry.place(x=80, y=10)
        self.dir_entry.bind("<Return>", lambda e: self.start_scan())
        
        browse_btn = tk.Button(self.root, text="Browse", command=self.browse_directory, bg="#3e3e5e", fg="white")
        browse_btn.place(x=540, y=6)
        
        # Search input
        tk.Label(self.root, text="Search:", bg="#1e1e2f", fg="white").place(x=10, y=40)
        self.search_entry = tk.Entry(self.root, width=30, bg="#2e2e3e", fg="white", insertbackground="white")
        self.search_entry.place(x=80, y=40)
        self.search_entry.bind("<Return>", lambda e: self.start_scan())
        
        # File type filter dropdown
        tk.Label(self.root, text="Filter:", bg="#1e1e2f", fg="white").place(x=350, y=40)
        self.filter_var = tk.StringVar(value="All")  # Default "All"
        self.filter_dropdown = ttk.Combobox(
            self.root, 
            textvariable=self.filter_var, 
            values=list(FILE_TYPES.keys()), 
            state="readonly", width=15
        )
        self.filter_dropdown.place(x=400, y=40)
        self.filter_dropdown.bind("<<ComboboxSelected>>", lambda e: self.start_scan())
        
        # Tooltip placeholder (implement separately if needed)
        # self.filter_dropdown_tip = CreateToolTip(self.filter_dropdown, "Select file type filter")
        
        # Buttons
        self.scan_btn = tk.Button(self.root, text="Start Scan", command=self.start_scan, bg="#4caf50", fg="white")
        self.scan_btn.place(x=580, y=40)
        
        self.stop_btn = tk.Button(self.root, text="Stop Scan", command=self.stop_scan, bg="#f44336", fg="white")
        self.stop_btn.place(x=580, y=75)
        self.stop_btn.config(state="disabled")
        
        # Result listbox with scrollbar
        self.result_listbox = tk.Listbox(self.root, bg="#2e2e3e", fg="white", width=80, height=18, font=("Courier New", 10))
        self.result_listbox.place(x=10, y=110)
        self.result_listbox.bind("<Double-Button-1>", self.preview_file)
        
        scrollbar = tk.Scrollbar(self.root, command=self.result_listbox.yview)
        scrollbar.place(x=665, y=110, height=290)
        self.result_listbox.config(yscrollcommand=scrollbar.set)
        
        # Preview text box
        tk.Label(self.root, text="File Preview:", bg="#1e1e2f", fg="white").place(x=10, y=410)
        self.preview_text = scrolledtext.ScrolledText(self.root, bg="#2e2e3e", fg="white", width=90, height=5)
        self.preview_text.place(x=10, y=430)
        self.preview_text.config(state="disabled")
        
        # Animation label
        self.anim_label = tk.Label(self.root, text="", bg="#1e1e2f", fg="white")
        self.anim_label.place(x=600, y=10)
        self.anim_running = False
        
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
        
    def start_scan(self):
        directory = self.dir_entry.get().strip()
        if not os.path.isdir(directory):
            messagebox.showerror("Error", "Invalid directory")
            return
        self.search_term = self.search_entry.get().strip().lower()
        self.filter_key = self.filter_var.get()
        self.stop_scanning.clear()
        self.result_listbox.delete(0, tk.END)
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.config(state="disabled")
        
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.anim_running = True
        threading.Thread(target=self.animate, daemon=True).start()
        
        threading.Thread(target=self.scan_files, args=(directory,), daemon=True).start()
        
    def stop_scan(self):
        self.stop_scanning.set()
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.anim_running = False
        self.anim_label.config(text="")
        
    def scan_files(self, directory):
        filter_exts = FILE_TYPES.get(self.filter_key)
        try:
            all_items = os.listdir(directory)
        except Exception as e:
            self.show_error(f"Cannot list directory: {e}")
            self.stop_scan()
            return
        
        self.files = []
        
        # Insert header with fixed width columns
        header = f"{'Index'.ljust(6)}|{'Size (KB)'.ljust(12)}| Path"
        self.result_listbox.insert(tk.END, header)
        self.result_listbox.insert(tk.END, "-" * 75)
        
        index = 1
        for item in all_items:
            if self.stop_scanning.is_set():
                break
            
            full_path = os.path.join(directory, item)
            if os.path.isfile(full_path):
                ext = os.path.splitext(item)[1].lower()
                if (filter_exts is None or ext in filter_exts):
                    if self.search_term == "all" or self.search_term == "" or self.search_term in item.lower():
                        try:
                            size = os.path.getsize(full_path)
                            size_kb = size / 1024
                        except:
                            size_kb = 0
                        # Format string with fixed widths for columns
                        display_text = f"{str(index).ljust(6)}|{f'{size_kb:.2f}'.ljust(12)}| {item}"
                        self.files.append(full_path)
                        self.result_listbox.insert(tk.END, display_text)
                        index += 1
        
        if not self.files and not self.stop_scanning.is_set():
            self.result_listbox.insert(tk.END, "No files found.")
        self.stop_scan()
        
    def preview_file(self, event):
        selection = self.result_listbox.curselection()
        if not selection:
            return
        index = selection[0] - 2  # Adjust for header and separator lines
        if index < 0 or index >= len(self.files):
            return
        filepath = self.files[index]
        try:
            ext = os.path.splitext(filepath)[1].lower()
            # Preview only text-based files (txt, py, bat, etc.)
            text_exts = ['.txt', '.py', '.bat', '.log', '.csv', '.json', '.md']
            if ext in text_exts:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read(10000)  # preview up to 10k chars
                self.preview_text.config(state="normal")
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert(tk.END, content)
                self.preview_text.config(state="disabled")
            else:
                self.preview_text.config(state="normal")
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert(tk.END, f"Preview not available for '{ext}' files.")
                self.preview_text.config(state="disabled")
        except Exception as e:
            self.preview_text.config(state="normal")
            self.preview_text.delete("1.0", tk.END)
            self.preview_text.insert(tk.END, f"Error reading file: {e}")
            self.preview_text.config(state="disabled")
            
    def animate(self):
        animation = ["|", "/", "-", "\\"]
        idx = 0
        while self.anim_running:
            self.anim_label.config(text=animation[idx])
            idx = (idx + 1) % len(animation)
            # sleep in main thread not good, so use after method
            self.root.after(150)
    
    def show_error(self, msg):
        messagebox.showerror("Error", msg)


if __name__ == "__main__":
    root = tk.Tk()
    app = FileScannerApp(root)
    root.mainloop()
