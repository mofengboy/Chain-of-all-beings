from abc import ABC
from core.utils.system_time import STime
from core.utils.ciphersuites import CipherSuites


class Block(ABC):
    def __init__(self, e, block_type, user_pk):
        self.__header = {
            "blockID": CipherSuites.generateBlockID(e, block_type, user_pk),  # 区块ID
            "timestamp": STime.getTimestamp(),
            "epoch": e,
            "prevBlock": [],  # 上一个区块的哈希值列表
            "prevBlockHeader": [],  # 上一个区块的头部哈希值列表
            "userPK": [],  # 生成该区块的用户公钥
            "bodySignature": [],  # 签名,第一个是简单节点用户的签名，第二个是主节点用户的签名，若只有一个，则为主节点用户的签名
            "bodyEncoding": "utf-8",  # 内容编码方式
            "blockType": block_type
        }
        # 存储的内容
        self.body = None

    def setElectionPeriod(self, election_period):
        self.__header["electionPeriod"] = election_period

    # 获取区块ID
    def getBlockID(self):
        return self.__header["blockID"]

    def getEpoch(self):
        return self.__header["epoch"]

    def getUserPk(self):
        return self.__header["userPK"]

    def getPrevBlock(self):
        return self.__header["prevBlock"]

    def getPrevBlockHeader(self):
        return self.__header["prevBlockHeader"]

    # 获取区块头
    def getBlockHeader(self):
        return self.__header

    # 仅获取区块头部哈希值
    def getBlockHeaderSHA256(self):
        header = self.__header.copy()
        header["prevBlock"] = []
        return CipherSuites.generateSHA256(str(header).encode("utf-8")).hexdigest()

    # 获取区块哈希值
    def getBlockSHA256(self):
        content = str(self.__header).encode("utf-8") + str(self.body).encode("utf-8")
        return CipherSuites.generateSHA256(content).hexdigest()

    def setPrevBlock(self, prevBlock):
        self.__header["prevBlock"] = prevBlock

    def setPrevBlockHeader(self, prevBlockHeader):
        self.__header["prevBlockHeader"] = prevBlockHeader

    def setUserPK(self, userPK):
        self.__header["userPK"] = userPK

    def setBodySignature(self, bodySignature):
        self.__header["bodySignature"] = bodySignature

    def setBodyEncoding(self, bodyEncoding):
        self.__header["bodyEncoding"] = bodyEncoding

    def getBodySignature(self):
        return self.__header["bodySignature"]

    # 用于从数据库直接读入数据的情况
    def setHeader(self, header):
        self.__header = header
