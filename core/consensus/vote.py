from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_temp import StorageOfTemp
from core.utils.ciphersuites import CipherSuites

ElectionCycle = 40500


# 票数计算
class VoteCount:
    def __init__(self, storage_of_beings: StorageOfBeings, storage_of_temp: StorageOfTemp):
        self.storageOfBeings = storage_of_beings
        self.storageOfTemp = storage_of_temp

    def computeVoteMainUserByEpoch(self, main_node_user_pk, start, end):
        count = self.storageOfBeings.getUserCountByEpoch(user_pk=main_node_user_pk, start=start,
                                                         end=end)
        return count

    def computeVoteMainUserByElectionPeriod(self, main_node_user_pk, start, end):
        count = 0
        for i in range(start, end):
            count += self.computeVoteMainUserByEpoch(main_node_user_pk=main_node_user_pk,
                                                     start=ElectionCycle * i,
                                                     end=ElectionCycle * (i + 1))
        return count

    # 计算八个选举周期众生区块产生的票
    def computeMainUserVote(self, user_pk, current_election_cycle):
        start = current_election_cycle - 8
        return self.computeVoteMainUserByEpoch(main_node_user_pk=user_pk, start=start, end=current_election_cycle)

    # 计算简单用户被授权的票数
    def computeSimpleUserVote(self, simple_user_pk, current_election_cycle):
        simple_user_vote = self.storageOfTemp.getSimpleUserVoteByUserPk(user_pk=simple_user_pk,
                                                                        election_period=current_election_cycle)
        return simple_user_vote

    # 获取当前选举周期该用户已经消耗的票数
    def getVotesConsumedByCurrent(self, user_pk, current_election_cycle):
        return self.storageOfTemp.getVotesByUserPk(user_pk=user_pk, election_period=current_election_cycle)

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
    def getVotesOfGalaxyGenerate(self, current_election_cycle):
        # 最初的想法是这里根据总票数进行一个计算，但是似乎平均每1024个众生区块出一个银河区块也可以，先这样
        VotesOfGalaxyGenerate = 1024.0
        return VotesOfGalaxyGenerate
