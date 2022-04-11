from core.data.block import Block


# 时代区块body结构体
class BodyOfTimesBlock:
    def __init__(self, users_pk: [], block_id):
        self.usersPK = users_pk  # 被推荐区块的用户公钥（包含主节点用户和简单节点用户）
        self.blockId = block_id

    def getBody(self):
        return {
            "users_pk": self.usersPK,
            "block_id": self.blockId
        }


class BlockOfTimes(Block):
    def __init__(self, body: bytes, election_period=None, prev_block_header=None, pre_block=None,
                 user_pk=None, body_signature=None, ):
        epoch = "e"
        super().__init__(epoch, "t", user_pk)
        self.electionPeriod = election_period  # 选举期次
        self.setElectionPeriod(election_period)
        self.setPrevBlockHeader(prev_block_header)
        self.setPrevBlock(pre_block)
        self.setUserPK(user_pk)
        self.setBodySignature(body_signature)
        self.body = body
