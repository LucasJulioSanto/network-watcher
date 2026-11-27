import subprocess
import re
import socket
import csv
import os

MAC_PATTERN = re.compile(r"[0-9a-f]{2}(-[0-9a-f]{2}){5}")

def get_arp():
    # Finds the interface and its IP, MAC Addresses, and Types
    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
    # Returning the Raw ARP table as text
    return result.stdout


def parse_arp(arp_text, oui_db, my_ip):
    devices = []
    in_my_section = False

    for arp in arp_text.splitlines():

        if arp.startswith("Interface:"):
            in_my_section = my_ip in arp
            continue

        if not in_my_section:
            continue

        if "dynamic" in arp:
            parts = arp.split()

            if len(parts) != 3 or not MAC_PATTERN.fullmatch(parts[1]):
                continue

            devices.append({
                "ip": parts[0], 
                "mac": parts[1], 
                "hostname": get_hostname(parts[0]), 
                "vendor": get_vendor(parts[1], oui_db),
            })

    return devices

def get_hostname(ip):
    try: 
        hostname = socket.gethostbyaddr(ip)
        return hostname[0]
    except socket.herror:
        return "Unknown"

def load_oui():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    oui_path = os.path.join(base_dir, "data", "oui.csv")

    oui_db = {}

    with open(oui_path, newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)

        for row in reader:
            oui = row[1].strip()
            company = row[2].strip()
            oui_db[oui] = company

    return oui_db

def get_vendor(mac, oui_db):
    # We are changing the format of our mac addresses so that it matches our oui.csv files
    prefix = mac.replace("-","").upper()[:6]
    # This is looking it up and if it doesnt know then it will return "Unknown"
    return oui_db.get(prefix, "Unknown")

if __name__ == "__main__":
    import discover

    my_ip, my_network = discover.ip_range()
    oui_db = load_oui()
    arp_text = get_arp()
    devices = parse_arp(arp_text, oui_db, my_ip)
    for device in devices:
        print(device["ip"], device["mac"], device["hostname"], device["vendor"])
    