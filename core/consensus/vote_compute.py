import logging

from core.consensus.data import VoteMessage
from core.node.main_node import MainNode
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_temp import StorageOfTemp
from core.utils.ciphersuites import CipherSuites
from core.config.cycle_Info import ElectionPeriodValue
from core.consensus.constants import VotesOfTimesBlockGenerate

logger = logging.getLogger("main")


# 票数计算
class VoteCount:
    def __init__(self, storage_of_beings: StorageOfBeings, storage_of_temp: StorageOfTemp, main_node: MainNode):
        self.storageOfBeings = storage_of_beings
        self.storageOfTemp = storage_of_temp
        self.mainNode = main_node

    # 初始化所有主节点的票的总数
    def initVotesOfMainNode(self, current_election_cycle):
        main_node_list = self.mainNode.mainNodeList.getNodeList()
        logger.debug("初始化所有主节点的票的总数调试信息")
        for node_i in main_node_list:
            total_vote = self.computeMainUserVote(main_node_user_pk=node_i["node_info"]["user_pk"],
                                                  current_election_cycle=current_election_cycle)
            self.addMainUserVote(node_i["node_info"]["node_id"], main_node_user_pk=node_i["node_info"]["user_pk"],
                                 total_vote=total_vote)
            logger.debug(node_i["node_info"])
            logger.debug(total_vote)

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
        # 时代区块产生的永久票
        logger.debug("计算主节点的总票数,main_node_user_pk:" + main_node_user_pk)
        logger.debug(beings_vote_count)
        times_vote_count = 0
        return beings_vote_count + times_vote_count

    def addMainUserVote(self, main_node_id, main_node_user_pk, total_vote):
        self.storageOfTemp.addMainNodeVote(main_node_id=main_node_id, main_node_user_pk=main_node_user_pk,
                                           total_vote=total_vote)

    # 获取主节点的票数信息
    def getVotesOfMainNode(self, main_node_user_pk):
        return self.storageOfTemp.getMainNodeVoteByMainNodeUserPk(main_node_user_pk)

    # 验证生成时代区块的票数
    def checkVotesOfGenerateTimesBlock(self, beings_block_id, vote_message_list: [VoteMessage]) -> bool:
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
            # 验证签名
            if not CipherSuites.verify(pk=vote_message_i.mainUserPk, signature=vote_message_i.getSignature(),
                                       message=str(vote_message_i.getVoteInfo()).encode("utf-8")):
                logger.warning("投票验证失败")
                logger.warning(vote_message_i.getVoteMessage())
                continue
            total_votes += vote_message_i.numberOfVote
        if total_votes >= self.getVotesOfTimesBlockGenerate():
            return True
        else:
            return False

    # 获取当前选举周期生成银河区块所需要的票数
    @staticmethod
    def getVotesOfTimesBlockGenerate():
        return VotesOfTimesBlockGenerate
