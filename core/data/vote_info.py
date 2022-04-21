import hashlib


class WaitVote:
    def __init__(self):
        self.electionPeriod = 0
        self.toNodeId = ""
        self.blockId = ""
        self.vote = 0
        self.simpleUserPk = ""
        self.signature = ""
        self.voteType = 1  # 1为推荐区块投票，2为标记区块投票

    def setInfo(self, election_period, to_node_id, block_id, vote, simple_user_pk, vote_type):
        self.electionPeriod = election_period
        self.toNodeId = to_node_id
        self.blockId = block_id
        self.vote = vote
        self.simpleUserPk = simple_user_pk
        self.voteType = vote_type

    def setSignature(self, signature):
        self.signature = signature

    def getInfo(self):
        return {
            "election_period": self.electionPeriod,
            "to_node_id": self.toNodeId,
            "block_id": self.blockId,
            "vote": self.vote,
            "simple_user_pk": self.simpleUserPk,
            "vote_type": self.voteType
        }

    def getInfoOfSignature(self):
        info_of_signature = "{'election_period': " + str(
            self.electionPeriod) + ", 'to_node_id': " + self.toNodeId + ", 'block_id': " + self.blockId + ", 'vote': " + str(
            self.vote) + ", 'simple_user_pk': " + self.simpleUserPk + ", 'vote_type': " + str(self.voteType) + "}"
        return info_of_signature

    def getSignature(self):
        return self.signature

    def getMessage(self):
        return {
            "election_period": self.electionPeriod,
            "to_node_id": self.toNodeId,
            "block_id": self.blockId,
            "vote": self.vote,
            "simple_user_pk": self.simpleUserPk,
            "signature": self.signature,
            "vote_type": self.voteType
        }

    def getVoteInfoDigest(self):
        return hashlib.sha256(str(self.getMessage()).encode("utf-8")).hexdigest()
