import logging
from abc import ABC

from core.network.local_network import NetworkInfo
from core.storage.storage_of_temp import StorageOfTemp
from core.utils.ciphersuites import CipherSuites
from core.user.user import User
from core.data.node_info import NodeInfo

logger = logging.getLogger("main")


class Node(ABC):
    def __init__(self, user: User, server_url, storage_of_temp: StorageOfTemp):
        self.user = user
        user_pk = user.getUserPKString()
        self.__node_id = user_pk[0:16]
        self.node_ip = NetworkInfo.get_network_ip()
        self.nodeInfo = NodeInfo(self.__node_id, user_pk, self.node_ip, server_url)
        self.nodeInfo.nodeSignature = self.generateNodeSignature()
        logger.info("节点初始化完成")
        logger.info("节点ID:" + self.__node_id)
        logger.info("节点签名:" + self.nodeInfo.nodeSignature)
        storage_of_temp.setNodeInfo(self.nodeInfo)

    # 生成节点签名
    def generateNodeSignature(self):
        node_signature = self.user.sign(str(self.nodeInfo.getInfo()).encode("utf-8"))
        return node_signature

    # 对指定信息生成签名
    def sign(self, message):
        signature = self.user.sign(message)
        return signature

    def getNodeId(self):
        return self.__node_id

    def getNodeInfo(self):
        return self.nodeInfo.getInfo()

    def getNodeSignature(self):
        return self.nodeInfo.nodeSignature

    # 验证签名
    def verifySignature(self, signature, message):
        message = str(message).encode("utf-8")
        return CipherSuites.verify(self.user.getUserPKString(), signature, message)
