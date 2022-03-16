import socket
import requests


class NetworkInfo:
    @staticmethod
    def get_local_network_ip():
        """get the local network ip, not loopback 127.*"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('1.1.1.1', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    # 获取外网IP
    @staticmethod
    def get_network_ip():
        try:
            ip = requests.get('https://ifconfig.me/ip', timeout=1).text.strip()
            return ip
        except Exception as err:
            ip = requests.get('http://ifconfig.me/ip', timeout=1).text.strip()
            return ip


if __name__ == "__main__":
    print(NetworkInfo.get_network_ip())

