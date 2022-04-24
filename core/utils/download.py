import logging
import requests

from core.data.network_message import NetworkMessage, NetworkMessageType
from core.network.net import Client
from core.utils.serialization import SerializationAssetOfBeings, SerializationNetworkMessage, SerializationAssetOfTimes


class RemoteChainAsset:
    @staticmethod
    def getCurrentEpoch(getEpoch, client: Client, ip) -> int:
        try:
            serial_data = SerializationNetworkMessage.serialization(
                NetworkMessage(NetworkMessageType.Get_Current_Epoch, message=None))
            res = client.sendMessageByIP(ip=ip, data=str(serial_data).encode("utf-8"))
            epoch = int(res)
            return epoch - getEpoch()
        except Exception as err:
            logging.warning(err)
            return 0

    @staticmethod
    def getEpochListOfBeingsChain(url, offset, count):
        try:
            r = requests.get(url + "/chain/beings/epoch_list?offset=" + str(offset) + "&count=" + str(count))
            if r.json()["is_success"]:
                epoch_list = r.json()["data"]
                return epoch_list
            else:
                logging.warning(r.json()["data"])
                return "500"
        except Exception as err:
            logging.warning(err)
            return "500"

    # 获取其他主节点的众生区块
    @staticmethod
    def getChainOfBeings(url, epoch: int):
        try:
            r = requests.get(url + "/static/beings_" + str(epoch) + ".chain", timeout=1)
            if r.headers.get('content-type') == "application/octet-stream":
                return SerializationAssetOfBeings.deserialization(r.content)
            else:
                return "500"
        except Exception as err:
            logging.warning(err)
            return "500"

    # 获取其他主节点的时代区块
    @staticmethod
    def getChainOfTimes(url, election_period: int):
        try:
            r = requests.get(url + "/static/times_" + str(election_period) + ".chain", timeout=1)
            status_code = r.json()["data"]
            if status_code == "404":
                return "404"
            if r.headers.get('content-type') == "application/octet-stream":
                return SerializationAssetOfTimes.deserialization(r.content)
            else:
                return "500"
        except Exception as err:
            logging.warning(err)
            return "500"

    # 获取其他主节点的垃圾区块
    @staticmethod
    def getChainOfGarbage(url, election_period: int):
        try:
            r = requests.get(url + "/static/garbage_" + str(election_period) + ".chain", timeout=1)
            status_code = r.json()["data"]
            if status_code == "404":
                return "404"
            if r.headers.get('content-type') == "application/octet-stream":
                return SerializationAssetOfTimes.deserialization(r.content)
            else:
                return "500"
        except Exception as err:
            logging.warning(err)
            return "500"


if __name__ == "__main__":
    a = RemoteChainAsset().getChainOfTimes(url="https://server.beings.icu", election_period=10)
    print(a)
