import logging
from core.utils.system_time import STime

logger = logging.getLogger("main")


# 节点信息数据结构
class NodeInfo:
    def __init__(self, node_id, user_pk, node_ip, create_time=None):
        self.nodeId = node_id
        self.userPk = user_pk
        self.nodeIp = node_ip
        if create_time is None:
            self.createTime = STime.getTimestamp()
        else:
            self.createTime = int(create_time)
        self.nodeSignature = ""

    def setNodeSignature(self, signature):
        self.nodeSignature = signature

    def getInfo(self):
        info = {
            "node_id": self.nodeId,
            "user_pk": self.userPk,
            "node_ip": self.nodeIp,
            "create_time": self.createTime
        }
        return info

    def getMessage(self):
        return {
            "node_id": self.nodeId,
            "user_pk": self.userPk,
            "node_ip": self.nodeIp,
            "create_time": self.createTime,
            "signature": self.nodeSignature
        }


# 主节点列表数据结构
class MainNodeList:
    def __init__(self):
        self.__nodeList = []

    def getNodeList(self):
        return self.__nodeList

    def setNodeList(self, node_list):
        self.__nodeList = node_list

    def getNodeCount(self):
        return len(self.__nodeList)

    def getNodeWeights(self):
        weight_list = []
        for main_node in self.__nodeList:
            current_time = STime.getTimestamp()
            weight = str(current_time - main_node["update_time"])[0:6]
            weight_list.append(int(weight))

        return weight_list

    def getTotal(self):
        return len(self.__nodeList)

    def addMainNode(self, node_info: NodeInfo):
        self.__nodeList.append({
            "node_info": node_info.getInfo(),
            "update_time": node_info.createTime
        })
        # 排序
        self.__nodeList.sort(key=get_node_id)

    def setMainNodeUpdateTimeByNodeId(self, update_time, node_id):
        for main_node in self.__nodeList:
            if main_node["node_info"]["node_id"] == node_id:
                main_node["update_time"] = update_time
                break
        logger.info("节点上次生成区块时间已更新，节点ID为：" + node_id + ",时间更新为：" + str(update_time))

    def delMainNodeById(self, node_id):
        count = len(self.__nodeList)
        for i in range(count):
            if self.__nodeList[i]["node_info"]["node_id"] == node_id:
                del self.__nodeList[i]
                break
        # 排序
        self.__nodeList.sort(key=get_node_id)

    def isExit(self, ip):
        for main_node in self.__nodeList:
            if main_node["node_info"]["node_ip"] == ip:
                return True
        return False

    def userPKisExit(self, user_pk):
        for main_node in self.__nodeList:
            if main_node["node_info"]["user_pk"] == user_pk:
                return True
        return False


# 获取nodeId的静态函数
def get_node_id(node_list):
    return node_list["node_info"]["node_id"]
