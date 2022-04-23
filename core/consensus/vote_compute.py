import logging
import math

from core.consensus.data import VoteMessage
from core.node.main_node import MainNode
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_galaxy import StorageOfGalaxy
from core.storage.storage_of_garbage import StorageOfGarbage
from core.storage.storage_of_temp import StorageOfTemp
from core.utils.ciphersuites import CipherSuites
from core.config.cycle_Info import ElectionPeriodValue
from core.consensus.constants import VotesOfTimesBlockGenerate, VotesOfGarbageBlockGenerate

logger = logging.getLogger("main")


# 票数计算
class VoteCount:
    def __init__(self, storage_of_beings: StorageOfBeings, storage_of_times: StorageOfGalaxy,
                 storage_of_temp: StorageOfTemp, storage_of_garbage: StorageOfGarbage, main_node: MainNode):
        self.storageOfBeings = storage_of_beings
        self.storageOfTimes = storage_of_times
        self.storageOfTemp = storage_of_temp
        self.storageOfGarbage = storage_of_garbage
        self.mainNode = main_node

    # 初始化所有主节点的票的总数
    def initVotesOfMainNode(self, current_election_cycle):
        # 清空投票摘要
        logger.info("清空投票摘要")
        self.storageOfTemp.clearVoteDigest()
        main_node_list = self.mainNode.mainNodeList.getNodeList()
        logger.debug("初始化所有主节点的票的总数调试信息")
        # 清除上一选举周期产生票数数据
        self.storageOfTemp.clearAllMainNodeVote()
        for node_i in main_node_list:
            total_vote = self.computeMainUserVote(main_node_user_pk=node_i["node_info"]["user_pk"],
                                                  current_election_cycle=current_election_cycle)
            self.addMainUserVote(node_i["node_info"]["node_id"], main_node_user_pk=node_i["node_info"]["user_pk"],
                                 total_vote=total_vote)
            logger.debug(node_i["node_info"])
            logger.debug(total_vote)

    # 初始化普通用户的长期票的总数
    def initPermanentVotesOfSimpleUser(self, current_election_cycle):
        logger.debug("初始化普通用户的长期票的总数调试信息")
        # 普通用户的永久票
        simple_user_permanent_vote_dict = self.storageOfTimes.computeSimpleUserInfoOfPermanentVote(
            current_election_cycle)
        # 若记录的区块被标记为垃圾区块，则扣除所有永久票的一半
        simple_user_list_of_garbage_deduct_vote = self.storageOfGarbage.getListOfSimpleUser()
        for simple_user in simple_user_list_of_garbage_deduct_vote:
            try:
                simple_user_permanent_vote_dict[simple_user] = int(simple_user_permanent_vote_dict[simple_user] / 2)
            except KeyError as err:
                logger.info(err)
                logger.info("该用户不存在永久票,普通用户公钥为：" + simple_user)
        # 清除已有数据
        self.storageOfTemp.clearAllSimpleUserPermanentVote()
        # 保存
        self.storageOfTemp.addBatchPermanentVoteOfSimpleUser(data_dict=simple_user_permanent_vote_dict)

    # 计算主节点的总票数
    def computeMainUserVote(self, main_node_user_pk, current_election_cycle):
        start = current_election_cycle - 8
        # 众生区块产生的临时票
        # 计算在当前选举周期之前的八个周期（不包含本选举周期）
        beings_vote_count = 0
        for i in range(start, current_election_cycle):
            beings_vote_count += self.storageOfBeings.getUserCountByEpoch(user_pk=main_node_user_pk,
                                                                          start=i * ElectionPeriodValue,
                                                                          end=(i + 1) * ElectionPeriodValue)
        # 时代区块产生的长期票
        times_vote_count = self.storageOfTimes.getMainNodeUserCount(main_node_user_pk=main_node_user_pk,
                                                                    election_period=current_election_cycle)
        # 标记垃圾区块产生的长期票
        garbage_vote_count = self.storageOfGarbage.getMainNodeUserCount(main_node_user_pk=main_node_user_pk,
                                                                        election_period=current_election_cycle)
        # 垃圾区块扣除票数
        # 底数为2的指数
        raw_garbage_deduct_vote_count = self.storageOfGarbage.getMainNodeOfBeingsBlockUserCount(main_node_user_pk)
        garbage_deduct_vote_count = 8 * (math.pow(2, raw_garbage_deduct_vote_count) - 1)
        total = beings_vote_count + times_vote_count + garbage_vote_count - garbage_deduct_vote_count
        if total < 0:
            total = 0
        return total

    def addMainUserVote(self, main_node_id, main_node_user_pk, total_vote):
        self.storageOfTemp.addMainNodeVote(main_node_id=main_node_id, main_node_user_pk=main_node_user_pk,
                                           total_vote=total_vote)

    # 获取主节点的票数信息
    def getVotesOfMainNode(self, main_node_user_pk):
        return self.storageOfTemp.getMainNodeVoteByMainNodeUserPk(main_node_user_pk)

    # 验证生成时代区块的票数
    def checkVotesOfGenerateTimesBlock(self, beings_block_id, vote_message_list: list) -> bool:
        total_votes = 0.0
        election_period = self.storageOfTemp.getElectionPeriod()
        for vote_message_i in vote_message_list:
            # 是否与众生区块ID相符
            if vote_message_i.blockId != beings_block_id:
                logger.warning("投票信息与众生区块ID不符")
                logger.warning(vote_message_i.getVoteMessage())
                continue
            # 是否为本周期的投票
            if vote_message_i.electionPeriod != election_period:
                logger.warning("投票不在本周期内")
                logger.warning(vote_message_i.getVoteMessage())
                logger.warning(election_period)
                continue
            # 判断短期票还是长期票
            if hasattr(vote_message_i, "mainUserPk"):
                # 短期票
                # 验证签名
                if not CipherSuites.verify(pk=vote_message_i.mainUserPk, signature=vote_message_i.getSignature(),
                                           message=str(vote_message_i.getVoteInfo()).encode("utf-8")):
                    logger.warning("投票验证失败")
                    logger.warning(vote_message_i.getVoteMessage())
                    continue
                total_votes += vote_message_i.numberOfVote
            else:
                # 长期票
                # 验证签名
                if not CipherSuites.verify(pk=vote_message_i.simpleUserPk, signature=vote_message_i.getSignature(),
                                           message=str(vote_message_i.getInfoOfSignature()).encode("utf-8")):
                    logger.warning("投票验证失败")
                    logger.warning(vote_message_i.getVoteMessage())
                    continue
                total_votes += vote_message_i.numberOfVote
        if total_votes >= self.getVotesOfTimesBlockGenerate():
            return True
        else:
            return False

    # 验证生成垃圾区块的票数
    def checkVotesOfGenerateGarbageBlock(self, beings_block_id, vote_message_list: list) -> bool:
        total_votes = 0.0
        election_period = self.storageOfTemp.getElectionPeriod()
        for vote_message_i in vote_message_list:
            # 是否与众生区块ID相符
            if vote_message_i.blockId != beings_block_id:
                logger.warning("投票信息与众生区块ID不符")
                logger.warning(vote_message_i.getVoteMessage())
                continue
            # 是否为本周期的投票
            if vote_message_i.electionPeriod != election_period:
                logger.warning("投票不在本周期内")
                logger.warning(vote_message_i.getVoteMessage())
                logger.warning(election_period)
                continue
            # 判断短期票还是长期票
            if hasattr(vote_message_i, "mainUserPk"):
                # 短期票
                # 验证签名
                if not CipherSuites.verify(pk=vote_message_i.mainUserPk, signature=vote_message_i.getSignature(),
                                           message=str(vote_message_i.getVoteInfo()).encode("utf-8")):
                    logger.warning("投票验证失败")
                    logger.warning(vote_message_i.getVoteMessage())
                    continue
                total_votes += vote_message_i.numberOfVote
            else:
                # 长期票
                # 验证签名
                if not CipherSuites.verify(pk=vote_message_i.simpleUserPk, signature=vote_message_i.getSignature(),
                                           message=str(vote_message_i.getInfoOfSignature()).encode("utf-8")):
                    logger.warning("投票验证失败")
                    logger.warning(vote_message_i.getVoteMessage())
                    continue
                total_votes += vote_message_i.numberOfVote
        if total_votes >= self.getVotesOfGarbageBlockGenerate():
            return True
        else:
            return False

    # 获取当前选举周期生成时代区块所需要的票数
    @staticmethod
    def getVotesOfTimesBlockGenerate():
        return VotesOfTimesBlockGenerate

    # 获取当前选举周期生成垃圾区块所需要的票数
    @staticmethod
    def getVotesOfGarbageBlockGenerate():
        return VotesOfGarbageBlockGenerate
