from core.node.node import Node
from core.user.user import User
from core.data.network_message import NetworkMessage
from core.data.node_info import MainNodeList
from core.data.block_of_beings import BlockListOfBeings


class MainNode(Node):
    def __init__(self, user: User):
        super().__init__(user)
        self.mainNodeList = MainNodeList()  # 主节点列表
        self.currentBlockList = BlockListOfBeings()  # 本轮已经收集的区块列表
        self.nodeListOfApply = []  # 接受到的待审核的申请成为主节点的列表


if __name__ == "__main__":
    pass
    # user = User()
    # user.register()
    # user_vk = user.getUserVK()
    #
    # mainNode = MainNode(user_vk)
    # print(mainNode.getNodeInfo())
    # mainNode.listenOtherMainNode()
    # print("监听中")
    #
    # time.sleep(1)
    #
    # mainNode.findMainNode("localhost")
    # print("发送消息")
    # mainNode.clint.testConnection()
    # mainNode.clint.broadcast("hello world")
    #
    # time.sleep(2)
    #
    # a = mainNode.acceptMessage.message
    # print(a)
