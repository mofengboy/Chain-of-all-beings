from core.node.main_node import MainNode
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_temp import StorageOfTemp
from core.utils.ciphersuites import CipherSuites
from core.config.cycle_Info import ElectionPeriodValue
from core.consensus.constants import VotesOfGalaxyGenerate


# 票数计算
class VoteCount:
    def __init__(self, storage_of_beings: StorageOfBeings, storage_of_temp: StorageOfTemp, main_node: MainNode):
        self.storageOfBeings = storage_of_beings
        self.storageOfTemp = storage_of_temp
        self.mainNode = main_node

    # 初始化所有主节点的票的总数
    def initVotesOfMainNode(self, current_election_cycle):
        main_node_list = self.mainNode.mainNodeList.getNodeList()
        for node_i in main_node_list:
            total_vote = self.computeMainUserVote(main_node_user_pk=node_i["node_info"]["user_pk"],
                                                  current_election_cycle=current_election_cycle)
            self.addMainUserVote(node_i["node_info"]["node_id"], main_node_user_pk=node_i["node_info"]["user_pk"],
                                 total_vote=total_vote)

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
        times_vote_count = 0
        return beings_vote_count + times_vote_count

    def addMainUserVote(self, main_node_id, main_node_user_pk, total_vote):
        self.storageOfTemp.addMainNodeVote(main_node_id=main_node_id, main_node_user_pk=main_node_user_pk,
                                           total_vote=total_vote)

    # 获取主节点的票数信息
    def getVotesOfMainNode(self, main_node_user_pk):
        return self.storageOfTemp.getMainNodeVoteByMainNodeUserPk(main_node_user_pk)

    # 验证银河区块产生的票数
    @staticmethod
    def getAndVerifyVotes(votes, main_node_id_of_block, block_id_of_block, election_period_of_block):
        total = 0.0
        for vote in votes:
            vote_info = vote["vote_info"]
            signature = vote["signature"]
            user_pk = vote["user_pk"]

            main_node_id = vote_info["main_node_id"]  # 推荐和负责维护投票信息的主节点
            block_id = vote_info["block_id"]
            current_election_period = vote_info["current_election_period"]
            number_of_vote = vote_info["number_of_vote"]
            if main_node_id_of_block == main_node_id and block_id_of_block == block_id and election_period_of_block == current_election_period:
                if CipherSuites.verify(pk=user_pk, signature=signature, message=str(vote_info).encode("utf-8")):
                    total += number_of_vote
        return total

    # 获取当前选举周期生成银河区块所需要的票数
    @staticmethod
    def getVotesOfGalaxyGenerate():
        return VotesOfGalaxyGenerate
