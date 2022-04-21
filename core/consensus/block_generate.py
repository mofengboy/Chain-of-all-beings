import logging
import random

from core.data.block_of_garbage import BodyOfGarbageBlock, BlockOfGarbage
from core.data.node_info import MainNodeList, NodeInfo
from core.data.block_of_beings import BlockOfBeings
from core.data.block_of_times import BlockOfTimes, BodyOfTimesBlock
from core.utils.ciphersuites import CipherSuites

logger = logging.getLogger("main")


# 计算本次生成区块的节点
class CurrentMainNode:
    def __init__(self, main_node_list: MainNodeList, last_block: BlockOfBeings, getEpoch):
        self.mainNodeList = main_node_list
        self.lastBlock = last_block
        self.getEpoch = getEpoch
        self.__generateCount = self.getGenerateCount()

    # 一个epoch内产生的区块数量
    def getGenerateCount(self):
        main_node_count = self.mainNodeList.getNodeCount()
        if main_node_count > 20:
            return int(main_node_count / 10)
        else:
            return 2

    # 获取当前期次生成区块的主节点列表
    def getNodeListOfGenerateBlock(self) -> MainNodeList:
        seed = CipherSuites.getSeed(self.lastBlock.getBlockSHA256(), self.getEpoch())
        random.seed(seed)
        node_list = random.choices(population=self.mainNodeList.getNodeList(),
                                   weights=self.mainNodeList.getNodeWeights(), k=self.getGenerateCount())
        logger.info("本次被选中的节点数量为:" + str(len(node_list)))
        main_node_list = MainNodeList()
        for node in node_list:
            if not main_node_list.userPKisExit(user_pk=node["node_info"]["user_pk"]):
                node_info = NodeInfo(node_id=node["node_info"]["node_id"], user_pk=node["node_info"]["user_pk"],
                                     node_ip=node["node_info"]["node_ip"], server_url=node["node_info"]["server_url"],
                                     create_time=node["node_info"]["create_time"])
                main_node_list.addMainNode(node_info=node_info)
        logger.info("去重后的数量为:" + str(main_node_list.getTotal()))
        logger.debug("去重后的主节点分别为:")
        logger.debug(main_node_list.getNodeList())
        return main_node_list

    # 获取当前期次有权限发送广播检测其他主节点是否发布区块的主节点列表
    def getNodeListOfCheckNode(self) -> MainNodeList:
        seed = CipherSuites.getSeed(self.lastBlock.getBlockSHA256(), self.getEpoch() - 1)
        random.seed(seed)
        node_list = random.choices(population=self.mainNodeList.getNodeList(),
                                   weights=self.mainNodeList.getNodeWeights(), k=self.getGenerateCount() * 2)
        logger.info("本次被选中检查其他主节点的主节点数量为:" + str(len(node_list)))
        main_node_list = MainNodeList()
        for node in node_list:
            if not main_node_list.userPKisExit(user_pk=node["node_info"]["user_pk"]):
                node_info = NodeInfo(node_id=node["node_info"]["node_id"], user_pk=node["node_info"]["user_pk"],
                                     node_ip=node["node_info"]["node_ip"], create_time=node["node_info"]["create_time"],
                                     server_url=node["node_info"]["server_url"])
                main_node_list.addMainNode(node_info=node_info)
        logger.info("去重后的数量为:" + str(main_node_list.getTotal()))
        logger.debug("去重后的被选中检查其他主节点的主节点分别为:")
        logger.debug(main_node_list.getNodeList())
        return main_node_list


# 生成众生区块
class NewBlockOfBeings:
    def __init__(self, user_pk: [], body_signature: [], body: bytes, epoch, pre_block, prev_block_header):
        for i in range(len(user_pk)):
            if not CipherSuites.verify(pk=user_pk[i], signature=body_signature[i], message=body):
                # 用户公钥、签名、内容不匹配 抛出错误
                raise "签名验证失败"
        self.newBlock = BlockOfBeings(epoch=epoch, pre_block=pre_block, prev_block_header=prev_block_header,
                                      user_pk=user_pk, body_signature=body_signature, body=body)

    def getBlock(self) -> BlockOfBeings:
        return self.newBlock


# 生成众生区块
class NewBlockOfBeingsByExist:
    def __init__(self, header, body: bytes):
        for i in range(len(header["userPK"])):
            if not CipherSuites.verify(pk=header["userPK"][i], signature=header["bodySignature"][i], message=body):
                # 用户公钥、签名、内容不匹配 抛出错误
                raise "签名验证失败"

        self.newBlock = BlockOfBeings(body=body)
        self.newBlock.setHeader(header)

    def getBlock(self) -> BlockOfBeings:
        return self.newBlock


# 生产时代区块
class NewBlockOfTimes:
    def __init__(self, user_pk, election_period, body_signature, body: BodyOfTimesBlock, pre_block, prev_block_header):
        if not CipherSuites.verify(pk=user_pk[0], signature=body_signature[0],
                                   message=str(body.getBody()).encode("utf-8")):
            # 用户公钥、签名、内容不匹配 抛出错误
            raise "签名验证失败"
        self.newBlock = BlockOfTimes(election_period=election_period, prev_block_header=prev_block_header,
                                     pre_block=pre_block, user_pk=user_pk[0], body_signature=body_signature[0],
                                     body=str(body.getBody()).encode("utf-8"))

    def getBlock(self) -> BlockOfTimes:
        return self.newBlock


# 生产时代区块
class NewBlockOfTimesByExist:
    def __init__(self, header, body: bytes):
        for i in range(len(header["userPK"])):
            if not CipherSuites.verify(pk=header["userPK"][i], signature=header["bodySignature"][i], message=body):
                # 用户公钥、签名、内容不匹配 抛出错误
                raise "签名验证失败"
        self.newBlock = BlockOfTimes(body=body)
        self.newBlock.setHeader(header)

    def getBlock(self) -> BlockOfTimes:
        return self.newBlock


# 生产垃圾区块
class NewBlockOfGarbage:
    def __init__(self, user_pk, election_period, body_signature, body: BodyOfGarbageBlock, pre_block,
                 prev_block_header):
        if not CipherSuites.verify(pk=user_pk[0], signature=body_signature[0],
                                   message=str(body.getBody()).encode("utf-8")):
            # 用户公钥、签名、内容不匹配 抛出错误
            raise "签名验证失败"
        self.newBlock = BlockOfGarbage(election_period=election_period, prev_block_header=prev_block_header,
                                       pre_block=pre_block, user_pk=user_pk[0], body_signature=body_signature[0],
                                       body=str(body.getBody()).encode("utf-8"))

    def getBlock(self) -> BlockOfGarbage:
        return self.newBlock


# 生产垃圾区块
class NewBlockOfGarbageByExist:
    def __init__(self, header, body: bytes):
        for i in range(len(header["userPK"])):
            if not CipherSuites.verify(pk=header["userPK"][i], signature=header["bodySignature"][i], message=body):
                # 用户公钥、签名、内容不匹配 抛出错误
                raise "签名验证失败"
        self.newBlock = BlockOfGarbage(body=body)
        self.newBlock.setHeader(header)

    def getBlock(self) -> BlockOfGarbage:
        return self.newBlock
