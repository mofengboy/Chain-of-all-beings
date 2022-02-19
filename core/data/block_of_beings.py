from core.data.block import Block
from core.user.user import User


class BlockOfBeings(Block):
    def __init__(self, epoch, prev_block_header, pre_block, user_pk, body_signature, body: bytes):
        super().__init__(epoch, "b", user_pk)
        self.setPrevBlockHeader(prev_block_header)
        self.setPrevBlock(pre_block)
        self.setUserPK(user_pk)
        self.setBodySignature(body_signature)
        self.body = body


class EmptyBlock:
    def __init__(self, user_pk, epoch):
        self.userPk = user_pk
        self.epoch = epoch
        self.signature = ""

    def getInfo(self):
        return {
            "user_pk": self.userPk,
            "epoch": self.epoch
        }

    def setSignature(self, signature):
        self.signature = signature

    def getMessage(self):
        return {
            "user_pk": self.userPk,
            "epoch": self.epoch,
            "signature": self.signature
        }


class BlockListOfBeings:
    def __init__(self):
        self.list = []
        self.listOfNoBlock = []

    def getCount(self):
        return len(self.list) + len(self.listOfNoBlock)

    def addBlock(self, block: BlockOfBeings):
        self.list.append(block)

    # 添加不产生区块的消息
    def addMessageOfNoBlock(self, empty_block: EmptyBlock):
        self.listOfNoBlock.append(empty_block)

    def getMessageOfNoBlock(self, user_pk) -> EmptyBlock:
        for empty_block in self.listOfNoBlock:
            if user_pk == empty_block.userPk:
                return empty_block

    def getBlockByMaxBlockId(self) -> BlockOfBeings:
        max_block = self.list[0]
        for block in self.list:
            if block.getBlockID() > max_block.getBlockID():
                max_block = block
        return max_block

    def getBlockByUserPk(self, user_pk) -> BlockOfBeings:
        for block in self.list:
            if block.getUserPk() == user_pk:
                return block

    def userPkIsExit(self, user_pk):
        for block in self.list:
            if block.getUserPk() == user_pk:
                return True
        for empty_block in self.listOfNoBlock:
            if user_pk == empty_block.userPk:
                return True
        return False

    def userPkIsBlock(self, user_pk):
        for block in self.list:
            if block.getUserPk() == user_pk:
                return True
        return False


if __name__ == "__main__":
    user = User()
    user.register()
    genesis_user_sk = user.getUserSK()
    genesis_user_pk = user.getUserVKString()

    genesis_block_id = 0
    genesis_pre_block_header = "0" * 256
    genesis_pre_block = "0" * 256

    genesis_body = "江畔何人初见月? 江月何年初照人? 人生代代无穷已, 江月年年只相似. 不知江月待何人, 但见长江送流水."
    genesis_body_signature = [user.sign(genesis_body)]

    GenesisBlock = BlockOfBeings(blockID=genesis_block_id, prev_block_header=genesis_pre_block_header,
                                 pre_block=genesis_pre_block, user_pk=genesis_user_pk,
                                 body_signature=genesis_body_signature, body=genesis_body)

    # GenesisBlock.ge

    print(genesis_body)
