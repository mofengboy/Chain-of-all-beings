import logging

from core.consensus.data import ReplyApplicationForm, NodeDelApplicationForm, ApplicationForm, \
    ReplyApplicationFormActiveDelete, ApplicationFormActiveDelete
from core.utils.ciphersuites import CipherSuites
from core.utils.serialization import SerializationReplyApplicationForm, SerializationReplyApplicationFormActiveDelete
from core.utils.system_time import STime
from core.user.user import User
from core.storage.storage_of_temp import StorageOfTemp
from core.node.main_node import MainNode
from core.consensus.constants import AUDIT_TIME

logger = logging.getLogger("main")


class NodeManager:
    def __init__(self, user: User, main_node: MainNode, storage_of_temp: StorageOfTemp):
        self.mainNode = main_node
        self.user = user
        self.storageOfTemp = storage_of_temp

    # 获取新节点加入要求主节点同意的数量
    def getCountOfNewNodeJoin(self):
        return int(self.mainNode.mainNodeList.getNodeCount() / 2)

    # 获取主节点主动删除要求主节点同意的数量
    def getCountOfNodeActiveDelete(self):
        return int(self.mainNode.mainNodeList.getNodeCount() / 2)

    # 验证新节点加入回复信息中同意节点列表及其签名
    def verifyAgreeInfo(self, application_form: ApplicationForm,
                        reply_application_form_list: [ReplyApplicationForm]) -> bool:
        # 检测是否超过时间
        start_time = application_form.application["start_time"]
        current_time = STime.getTimestamp()
        if current_time - start_time > AUDIT_TIME:
            return False
        # 验证所有同意节点的时间和签名
        i = 1
        for reply_application_form in reply_application_form_list:
            if reply_application_form.isAgree != 1:
                continue
            # 验证申请书回复消息的节点信息是否与申请书的节点信息匹配
            if not (application_form.newNodeId == reply_application_form.newNodeId and
                    application_form.application["start_time"] == reply_application_form.startTime):
                continue
            # 验证签名
            if CipherSuites.verify(pk=reply_application_form.userPk, signature=reply_application_form.signature,
                                   message=str(reply_application_form.getInfo).encode("utf-8")):
                i += 1
        if i >= self.getCountOfNewNodeJoin():
            return True
        return False

    # 验证新节点加入回复信息中同意节点列表及其签名
    def verifyAgreeInfoOfActiveDelete(self, application_form_active_delete: ApplicationFormActiveDelete,
                                      reply_application_form_active_delete_list: list[
                                          ReplyApplicationFormActiveDelete]) -> bool:
        # 检测是否超过时间
        start_time = application_form_active_delete.application["start_time"]
        current_time = STime.getTimestamp()
        if current_time - start_time > AUDIT_TIME:
            logger.warning("超过规定时间")
            logger.warning(application_form_active_delete.getInfo())
            return False
        # 验证所有同意节点的时间和签名
        i = 1
        for reply_application_form_active_delete in reply_application_form_active_delete_list:
            if reply_application_form_active_delete.isAgree != 1:
                continue
            # 验证申请书回复消息的节点信息是否与申请书的节点信息匹配
            if not (application_form_active_delete.delNodeId == reply_application_form_active_delete.delNodeId and
                    application_form_active_delete.application[
                        "start_time"] == reply_application_form_active_delete.startTime):
                logger.warning("申请书时间与回复申请书时间不匹配")
                logger.warning(application_form_active_delete.getInfo())
                logger.warning(reply_application_form_active_delete.getInfo())
                continue
            # 验证签名
            if CipherSuites.verify(pk=reply_application_form_active_delete.userPk,
                                   signature=reply_application_form_active_delete.signature,
                                   message=str(reply_application_form_active_delete.getInfo).encode("utf-8")):
                i += 1
        if i >= self.getCountOfNodeActiveDelete():
            return True
        return False

    # 验证申请书回复信息签名
    @staticmethod
    def verifyReplyApplicationFormSignature(reply_application_form: ReplyApplicationForm):
        signature = reply_application_form.signature
        user_pk = reply_application_form.userPk
        info = reply_application_form.getInfo()
        return CipherSuites.verify(pk=user_pk, signature=signature, message=str(info).encode("utf-8"))

    # 处理新起点加入申请书回复消息
    def replyApplyJoin(self, reply_application_form: ReplyApplicationForm):
        # 检测该公钥是否在主节点列表
        if not self.mainNode.mainNodeList.userPKisExit(user_pk=reply_application_form.userPk):
            return False
        # 是否超过规定时间
        time_span = STime.getTimestamp() - int(reply_application_form.startTime)
        if time_span > AUDIT_TIME:
            return False
        # 验证签名
        if not self.verifyReplyApplicationFormSignature(reply_application_form=reply_application_form):
            return False
        # 检测数据库中是否已经存在该条回复消息
        if self.storageOfTemp.isApplicationFormReply(new_node_id=reply_application_form.newNodeId,
                                                     main_user_pk=reply_application_form.userPk,
                                                     start_time=reply_application_form.startTime):
            return False
        # 是否为同意消息
        if reply_application_form.isAgree == 1:
            # 保存回复消息
            self.storageOfTemp.insertApplicationFormReply(reply_application_form)
            # 增加同意消息数量
            self.storageOfTemp.addAgreeCount(new_node_id=reply_application_form.newNodeId, count=1)
        return True

    # 处理主动删除节点申请书回复消息
    def replyNodeActiveDelete(self, reply_application_form_active_delete: ReplyApplicationFormActiveDelete):
        # 检测申请用户公钥是否在主节点列表
        if not self.mainNode.mainNodeList.userPKisExit(user_pk=reply_application_form_active_delete.userPk):
            logger.warning("不在主节点列表")
            logger.warning(reply_application_form_active_delete.userPk)
            return False
        # 是否超过规定时间
        time_span = STime.getTimestamp() - int(reply_application_form_active_delete.startTime)
        if time_span > AUDIT_TIME:
            logger.warning("超过规定时间")
            logger.warning(reply_application_form_active_delete.startTime)
            return False
        # 验证签名
        if not CipherSuites.verify(pk=reply_application_form_active_delete.userPk,
                                   signature=reply_application_form_active_delete.signature,
                                   message=str(reply_application_form_active_delete.getInfo()).encode("utf-8")):
            logger.warning("签名验证失败")
            logger.warning(reply_application_form_active_delete.getInfo())
            return False
        # 检测数据库中是否已经存在该条回复消息
        if self.storageOfTemp.isApplicationFormActiveDelete(del_node_id=reply_application_form_active_delete.delNodeId,
                                                            application_start_time=reply_application_form_active_delete.startTime,
                                                            apply_user_pk=reply_application_form_active_delete.applyUserPk):
            logger.warning("该回复消息已经收到")
            logger.warning(reply_application_form_active_delete.getInfo())
            return False
        # 是否为同意消息
        if reply_application_form_active_delete.isAgree == 1:
            # 保存回复消息
            self.storageOfTemp.insertApplicationFormActiveDeleteReply(
                reply_application_form_active_delete=reply_application_form_active_delete)
            # 增加同意消息数量
            self.storageOfTemp.addAgreeCountOfNodeActiveDelete(
                del_node_id=reply_application_form_active_delete.delNodeId, count=1)
        return True

    # 检测申请书回复信息
    # 若超过规定申请时间，则删除该节点的申请书
    def isTimeReplyApplicationForm(self, new_node_id):
        application_form = self.storageOfTemp.getApplicationFormByNodeId(new_node_id)
        # 是否在规定时间内
        time_span = STime.getTimestamp() - int(application_form.application["start_time"])
        if time_span > AUDIT_TIME:
            # 取消该申请书
            self.storageOfTemp.delApplicationFormByNodeId(new_node_id)
            return False
        return True

    # 检测申请书回复信息
    # 若超过规定申请时间，则删除该节点的申请书
    def isTimeReplyApplicationFormActiveDelete(self, del_node_id):
        application_form_active_delete = self.storageOfTemp.getApplicationFormActiveDeleteByNodeId(del_node_id,
                                                                                                   is_audit=0)
        # 是否在规定时间内
        time_span = STime.getTimestamp() - int(application_form_active_delete.application["start_time"])
        if time_span > AUDIT_TIME:
            # 取消该申请书
            self.storageOfTemp.delApplicationFormActiveDeleteByNodeId(del_node_id=del_node_id, is_audit=0)
            return False
        return True

    # 检测申请书回复信息
    # 若在规定时间以内，且同意该节点加入的主节点的数量达到规定标准，则该节点正式成为主节点
    def isSuccessReplyApplicationForm(self, new_node_id) -> list[bool, list[ReplyApplicationForm]]:
        agree_count = self.storageOfTemp.getAgreeCountByNodeId(new_node_id)
        if agree_count >= self.getCountOfNewNodeJoin():
            application_form = self.storageOfTemp.getApplicationFormByNodeId(new_node_id)
            # 核对签名数量
            reply_application_form_list = self.storageOfTemp.getListOfReplyApplicationFormInfo(
                new_node_id=application_form.newNodeId,
                start_time=application_form.application["start_time"])
            verify_agree_count = 1
            verify_serial_reply_application_form_list = []
            for reply_application_form in reply_application_form_list:
                if CipherSuites.verify(pk=reply_application_form.userPk, signature=reply_application_form.signature,
                                       message=str(reply_application_form.getInfo).encode("utf-8")):
                    verify_agree_count += 1
                    verify_serial_reply_application_form_list.append(
                        SerializationReplyApplicationForm.serialization(reply_application_form))
            # 核验的同意数量与存储的同意数量不一致
            if verify_agree_count != agree_count:
                logger.warning("核验的主节点同意数量与存储的同意数量不一致")
                logger.warning("核验的主节点同意数量为：" + str(verify_agree_count))
                logger.warning("存储的主节点同意数量为：" + str(agree_count))
                # 将存储的主节点同意数量设置为核验的
                self.storageOfTemp.setAgreeCount(new_node_id, verify_agree_count)
            if verify_agree_count >= self.getCountOfNewNodeJoin():
                return [True, verify_serial_reply_application_form_list]
            else:
                return [False, None]
        else:
            return [False, None]

    # 检测申请书回复信息（主动删除节点）
    # 若在规定时间以内，且同意该节点加入的主节点的数量达到规定标准，则该节点正式成为主节点
    def isSuccessReplyApplicationFormActiveDelete(self, del_node_id) -> list[
        bool, list[ReplyApplicationFormActiveDelete]]:
        agree_count = self.storageOfTemp.getAgreeCountOfActiveDeleteByNodeId(del_node_id, is_audit=0)
        if agree_count >= self.getCountOfNodeActiveDelete():
            application_form_active_delete = self.storageOfTemp.getApplicationFormActiveDeleteByNodeId(del_node_id,
                                                                                                       is_audit=0)
            # 核对签名数量
            reply_application_form_active_delete_list = self.storageOfTemp.getListOfReplyApplicationActiveDelete(
                del_node_id=del_node_id, start_time=application_form_active_delete.application["start_time"])
            verify_agree_count = 1
            verify_serial_reply_application_form_active_delete_list = []
            for reply_application_form_active_delete in reply_application_form_active_delete_list:
                if CipherSuites.verify(pk=reply_application_form_active_delete.userPk,
                                       signature=reply_application_form_active_delete.signature,
                                       message=str(reply_application_form_active_delete.getInfo).encode("utf-8")):
                    verify_agree_count += 1
                    verify_serial_reply_application_form_active_delete_list.append(
                        SerializationReplyApplicationFormActiveDelete.serialization(
                            reply_application_form_active_delete))

            # 核验的同意数量与存储的同意数量不一致
            if verify_agree_count != agree_count:
                logger.warning("核验的主节点同意数量与存储的同意数量不一致")
                logger.warning("核验的主节点同意数量为：" + str(verify_agree_count))
                logger.warning("存储的主节点同意数量为：" + str(agree_count))
                # 将存储的主节点同意数量设置为核验的
                self.storageOfTemp.setAgreeCountOfActiveDelete(del_node_id, verify_agree_count)
            if verify_agree_count >= self.getCountOfNodeActiveDelete():
                return [True, verify_serial_reply_application_form_active_delete_list]
            else:
                return [False, None]
        else:
            return [False, None]

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
            if CipherSuites.verify(pk=vote["user_pk"], signature=vote["signature"], message=str(info).encode("utf-8")):
                total_vote += 1
        if total_vote >= (self.mainNode.mainNodeList.getNodeCount() / 2):
            return True
        else:
            return False
