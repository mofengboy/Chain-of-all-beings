import logging

import requests

from core.data.block_of_beings import BlockListOfBeings
from core.utils.serialization import SerializationAssetOfBeings


class RemoteChainAsset:
    # 获取其他主节点的众生区块
    @staticmethod
    def getChainOfBeings(url, epoch: int) -> BlockListOfBeings:
        try:
            r = requests.get(url + "static/beings_" + str(epoch) + ".chain", timeout=1)
            if r.headers.get('content-type') == "application/octet-stream":
                return SerializationAssetOfBeings.deserialization(r.content)
            else:
                return "404"
        except Exception as err:
            logging.warning(err)
            return "404"


if __name__ == "__main__":
    a = RemoteChainAsset().getChainOfBeings(url="http://192.168.1.116:5000/", epoch=1)
    print(a)
