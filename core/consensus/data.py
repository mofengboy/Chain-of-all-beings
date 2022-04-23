from core.data.node_info import NodeInfo
from core.data.block_of_times import BlockOfTimes


# 共识模块的数据结构
# 投票信息


# 投票信息
class VoteMessage:
    def __init__(self):
        self.toMainNodeUserPk = ""
        self.blockId = ""
        self.electionPeriod = 0
        self.numberOfVote = 0.0
        self.mainUserPk = ""
        self.signature = ""
        self.voteType = 1  # 1为推荐区块投票，2为标记区块投票

    def setSignature(self, signature):
        self.signature = signature

    def getSignature(self):
        return self.signature

    def setVoteInfo(self, to_main_node_user_pk, block_id, election_period, number_of_vote, main_user_pk, vote_type):
        self.toMainNodeUserPk = to_main_node_user_pk
        self.blockId = block_id
        self.electionPeriod = election_period
        self.numberOfVote = number_of_vote
        self.mainUserPk = main_user_pk
        self.voteType = vote_type

    def getVoteInfo(self):
        return {
            "to_main_node_user_pk": self.toMainNodeUserPk,
            "block_id": self.blockId,
            "election_period": self.electionPeriod,
            "number_of_vote": self.numberOfVote,
            "main_user_pk": self.mainUserPk,
            "vote_type": self.voteType
        }

    def getVoteMessage(self):
        return {
            "to_main_node_user_pk": self.toMainNodeUserPk,
            "block_id": self.blockId,
            "election_period": self.electionPeriod,
            "number_of_vote": self.numberOfVote,
            "main_user_pk": self.mainUserPk,
            "vote_type": self.voteType,
            "signature": self.signature
        }


# 长期票投票信息
class LongTermVoteMessage:
    def __init__(self):
        self.toMainNodeId = ""
        self.blockId = ""
        self.electionPeriod = 0
        self.numberOfVote = 0.0
        self.simpleUserPk = ""
        self.signature = ""
        self.voteType = 1  # 1为推荐区块投票，2为标记区块投票

    def setSignature(self, signature):
        self.signature = signature

    def getSignature(self):
        return self.signature

    def setVoteInfo(self, to_main_node_id, block_id, election_period, number_of_vote, simple_user_pk, vote_type):
        self.toMainNodeId = to_main_node_id
        self.blockId = block_id
        self.electionPeriod = election_period
        self.numberOfVote = number_of_vote
        self.simpleUserPk = simple_user_pk
        self.voteType = vote_type

    def getVoteInfo(self):
        return {
            "to_node_id": self.toMainNodeId,
            "block_id": self.blockId,
            "election_period": self.electionPeriod,
            "vote": self.numberOfVote,
            "simple_user_pk": self.simpleUserPk,
            "vote_type": self.voteType
        }

    def getInfoOfSignature(self):
        info_of_signature = "{'election_period': " + str(
            self.electionPeriod) + ", 'to_node_id': " + self.toMainNodeId + ", 'block_id': " + self.blockId + ", 'vote': " + str(
            self.numberOfVote) + ", 'simple_user_pk': " + self.simpleUserPk + ", 'vote_type': " + str(
            self.voteType) + "}"
        return info_of_signature

    def getVoteMessage(self):
        return {
            "to_node_id": self.toMainNodeId,
            "block_id": self.blockId,
            "election_period": self.electionPeriod,
            "vote": self.numberOfVote,
            "simple_user_pk": self.simpleUserPk,
            "vote_type": self.voteType,
            "signature": self.signature
        }


# 等待成为银河区块的区块
class WaitGalaxyBlock:
    def __init__(self, main_node_id, main_user_pk):
        self.blockList = []
        self.mainNodeId = main_node_id
        self.mainUserPk = main_user_pk

    def isExit(self, block_id):
        for block in self.blockList:
            if block["block_id"] == block_id:
                return True
        return False

    def addGalaxyBlock(self, block_id):
        block = {
            "block_id": block_id,
            "votes": [],
            "total": 0,
            "main_node_id": self.mainNodeId,
            "main_user_pk": self.mainUserPk
        }
        self.blockList.append(block)

    def addVote(self, vote_message: VoteMessage) -> bool:
        for block in self.blockList:
            if block["block_id"] == vote_message.blockId:
                vote = {
                    "vote_info": vote_message.getVoteInfo(),
                    "signature": vote_message.signature,
                    "user_pk": vote_message.mainUserPk
                }
                block["votes"].append(vote)
                block["total"] += vote_message.numberOfVote
                return True
        return False

    def getTotalOfVotesByBlockId(self, block_id):
        for block in self.blockList:
            if block_id == block["block_id"]:
                return block["total"]

    def getVotesByBlockId(self, block_id):
        for block in self.blockList:
            if block_id == block["block_id"]:
                return block["votes"]


# 银河区块生成确认消息
class ConformationOfGalaxyBlock:
    def __init__(self, block_of_galaxy: BlockOfTimes, votes, total):
        self.blockOfGalaxy = block_of_galaxy
        self.votes = votes
        self.total = total

    def getMessage(self):
        return {
            "block_of_galaxy": self.blockOfGalaxy,
            "votes": self.votes,
            "total": self.total
        }

    def getVotes(self):
        return self.votes


# 申请书
class ApplicationForm:
    def __init__(self, node_info: NodeInfo, start_time, content, application_signature_by_new_node):
        self.newNodeId = node_info.nodeId
        self.newNodeInfo = node_info.getInfo()
        self.newNodeSignature = node_info.nodeSignature
        self.application = {
            "content": content,
            "start_time": start_time,
        }
        self.applicationSignatureByNewNode = application_signature_by_new_node
        self.mainNode = {
            "application_signature": None,
            "user_pk": None
        }

    def setMainNodeSignature(self, main_node_signature):
        self.mainNode["application_signature"] = main_node_signature

    def setMainNodeUserPk(self, main_node_user_pk):
        self.mainNode["user_pk"] = main_node_user_pk


# 申请书回复
class ReplyApplicationForm:
    def __init__(self, new_node_id, new_node_user_pk, start_time: int, is_agree: int):
        self.newNodeId = new_node_id
        self.newNodeUserPk = new_node_user_pk
        self.startTime = start_time
        self.isAgree = is_agree
        self.signature = None
        self.userPk = None

    def getInfo(self):
        return {
            "new_node_id": self.newNodeId,
            "new_node_user_pk": self.newNodeUserPk,
            "new_node_create_time": self.startTime,
            "is_agree": self.isAgree
        }

    def setSignature(self, signature):
        self.signature = signature

    def setUserPk(self, user_pk):
        self.userPk = user_pk


# 被选中节点不回复
# 删除节点申请书
class NodeDelApplicationForm:
    def __init__(self, del_node_id, del_user_pk, current_epoch):
        self.delNodeId = del_node_id
        self.delNodeUserPk = del_user_pk
        self.currentEpoch = current_epoch
        self.applyUserPk = None
        self.applySignature = None
        self.votes = []

    def getInfo(self):
        return {
            "del_node_id": self.delNodeId,
            "del_node_user_pk": self.delNodeUserPk,
            "current_epoch": self.currentEpoch
        }

    def addVotes(self, user_pk, signature):
        self.votes.append(
            {
                "user_pk": user_pk,
                "signature": signature
            }
        )

    def userPkIsVotes(self, user_pk):
        for vote in self.votes:
            if vote["user_pk"] == user_pk:
                return True
        return False

    def getMessage(self):
        return {
            "del_node_id": self.delNodeId,
            "del_node_user_pk": self.delNodeUserPk,
            "current_epoch": self.currentEpoch,
            "apply_user_pk": self.applyUserPk,
            "apply_signature": self.applySignature,
            "votes": self.votes
        }

    def setApplyUserPk(self, user_pk):
        self.applyUserPk = user_pk

    def setApplySignature(self, signature):
        self.applySignature = signature
