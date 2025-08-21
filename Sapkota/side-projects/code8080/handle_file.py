import os
import json
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading

class file_handling:

    @staticmethod
    def folder_show(all=False, path=False, format=False, type='json',
                    path_dir=None, show=False, save=False):
        # Use current working directory if path_dir is None or "current"
        if path_dir is None or path_dir == "current":
            dir_path = os.getcwd()
        else:
            dir_path = os.path.abspath(path_dir)  # folder to read from

        try:
            items = os.listdir(dir_path)
        except FileNotFoundError:
            error_msg = {"error": f"Directory not found: {dir_path}"}
            if show:
                print(error_msg)
            return error_msg

        if not all:
            items = [item for item in items if os.path.isfile(os.path.join(dir_path, item))]

        files_list = []
        for item in items:
            item_path = os.path.join(dir_path, item)
            entry = {"name": item}
            if path:
                entry["path"] = item_path
            files_list.append(entry)

        data = {
            "pwd": dir_path,
            "files": files_list
        }

        if format and type.lower() == 'json':
            output = json.dumps(data, indent=4)
            if save:
                # Save JSON file in current working directory (not dir_path)
                save_path = os.path.join(os.getcwd(), 'my_data.json')
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                if show:
                    print(f"JSON saved at: {save_path}")
            if show:
                print(output)
            return output
        else:
            if show:
                print(data)
            return data
class local_host_publish:
    @staticmethod
    def publish(publish=False, port=8000):
        if not publish:
            print("Publishing is disabled. Set publish=True to start the server.")
            return
        
        # Get LAN IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable, just for getting IP
            s.connect(('10.255.255.255', 1))
            lan_ip = s.getsockname()[0]
        except Exception:
            lan_ip = '127.0.0.1'
        finally:
            s.close()
        
        server_address = (lan_ip, port)
        
        httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
        
        print(f"Serving HTTP on LAN IP: http://{lan_ip}:{port}/")
        print("Press Ctrl+C to stop.")
        
        # Run server in a separate thread so it doesn't block
        def run_server():
            httpd.serve_forever()
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        # Keep main thread alive until user interrupts
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("\nStopping server...")
            httpd.shutdown()
            thread.join()
            print("Server stopped.")
