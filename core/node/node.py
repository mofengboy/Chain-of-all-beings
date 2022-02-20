import logging
from abc import ABC

from core.network.local_network import NetworkInfo
from core.utils.ciphersuites import CipherSuites
from core.user.user import User
from core.data.node_info import NodeInfo

logger = logging.getLogger("main")


class Node(ABC):
    def __init__(self, user: User):
        self.user = user
        user_pk = user.getUserPKString()
        self.__node_id = user_pk[0:16]
        self.node_ip = NetworkInfo.get_network_ip()
        self.nodeInfo = NodeInfo(self.__node_id, user_pk, self.node_ip)
        self.nodeInfo.nodeSignature = self.generateNodeSignature()
        logger.info("节点初始化完成")
        logger.info("节点ID:" + self.__node_id)
        logger.info("节点签名:" + self.nodeInfo.nodeSignature)

    # 生成节点签名
    def generateNodeSignature(self):
        node_signature = self.user.sign(str(self.nodeInfo.getInfo()).encode("utf-8"))
        return node_signature

    # 对指定信息生成签名
    def sign(self, message):
        signature = self.user.sign(message)
        return signature

    # # 验证节点签名
    # def verifyNodeSignature(self, node_info: NodeInfo):
    #     return self.verifySignature(node_info.nodeSignature, node_info.getInfo())

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
