from core.node.node import Node
from core.user.user import User
from core.data.node_info import MainNodeList
from core.data.block_of_beings import BlockListOfBeings


class MainNode(Node):
    def __init__(self, user: User):
        super().__init__(user)
        self.mainNodeList = MainNodeList()  # 主节点列表
        self.currentMainNode = None  # 本轮有生成区块权限的节点列表
        self.currentBlockList = BlockListOfBeings()  # 本轮已经收集的区块列表

        self.nodeDelApplicationFormList = []  # 申请删除节点以及投票信息列表
