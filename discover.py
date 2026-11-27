import socket
import time
import ipaddress
import subprocess


def ip_range():
    # Finding the ip of the local machine
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)

    # Finding the network range it belongs too
    prefix = 24 # known limitation
    net = ipaddress.ip_network(f"{ip_address}/{prefix}", strict=False)

    return ip_address, net


def is_alive(ip):
    # Finds out if pings are alive
    result = subprocess.run(["ping", "-n", "1", "-w", "500", str(ip)], capture_output=True, text=True)
    # Checks to see if it has reponded
    return "TTL=" in result.stdout

def sweep(net):
    ips = []
    for host in net.hosts():
        if is_alive(host):
            ips.append(host)
        print(host)
    return ips






if __name__ == "__main__":
    my_ip, my_network = ip_range()
    print(f"Local IP: {my_ip}")
    print(f"Network: {my_network}")
    print(is_alive("192.168.1.250"))
    print(is_alive("192.168.1.254"))
    start = time.perf_counter()
    live_hosts = sweep(my_network)
    end = time.perf_counter()

    print(f"Live hosts: {live_hosts}")
    print(f"Found {len(live_hosts)} devices in {end - start:.1f} seconds")
