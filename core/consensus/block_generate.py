import random

from core.data.node_info import MainNodeList
from core.data.block_of_beings import BlockOfBeings
from core.data.block_of_galaxy import BlockOfGalaxy, BodyOfGalaxyBlock
from core.utils.ciphersuites import CipherSuites


# 计算本次生成区块的节点
class CurrentMainNode:
    def __init__(self, main_node_list: MainNodeList, last_block: BlockOfBeings):
        self.mainNodeList = main_node_list
        self.lastBlock = last_block
        self.__generateCount = self.getGenerateCount()

    def getGenerateCount(self):
        main_node_count = self.mainNodeList.getNodeCount()
        if main_node_count > 200:
            return int(main_node_count / 100)
        else:
            return 2

    def getNodeList(self) -> MainNodeList:
        seed = CipherSuites.getSeed(self.lastBlock.getBlockSHA256(), self.lastBlock.getEpoch())
        random.seed(seed)
        node_list = random.choices(population=self.mainNodeList.getNodeList(),
                                   weights=self.mainNodeList.getNodeWeights(), k=self.getGenerateCount())
        main_node_list = MainNodeList()
        for node in node_list:
            main_node_list.addMainNode(node)
        return main_node_list


# 生产众生区块
class NewBlockOfBeings:
    def __init__(self, user_pk: [], body_signature: [], body, epoch, pre_block, prev_block_header):
        for i in range(len(user_pk)):
            if not CipherSuites.verify(pk=user_pk[i], signature=body_signature[i], message=body):
                # 用户公钥、签名、内容不匹配 抛出错误
                pass

        self.newBlock = BlockOfBeings(epoch=epoch, pre_block=pre_block, prev_block_header=prev_block_header,
                                      user_pk=user_pk, body_signature=body_signature, body=body)

    def getBlock(self) -> BlockOfBeings:
        return self.newBlock


# 生产银河区块
class NewBlockOfGalaxy:
    def __init__(self, user_pk, election_period, body_signature, body: BodyOfGalaxyBlock, epoch, pre_block,
                 prev_block_header):

        if not CipherSuites.verify(pk=user_pk[0], signature=body_signature[0], message=body.getBody()):
            # 用户公钥、签名、内容不匹配 抛出错误
            pass
        self.newBlock = BlockOfGalaxy(election_period=election_period, epoch=epoch, prev_block_header=prev_block_header,
                                      pre_block=pre_block, user_pk=user_pk, body_signature=body_signature,
                                      body=body.getBody())

    def getBlock(self) -> BlockOfGalaxy:
        return self.newBlock
