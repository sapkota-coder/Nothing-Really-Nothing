import os
import shutil

def list_dir(path):
    try:
        entries = os.listdir(path)
        if entries:
            print(f"Listing {len(entries)} entries in {path}:")
            for entry in entries:
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    print(f"[Folder] {entry}")
                else:
                    print(f"[File] {entry}")
        else:
            print("No files or folders found.")
    except Exception as e:
        print(f"Error reading directory: {e}")

def preview_file(path):
    if not os.path.isfile(path):
        print("Not a file.")
        return
    ext = os.path.splitext(path)[1].lower()
    if ext in [".txt", ".py", ".md", ".log"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(1000)
                print("\n--- File Preview (first 1000 chars) ---")
                print(content)
                print("--- End Preview ---\n")
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print("No preview available for this file type.")

def mkdir_cmd(path):
    try:
        os.makedirs(path, exist_ok=False)
        print(f"Directory created: {path}")
    except FileExistsError:
        print("Directory already exists.")
    except Exception as e:
        print(f"Error creating directory: {e}")

def mkfile_cmd(path):
    if os.path.exists(path):
        print("File or directory already exists.")
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("")
        print(f"File created: {path}")
    except Exception as e:
        print(f"Error creating file: {e}")

def rm_r_cmd(path):
    if not os.path.exists(path):
        print("File or directory does not exist.")
        return
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Directory removed: {path}")
        else:
            os.remove(path)
            print(f"File removed: {path}")
    except Exception as e:
        print(f"Error removing file/directory: {e}")

def pwd_cmd(path):
    print("Current working directory:", path)

def search_cmd(base_path, query):
    print(f"Searching for '{query}' under '{base_path}' ...")
    matches = []
    for root, dirs, files in os.walk(base_path):
        for d in dirs:
            if query.lower() in d.lower():
                matches.append(("Folder", d, os.path.join(root, d)))
        for f in files:
            if query.lower() in f.lower():
                matches.append(("File", f, os.path.join(root, f)))
    if matches:
        for typ, name, path in matches:
            print(f"[{typ}] {name} -> {path}")
    else:
        print("No matches found.")

def main():
    print("CLI File Manager with Bash Commands")
    current_path = os.path.expanduser("~")
    print(f"Starting in directory: {current_path}")
    print("Type 'help' for available commands.\n")

    while True:
        try:
            cmd = input(f"{current_path} > ").strip()
            if not cmd:
                continue
            if cmd.lower() in ["exit", "quit"]:
                print("Bye!")
                break
            elif cmd.lower() == "help":
                print("""
Commands:
  ls                   : list files and folders
  cd <path>            : change directory
  pwd                  : print current directory
  preview <filename>   : preview text file content
  mkdir <dir_name>     : create directory
  mkfile <file_name>   : create empty file
  rm -r <path>         : remove file or directory recursively
  search <query>       : search files/folders by name
  help                 : show this help text
  exit or quit         : exit program
""")
            elif cmd == "ls":
                list_dir(current_path)
            elif cmd.startswith("cd "):
                path = cmd[3:].strip()
                new_path = os.path.abspath(os.path.join(current_path, path))
                if os.path.isdir(new_path):
                    current_path = new_path
                else:
                    print("Directory does not exist.")
            elif cmd == "pwd":
                pwd_cmd(current_path)
            elif cmd.startswith("preview "):
                name = cmd[8:].strip()
                path = os.path.join(current_path, name)
                if os.path.exists(path):
                    preview_file(path)
                else:
                    print("File not found.")
            elif cmd.startswith("mkdir "):
                dirname = cmd[6:].strip()
                path = os.path.join(current_path, dirname)
                mkdir_cmd(path)
            elif cmd.startswith("mkfile "):
                filename = cmd[7:].strip()
                path = os.path.join(current_path, filename)
                mkfile_cmd(path)
            elif cmd.startswith("rm -r "):
                path_arg = cmd[6:].strip()
                path = os.path.join(current_path, path_arg)
                rm_r_cmd(path)
            elif cmd.startswith("search "):
                parts = cmd.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: search <query>")
                    continue
                query = parts[1]
                search_cmd(current_path, query)
            else:
                print("Unknown command. Type 'help' for commands.")
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
