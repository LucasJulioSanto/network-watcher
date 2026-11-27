import json
import os
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
DEVICES_PATH = os.path.join(base_dir, "data", "known_devices.json")


def load_devices():
    try:
        with open(DEVICES_PATH, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {}


def save_devices(devices):
    os.makedirs(os.path.dirname(DEVICES_PATH), exist_ok=True)
    with open(DEVICES_PATH, 'w', encoding="utf-8") as file:
        json.dump(devices, file, indent=4)


def update_devices(known, scanned):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_macs = []

    for device in scanned:
        mac = device["mac"]

        if mac in known:
            # This are devices that we have seen before in previous scans
            known[mac]["last_seen"] = now
            known[mac]["last_ip"] = device["ip"]
            known[mac]["hostname"] = device["hostname"]
        else:
            # This are new devices that either have been added to out network or that havent been scanned yet
            known[mac] = {
                "nickname": "",
                "vendor": device["vendor"],
                "hostname": device["hostname"],
                "last_ip": device["ip"],
                "first_seen": now,
                "last_seen": now,
            }
            new_macs.append(mac)

    return known, new_macs


def trust_device(mac, nickname):
    known = load_devices()
    if mac not in known:
        print("Device not found")
    else:
        known[mac]["nickname"] = nickname
        save_devices(known)
        print(f"{mac} | {nickname}")
    





if __name__ == "__main__":
    import identify
    import discover

    my_ip, my_network = discover.ip_range()
    oui_db = identify.load_oui()
    arp_text = identify.get_arp()
    scanned = identify.parse_arp(arp_text, oui_db, my_ip)

    known = load_devices()
    known, new_macs = update_devices(known, scanned)
    save_devices(known)

    print(f"Saved {len(known)} devices to known_devices.json")
    if new_macs:
        print(f"{len(new_macs)} NEW DEVICE(S) DETECTED")
        
        for new in new_macs:
            info = known[new]
            print(f"{new} | {info['last_ip']} | {info['vendor']} | {info['hostname']}")
    else:
        print("No new Devices")



