import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from file_types import FILE_TYPES
import time

# For PDF preview
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

class FileScannerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local File Scanner")
        self.root.geometry("700x500")
        self.root.config(bg="#1e1e2f")
        
        self.stop_scanning = threading.Event()
        self.files = []  # list of tuples (filepath, category)
        
        self.create_widgets()
        
        # Remove directory input, so use fixed scan directory
        self.scan_directory = "C:\\"  # change this as you want
        # Show it somewhere in title or anim label:
        self.anim_label.config(text=f"Scanning: {self.scan_directory}")
        
    def create_widgets(self):
        # Remove directory input and browse button, keep search and filter
        
        # Search input
        tk.Label(self.root, text="Search:", bg="#1e1e2f", fg="white").place(x=10, y=10)
        self.search_entry = tk.Entry(self.root, width=30, bg="#2e2e3e", fg="white", insertbackground="white")
        self.search_entry.place(x=80, y=10)
        self.search_entry.bind("<Return>", lambda e: self.start_scan())
        
        # File type filter dropdown
        tk.Label(self.root, text="Filter:", bg="#1e1e2f", fg="white").place(x=350, y=10)
        self.filter_var = tk.StringVar(value="All")  # Default "All"
        self.filter_dropdown = ttk.Combobox(
            self.root, 
            textvariable=self.filter_var, 
            values=list(FILE_TYPES.keys()), 
            state="readonly", width=15
        )
        self.filter_dropdown.place(x=400, y=10)
        self.filter_dropdown.bind("<<ComboboxSelected>>", lambda e: self.start_scan())
        
        # Buttons
        self.scan_btn = tk.Button(self.root, text="Start Scan", command=self.start_scan, bg="#4caf50", fg="white")
        self.scan_btn.place(x=580, y=10)
        
        self.stop_btn = tk.Button(self.root, text="Stop Scan", command=self.stop_scan, bg="#f44336", fg="white")
        self.stop_btn.place(x=580, y=45)
        self.stop_btn.config(state="disabled")
        
        # Result listbox with scrollbar
        self.result_listbox = tk.Listbox(self.root, bg="#2e2e3e", fg="white", width=80, height=22, font=("Courier New", 10))
        self.result_listbox.place(x=10, y=75)
        self.result_listbox.bind("<Double-Button-1>", self.preview_file)
        
        scrollbar = tk.Scrollbar(self.root, command=self.result_listbox.yview)
        scrollbar.place(x=665, y=75, height=360)
        self.result_listbox.config(yscrollcommand=scrollbar.set)
        
        # Preview text box
        tk.Label(self.root, text="File Preview:", bg="#1e1e2f", fg="white").place(x=10, y=440)
        self.preview_text = scrolledtext.ScrolledText(self.root, bg="#2e2e3e", fg="white", width=90, height=6)
        self.preview_text.place(x=10, y=460)
        self.preview_text.config(state="disabled")
        
        # Animation label (used to show scanning directory)
        self.anim_label = tk.Label(self.root, text="", bg="#1e1e2f", fg="white")
        self.anim_label.place(x=10, y=40)
        self.anim_running = False
        
    def start_scan(self):
        self.stop_scanning.clear()
        self.result_listbox.delete(0, tk.END)
        self.preview_text.config(state="normal")
        self.preview_text.delete("1.0", tk.END)
        self.preview_text.config(state="disabled")
        
        self.scan_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.anim_running = True
        
        self.anim_label.config(text=f"Scanning: {self.scan_directory}")
        
        threading.Thread(target=self.animate, daemon=True).start()
        threading.Thread(target=self.scan_files, args=(self.scan_directory,), daemon=True).start()
        
    def stop_scan(self):
        self.stop_scanning.set()
        self.scan_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.anim_running = False
        self.anim_label.config(text="")
        
    def is_at_bottom(self):
        total = self.result_listbox.size()
        if total == 0:
            return True
        last_visible = self.result_listbox.nearest(self.result_listbox.winfo_height())
        return last_visible >= total - 1

    def insert_result(self, text):
        at_bottom = self.is_at_bottom()
        self.result_listbox.insert(tk.END, text)
        if at_bottom:
            self.result_listbox.see(tk.END)
        self.result_listbox.update_idletasks()
        
    def scan_files(self, directory):
        filter_exts = FILE_TYPES.get(self.filter_var.get())
        search_str = self.search_entry.get().strip().lower()
        
        self.files.clear()
        
        # We will collect files by categories
        pdf_files = []
        image_files = []
        other_files = []
        
        # Define image extensions (can expand as needed)
        image_exts = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
        
        # Recursive scan
        for root_dir, dirs, files in os.walk(directory):
            if self.stop_scanning.is_set():
                break
            folder_name = os.path.basename(root_dir) or root_dir
            self.insert_result(f"------------- {folder_name} -------------")
            
            for fname in files:
                if self.stop_scanning.is_set():
                    break
                ext = os.path.splitext(fname)[1].lower()
                if (filter_exts is None or ext in filter_exts):
                    if search_str == "all" or search_str == "" or search_str in fname.lower():
                        full_path = os.path.join(root_dir, fname)
                        try:
                            size_kb = os.path.getsize(full_path) / 1024
                        except:
                            size_kb = 0
                        display_text = f"{fname.ljust(40)} {size_kb:8.2f} KB"
                        
                        if ext == ".pdf":
                            pdf_files.append((display_text, full_path))
                        elif ext in image_exts:
                            image_files.append((display_text, full_path))
                        else:
                            other_files.append((display_text, full_path))
            
            self.insert_result("_" * 65)
            time.sleep(0.01)
        
        def display_group(title, files):
            self.insert_result(f"------------- {title} -------------")
            if files:
                for text, path in files:
                    if self.stop_scanning.is_set():
                        break
                    self.files.append(path)
                    self.insert_result(text)
                    time.sleep(0.02)
            else:
                self.insert_result("No files found in this category.")
            self.insert_result("_" * 65)
        
        # Show grouped results
        if not self.stop_scanning.is_set():
            display_group("PDF Files", pdf_files)
            display_group("Image Files", image_files)
            display_group("Other Files", other_files)
        
        if not self.files and not self.stop_scanning.is_set():
            self.insert_result("No files found.")
        
        self.stop_scan()
        
    def preview_file(self, event):
        selection = self.result_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        
        # Map index to file in self.files by skipping header/separator lines
        # We'll do a simple linear scan here because headers break list continuity
        
        line = self.result_listbox.get(index)
        # If line is a header or separator, ignore preview
        if line.startswith("-------------") or set(line.strip()) == {"_"}:
            return
        
        # Find file path by matching displayed text
        # The file lines have format: "filename padded size KB"
        # So just find the first file with matching text (could be improved)
        try:
            file_path = None
            for fpath in self.files:
                fname = os.path.basename(fpath)
                size_kb = os.path.getsize(fpath) / 1024
                display_text = f"{fname.ljust(40)} {size_kb:8.2f} KB"
                if display_text == line:
                    file_path = fpath
                    break
            if not file_path:
                return
        except Exception:
            return
        
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".pdf" and PyPDF2 is not None:
                # Extract text from first page for preview
                with open(file_path, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    if reader.pages:
                        page = reader.pages[0]
                        content = page.extract_text() or "(No text extracted)"
                    else:
                        content = "(No pages)"
                self.preview_text.config(state="normal")
                self.preview_text.delete("1.0", tk.END)
                self.preview_text.insert(tk.END, content[:10000])  # limit preview size
                self.preview_text.config(state="disabled")
            else:
                # For text files
                text_exts = ['.txt', '.py', '.bat', '.log', '.csv', '.json', '.md']
                if ext in text_exts:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(10000)
                    self.preview_text.config(state="normal")
                    self.preview_text.delete("1.0", tk.END)
                    self.preview_text.insert(tk.END, content)
                    self.preview_text.config(state="disabled")
                else:
                    self.preview_text.config(state="normal")
                    self.preview_text.delete("1.0", tk.END)
                    self.preview_text.insert(tk.END, f"No preview available for '{ext}' files.")
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
            self.anim_label.config(text=f"Scanning: {self.scan_directory} {animation[idx]}")
            idx = (idx + 1) % len(animation)
            time.sleep(0.15)
    
    def show_error(self, msg):
        messagebox.showerror("Error", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileScannerApp(root)
    root.mainloop()
