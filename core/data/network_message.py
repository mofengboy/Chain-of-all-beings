import hashlib
from enum import Enum, auto

from core.utils.system_time import STime


# 订阅主题
class SubscribeTopics:
    # 众生区块生成订阅主题
    @staticmethod
    def getBlockTopicOfBeings():
        return b"block b "

    # 银河区块生成订阅主题
    @staticmethod
    def getBlockTopicOfGalaxy():
        return b"block g "

    # 新节点申请加入订阅主题
    @staticmethod
    def getNodeTopicOfApplyJoin():
        return b"node apply join "

    # 新节点确认加入订阅主题
    @staticmethod
    def getNodeTopicOfJoin():
        return b"node join "

    # 申请删除节点订阅主题
    @staticmethod
    def getNodeTopicOfApplyDelete():
        return b"node apply delete "

    # 主动申请删除节点订阅主题
    @staticmethod
    def getNodeTopicOfProactiveApplyDelete():
        return b"node apply delete "

    # 确认删除节点订阅主题
    @staticmethod
    def getNodeTopicOfDelete():
        return b"node delete "

    # 投票确认广播主题
    @staticmethod
    def getVoteConfirmation():
        return b"vote confirmation "


# 消息类型
class NetworkMessageType(Enum):
    # 收到确认
    RECEIVE_CONFIRMATION = auto()
    # 新区块消息
    NEW_BLOCK = auto()
    # 申请获取该区块
    APPLY_GET_BLOCK = auto
    # 被选中的节点不生成区块
    NO_BLOCK = auto()
    # 新节点申请加入
    NewNodeApplicationJoin = auto()
    # 新节点确认加入
    NewNodeJoin = auto()
    # 对申请信息的回复
    ReplayNewNodeApplicationJoin = auto()
    # 申请删除节点
    NodeApplicationDelete = auto()
    # 确认删除节点
    NewNodeDelete = auto()
    # 对删除信息的回复
    ReplyNodeApplicationDelete = auto()
    # 投票信息
    Vote_Info = auto()
    # 投票信息回复
    Reply_Vote_Info = auto()
    # 获取主节点列表
    Get_Main_Node_List = auto()
    # 获取当前epoch
    Get_Current_Epoch = auto()
    # 申请同步众生区块数据
    Get_Beings_Data = auto()
    # 数据恢复请求
    Data_Recovery_Req = auto()
    # 无法数据恢复（同样没收集完成）
    No_Data_Recovery = auto()
    # 数据恢复
    Data_Recovery = auto()


# 网络消息格式
class NetworkMessage:
    def __init__(self, mess_type: NetworkMessageType, message):
        self.message = message
        self.messType = mess_type
        self.clientInfo = {
            "user_pk": "",
            "send_time": 0
        }
        self.signature = None

    def setClientInfo(self, user_pk, send_time=0):
        self.clientInfo["user_pk"] = user_pk
        if send_time == 0:
            self.clientInfo["send_time"] = STime.getTimestamp()
        else:
            self.clientInfo["send_time"] = send_time

    def setSignature(self, signature):
        self.signature = signature

    # def getCertificationAbstract(self):
    #     data = {
    #         "client_info": self.clientInfo,
    #         "message": self.message
    #     }
    #     return hashlib.sha256(str(data).encode("utf-8")).hexdigest()

    def getClientAndMessageDigest(self):
        data = {
            "client": self.clientInfo,
            "message": self.message
        }
        return hashlib.sha256(str(data).encode("utf-8")).hexdigest()

    # def getNetMessage(self):
    #     return {
    #         "mess_type": self.messType,
    #         "message": self.message,
    #         "client_info": self.clientInfo,
    #         "signature": self.signature
    #     }
