# Network Watcher
 
> A Python tool that discovers devices on my home network, remembers them, scans for exposed services, and alerts me when an unknown device joins.
 
<!-- Add a short demo GIF or screenshot here once main.py is finished, e.g. ![Demo](docs/demo.gif) -->
 
![Python](https://img.shields.io/badge/python-3.11-blue) ![Platform](https://img.shields.io/badge/platform-Windows-lightgrey) ![Status](https://img.shields.io/badge/status-in%20progress-yellow)
 
---
 
## Why I Built This
 
I wanted to know exactly what is connected to my home network at any moment — and to be told when something new shows up. Unknown devices on a network are one of the first things a security team looks for, so I built my own monitoring tool from scratch using only Python's standard library, to understand how device discovery actually works under the hood instead of relying on tools like Nmap.
 
---
 
## Features
 
- [X] Detects my local IP and network range
- [X] Discovers live hosts on the subnet
- [X] Identifies devices by MAC address, hostname, and vendor
- [X] Remembers known devices between scans
- [X] Flags new / unknown devices
- [ ] Scans devices for common open ports
- [ ] Sends alerts and runs on a schedule
---
 
## How It Works
 
1. **Find the network** — detects the computer's local IP and works out the subnet range (e.g. `192.168.1.0/24`).
2. **Sweep hosts** — pings every usable address in the range and keeps the ones that reply with a real echo reply (checked by looking for `TTL=` in the output, since Windows returns exit code `0` even for "Destination host unreachable").
3. **Identify devices** — reads the system's ARP table to get each device's MAC address, then looks up its hostname (reverse DNS) and its manufacturer (from the IEEE OUI list).
4. **Compare to known** — loads previously seen devices from a JSON file (keyed by MAC address), updates the ones it has seen before, and adds the new ones.
5. **Alert** — prints a warning for every device that has never been seen before.
```
[ Find network ] → [ Sweep hosts ] → [ Identify devices ] → [ Compare to known ] → [ Port scan ] → [ Alert ]
```
 
---
 
## Tech Stack
 
- **Language:** Python 3.11
- **Libraries:** standard library only — `socket`, `ipaddress`, `subprocess`, `re`, `csv`, `json`, `os`, `datetime`, `time`
- **Data source:** IEEE OUI list (`oui.csv`) for vendor lookups
- **Platform tested on:** Windows 11
---
 
## Installation
 
```bash
git clone https://github.com/LucasJulioSanto/network-watcher.git
cd network-watcher
python -m venv venv
venv\Scripts\Activate.ps1      # Windows PowerShell
```
 
**Download the vendor list (one time):**
 
1. Download the IEEE OUI list from `https://standards-oui.ieee.org/oui/oui.csv`
2. Create a `data/` folder in the project and save the file as `data/oui.csv`
The `data/` folder is in `.gitignore`, so your own device list never gets uploaded.
 
> **Note:** turn off any VPN before scanning — a VPN changes which IP the tool detects and can block access to your local network.
 
---
 
## Usage
 
```bash
python discover.py    # find the network and sweep for live hosts
python identify.py    # list devices with IP, MAC, hostname, and vendor
python storage.py     # scan, save devices, and flag any new ones
```
 
| Command | What it does |
|---------|--------------|
| `python discover.py` | Detects the local network and pings every address to find live hosts |
| `python identify.py` | Reads the ARP table and shows each device's IP, MAC, hostname, and vendor |
| `python storage.py` | Updates `data/known_devices.json` and warns about devices never seen before |
| `python main.py <command>` | *(in progress)* Single entry point with `scan`, `list`, and `trust` commands |
 
**Example output** (addresses and names changed):
 
```
Saved 13 devices to known_devices.json
2 NEW DEVICE(S) DETECTED
aa-bb-cc-11-22-33 | 192.168.1.108 | Example Vendor Inc. | Smart_Clock.lan
aa-bb-cc-44-55-66 | 192.168.1.166 | Example Network Co. | Unknown
```
 
---
 
## Project Structure
 
```
network-watcher/
├── data/                  # not uploaded (.gitignore)
│   ├── oui.csv            # IEEE vendor list (download yourself)
│   └── known_devices.json # created automatically on first scan
├── __init__.py
├── discover.py            # find network range + ping sweep
├── identify.py            # ARP table parsing, hostnames, vendor lookup
├── storage.py             # save/load devices, flag new ones, nicknames
├── main.py                # command-line entry point (in progress)
├── .gitignore
└── README.md
```
 
---
 
## Build Log
 
### Milestone 1 — Find My Network
- **Goal:** Detect my computer's local IP and the network range it belongs to.
- **What I learned:** Private vs. public IPs (RFC 1918), subnet masks and CIDR notation (`/24` = `255.255.255.0`), the `ipaddress` module, the difference between `print` and `return`, how a function returns multiple values, and why `if __name__ == "__main__":` stops code from running on import.
- **Problems I hit & how I solved them:** My function printed the network instead of returning it, so other code got `None` — fixed by returning the values and printing them outside the function. I also learned that `socket.gethostbyname()` can pick the wrong network adapter (WSL, VPN), which came back to bite me in Milestone 4.
### Milestone 2 — Ping Sweep
- **Goal:** Ping every address on the network and collect the ones that reply.
- **What I learned:** How ICMP ping works, running OS commands from Python with `subprocess.run()`, capturing output, how `PATH` lets programs like `ping` be found, and looping over `ip_network.hosts()`.
- **Problems I hit & how I solved them:** My router was at `.254`, not `.1`. On Windows, "Destination host unreachable" still returns exit code `0`, so the return code couldn't tell live and dead hosts apart — I switched to checking the output for `TTL=` (not just `TTL`, because "TTL expired in transit" is a failure message). The full sweep took **122.5 seconds** for 254 addresses, which will be my "before" number when I add threading.
### Milestone 3 — MAC Addresses & Hostnames
- **Goal:** Find out *what* each device is — its MAC address, hostname, and manufacturer.
- **What I learned:** What ARP is and why the ping sweep fills the ARP table, parsing command output with `.splitlines()` and `.split()`, storing devices as a list of dictionaries, reverse DNS with `socket.gethostbyaddr()`, `try`/`except`, variable scope, reading a CSV into a dictionary, and how the first half of a MAC (the OUI) identifies the manufacturer.
- **Problems I hit & how I solved them:** A function with no `return` gave back `None` and crashed my loop. `gethostbyaddr()` throws an error for devices with no name, so I caught it and returned `"Unknown"`. My MACs (`84-a3-29-...`) didn't match the OUI file format (`84A329`), so I normalized them with `.replace()`, `.upper()`, and slicing. I also found that iPhones use randomized "private" MACs, so they can't be matched to a vendor.
### Milestone 4 — Remembering Devices
- **Goal:** Save every device to a JSON file so the tool remembers what it has seen between scans.
- **What I learned:** Reading and writing JSON, building file paths with `os.path` so the script works from any folder, `os.makedirs(exist_ok=True)`, keying devices by MAC instead of IP (because DHCP can change IPs), timestamps with `datetime`, and input validation with a regex.
- **Problems I hit & how I solved them:** My parser accepted hundreds of fake devices where the word `dynamic` was read as a MAC — lines from other network interfaces (WSL/Hyper-V) had no MAC column. I fixed it by validating each MAC with a regex and only reading the ARP section for my own interface. Later, the scan found **0 devices** — my VPN was on, so the tool detected the VPN's IP (`10.2.0.2`) instead of my Ethernet IP. Turning off the VPN fixed it.
### Milestone 5 — Flagging New Devices
- **Goal:** Warn me about devices that have never been seen before, and let me give known devices a nickname.
- **What I learned:** Returning two values (the updated devices and a list of new MACs), using an empty list as `False` in an `if`, early returns, and looking up details by dictionary key.
- **Problems I hit & how I solved them:** My first version appended the device's details instead of its MAC, so the alert couldn't say *which* device was new. On the first real run it flagged 3 devices — one turned out to have been on my network all along but was offline during my first scan. That taught me that "new to the tool" is not the same as "new to the network."
### Milestone 6 — Port Scanning
- **Goal:** Check each device for common open ports to see what services it exposes.
- **What I learned:** *Not started yet.*
- **Problems I hit & how I solved them:** *Not started yet.*
### Milestone 7 — Alerts & Scheduling
- **Goal:** Get notified automatically and run scans on a schedule.
- **What I learned:** *Not started yet.*
- **Problems I hit & how I solved them:** *Not started yet.*
---
 
## Limitations
 
- **Windows only for now** — the `ping` flags and `arp -a` parsing are written for Windows output.
- **Some devices ignore ping**, so the sweep can miss them (the ARP table often catches them anyway).
- **The ping sweep is slow** (~2 minutes for a `/24`) because it checks one address at a time.
- **Randomized MAC addresses** (iPhones, iPads, Apple Watch) can't be matched to a vendor, and can show up as "new" again if the device rotates its MAC.
- **Generic hostnames** — phones report names like `iPhone-4.lan`, not the name set on the device, so nicknames have to be set manually.
- **A VPN or virtual adapter (WSL/Hyper-V)** can make the tool detect the wrong IP and find no devices.
- **The network size is assumed to be `/24`** rather than read from the system.
- **"New" means new to the tool** — a device that was offline during earlier scans will be flagged when it first appears.
- **My own computer isn't listed**, because a computer doesn't keep itself in its own ARP table.
---
 
## Security & Ethics
 
This tool is intended **only** for networks I own or have explicit permission to scan. Scanning networks without authorization may violate acceptable-use policies or the law.
 
The `data/` folder (my device list and the OUI file) is excluded with `.gitignore`, and all example output in this README uses fake MAC addresses and changed names, so no real details about my home network are published.
 
---
 
## Future Improvements
 
- Speed up the ping sweep with `ThreadPoolExecutor` (target: a few seconds instead of ~2 minutes)
- `main.py` command-line interface with `scan`, `list`, and `trust` commands
- Show nicknames instead of hostnames in output once a device is trusted
- Port scanning of common services (Milestone 6)
- Desktop/email alerts and scheduled scans with Windows Task Scheduler (Milestone 7)
- Keep a history of alerts in a log file
- Try mDNS/Bonjour discovery to get better device names
- Read the real subnet mask instead of assuming `/24`
- Cross-platform support for macOS and Linux
---
 
## What I Learned
 
- Testing assumptions against real output matters — the Windows ping exit code looked right but was lying.
- Never trust input you didn't create: validating the ARP output stopped hundreds of fake "devices."
- Your environment can break working code — a VPN silently changed the detected IP and made the scan return nothing.
- Small functions that each do one job (get, parse, look up, save) are much easier to test and debug.
- Privacy features like MAC randomization make network monitoring harder — and show why defenders need more than one way to identify a device.
---
 
## Author
 
**Julio** — BCIT Computer Information Technology
GitHub: [@LucasJulioSanto](https://github.com/LucasJulioSanto)
 