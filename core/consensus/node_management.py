# 两种方式，主动申请和未收到消息被动申请
from core.consensus.data import ManagerOfReplyNewNode, ReplyApplicationForm, NodeDelApplicationForm
from core.data.network_message import NetworkMessage, NetworkMessageType, SubscribeTopics
from core.utils.ciphersuites import CipherSuites
from core.utils.system_time import STime
from core.user.user import User
from core.storage.storage_of_temp import StorageOfTemp
from core.node.main_node import MainNode

# 规定的节点申请审核时间（大约五天时间）
AUDIT_TIME = 432000000  # 13位时间戳


class NodeManager:
    def __init__(self, user: User, main_node: MainNode, manager_of_reply_new_node_list: [ManagerOfReplyNewNode],
                 node_list_of_delete: []):
        self.mainNode = main_node
        self.user = user
        self.managerOfReplyNewNodeList = manager_of_reply_new_node_list
        self.nodeListOfDelete = node_list_of_delete

    # 验证新节点加入回复信息中同意节点列表及其签名
    @staticmethod
    def verifyAgreeInfo(current_main_node_count, agree_info) -> bool:
        # 检测是否超过时间
        start_time = agree_info["start_time"]
        current_time = STime.getTimestamp()
        if current_time - start_time > AUDIT_TIME:
            return False

        # 验证新节点信息和签名
        node_info = agree_info["node_info"]
        node_signature = agree_info["node_signature"]
        agree_list = agree_info["agree_list"]
        if not CipherSuites.verify(pk=node_info["user_pk"], signature=node_signature,
                                   message=str(node_info).encode("utf-8")):
            return False

        # 验证所有同意节点的时间和签名
        i = 0
        for agree_i in agree_list:
            info = agree_i["info"]
            signature = agree_i["signature"]
            user_pk = agree_i["user_pk"]
            if CipherSuites.verify(pk=user_pk, signature=signature, message=str(info).encode("utf-8")):
                i += 1
        if i >= current_main_node_count:
            return True
        return False

    # 申请书回复信息签名
    def replyApplicationFormSign(self, reply_application_form: ReplyApplicationForm):
        info = reply_application_form.getInfo()
        signature = self.user.sign(str(info).encode("utf-8"))
        return signature

    # 验证申请书回复信息签名
    def verifyReplyApplicationFormSignature(self, reply_application_form: ReplyApplicationForm):
        # 检测该公钥是否在主节点列表
        if not self.mainNode.mainNodeList.userPKisExit(user_pk=reply_application_form.userPk):
            return False
        signature = reply_application_form.signature
        user_pk = reply_application_form.userPk
        info = reply_application_form.getInfo()
        return CipherSuites.verify(pk=user_pk, signature=signature, message=str(info).encode("utf-8"))

    # 处理申请书回复消息
    def replyApplyJoin(self, pub, current_main_node_count,
                       storage_of_temp: StorageOfTemp,
                       reply_application_form: ReplyApplicationForm):
        # 验证签名
        if self.verifyReplyApplicationFormSignature(reply_application_form=reply_application_form):
            # 是否超过规定时间
            current_time = STime.getTimestamp()
            time_span = current_time - reply_application_form.startTime
            # 检测暂存的所有新节点申请信息，发现有超过时间的，删除，并修改申请标识
            i = 0
            for manager_of_reply_new_node_i in self.managerOfReplyNewNodeList:
                if manager_of_reply_new_node_i.startTime - current_time > AUDIT_TIME:
                    del self.managerOfReplyNewNodeList[i]
                    storage_of_temp.modifyStateOfNewNode(db_id=manager_of_reply_new_node_i.dbId, is_audit=4)

                else:
                    i += 1

            # 未超过规定时间
            if time_span < AUDIT_TIME:
                # 将该节点的信息加入统计数据中
                i = 0
                for manager_of_reply_new_node_i in self.managerOfReplyNewNodeList:
                    if manager_of_reply_new_node_i.newNodeId == reply_application_form.newNodeId:
                        # 同意
                        if reply_application_form.isAgree == 1:
                            manager_of_reply_new_node_i.addAgreeNode(node_id=reply_application_form.newNodeId,
                                                                     signature=reply_application_form.signature,
                                                                     reply_time=reply_application_form.replyTime,
                                                                     user_pk=reply_application_form.userPk)
                        elif reply_application_form.isAgree == 0:
                            manager_of_reply_new_node_i.addDisagree()

                        # 统计结果同意的数量或者不同意的数量是否超过一半
                        if len(manager_of_reply_new_node_i.agreeList) >= current_main_node_count:
                            # 达到要求后，全网广播，修改数据标识
                            message = NetworkMessage(mess_type=NetworkMessageType.NewNodeJoin,
                                                     message=manager_of_reply_new_node_i.getAgreeInfo).getNetMessage()
                            storage_of_temp.modifyStateOfNewNode(db_id=manager_of_reply_new_node_i.dbId, is_audit=3)
                            pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfJoin(),
                                            message=str(message).encode("utf-8"))
                            del self.managerOfReplyNewNodeList[i]
                        # 申请失败,修改数据标识，删除数据
                        if manager_of_reply_new_node_i.disagreeCount > current_main_node_count:
                            storage_of_temp.modifyStateOfNewNode(db_id=manager_of_reply_new_node_i.dbId, is_audit=4)
                            del self.managerOfReplyNewNodeList[i]

                        break
                    else:
                        i += 1

    # 检测是否达到条件，确认删除节点
    def confirmDelNodes(self, node_del_application_form: NodeDelApplicationForm) -> bool:
        # 验证申请者签名
        info = node_del_application_form.getInfo()
        if not CipherSuites.verify(pk=node_del_application_form.applyUserPk,
                                   signature=node_del_application_form.applySignature,
                                   message=str(info).encode("utf-8")):
            return False
        # 去重
        votes = []
        for vote in node_del_application_form.votes:
            if vote not in votes:
                votes.append(vote)

        total_vote = 1
        for vote in votes:
            if CipherSuites.verify(pk=vote["user_pk"], signature="signature", message=str(info).encode("utf-8")):
                total_vote += 1
        if total_vote >= self.mainNode.mainNodeList.getNodeCount() / 2:
            return True
        else:
            return False
