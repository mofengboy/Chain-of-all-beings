from core.data.block import Block


class BlockOfBeings(Block):
    def __init__(self, body: bytes, epoch=None, prev_block_header=None, pre_block=None, user_pk=None,
                 body_signature=None):
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
        self.emptyBlockIsFinish = False

    def reset(self):
        self.list = []
        self.listOfNoBlock = []
        self.emptyBlockIsFinish = False

    def setEmptyFinish(self):
        self.emptyBlockIsFinish = True

    # 正序排列获得区块列表
    def getListOfOrthogonalOrder(self):
        block_of_list = self.list.copy()
        block_of_list.sort(key=lambda block: block.getBlockID())
        return block_of_list

    def getCount(self):
        return len(self.list) + len(self.listOfNoBlock)

    def addBlock(self, block: BlockOfBeings):
        self.list.append(block)

    # 添加不产生区块的消息
    def addMessageOfNoBlock(self, empty_block: EmptyBlock):
        if empty_block not in self.listOfNoBlock:
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
            if block.getUserPk()[1] == user_pk:
                return block

    def userPkIsExit(self, user_pk):
        for block in self.list:
            if block.getUserPk()[1] == user_pk:
                return True
        if self.emptyBlockIsFinish:
            return True
        else:
            for empty_block in self.listOfNoBlock:
                if user_pk == empty_block.userPk:
                    return True
        return False

    def userPkIsBlock(self, user_pk):
        for block in self.list:
            if block.getUserPk()[1] == user_pk:
                return True
        return False

    def userPkIsEmptyBlock(self, user_pk):
        if self.emptyBlockIsFinish:
            return True
        for empty_block in self.listOfNoBlock:
            if user_pk == empty_block.userPk:
                return True
        return False

    # ID正序排序
    def sortByBlockId(self):
        def get_block_id(block_of_beings: BlockOfBeings):
            return block_of_beings.getBlockID()

        self.list.sort(key=get_block_id)
