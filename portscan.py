import socket


COMMON_PORTS = {
    22: "SSH",
    80: "HTTP",
    443: "HTTPS",
    21: "FTP",
    23: "Telnet",
    53: "DNS",
    139: "Windows file sharing",
    445: "Windows file sharing",
    3389: "Remote Desktop",
    554: "RTSP",
    8080: "Alternate HTTP",
    9100: "Printers",
}

def is_port_open(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.settimeout(0.5)
        result = client_socket.connect_ex((ip, port))
        return result == 0



if __name__ == "__main__":
    print(is_port_open("192.168.1.254", 80))      # router: probably True
    print(is_port_open("192.168.1.254", 12345))   # random port: probably False