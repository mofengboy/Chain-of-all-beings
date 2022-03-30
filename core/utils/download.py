import logging
import requests

from core.utils.serialization import SerializationAssetOfBeings


class RemoteChainAsset:
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


if __name__ == "__main__":
    a = RemoteChainAsset().getEpochListOfBeingsChain(url="https://server.beings.icu", offset=0, count=8)
    print(a)
