import socket


class NetworkInfo:
    @staticmethod
    def get_network_ip():
        """get the local network ip, not loopback 127.*"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('1.1.1.1', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    # 获取外网IP
    @staticmethod
    def getExtranetIP():
        pass


if __name__ == "__main__":
    NetworkInfo.get_network_ip()
