import requests

from core.config.node_seed import main_node_site


class MainNodeIp:
    def __init__(self):
        self.ipList = []
        self.getMainNodeIp()

    def getMainNodeIp(self):
        for site in main_node_site:
            try:
                res = requests.get(site)
                self.ipList = res.json()
            except Exception as err:
                print(err)

    def getTpList(self):
        return self.ipList


if __name__ == "__main__":
    MainNodeIp()
