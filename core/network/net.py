import hashlib
import logging
import threading
import zmq
from ast import literal_eval

from core.consensus.block_generate import NewBlockOfTimes
from core.consensus.vote_compute import VoteCount
from core.consensus.node_management import NodeManager
from core.consensus.data import ApplicationForm, VoteMessage, WaitGalaxyBlock, NodeDelApplicationForm
from core.data.block_of_times import BodyOfTimesBlock
from core.node.main_node import MainNode
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_garbage import StorageOfGarbage
from core.storage.storage_of_temp import StorageOfTemp
from core.storage.storage_of_galaxy import StorageOfGalaxy
from core.user.user import User
from core.utils.ciphersuites import CipherSuites
from core.utils.server_sdk import SDK
from core.utils.system_time import STime
from core.utils.serialization import SerializationBeings, SerializationApplicationForm, SerializationNetworkMessage, \
    SerializationReplyApplicationForm, SerializationVoteMessage, SerializationTimes, SerializationLongTermVoteMessage, \
    SerializationGarbage, SerializationApplicationFormActiveDelete, SerializationReplyApplicationFormActiveDelete
from core.data.network_message import SubscribeTopics, NetworkMessage, NetworkMessageType
from core.data.block_of_beings import BlockListOfBeings, EmptyBlock
from core.data.node_info import MainNodeList, NodeInfo

logger = logging.getLogger("main")


# 订阅消息
# 发布者
# 端口23333
class PUB(threading.Thread):
    def __init__(self):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.name = "pub"
        logger.info("发布者初始化完成")

    def initBind(self):
        self.socket.bind('tcp://*:23333')

    def sendMessage(self, topic: bytes, message):
        self.socket.send(topic + str(message).encode("utf-8"))
        logger.info("已发送广播，主题：" + topic.decode("utf-8"))
        logger.debug(str(message).encode("utf-8"))

    def run(self):
        self.initBind()
        logger.info("发布者进程启动")


# 指定IP发送消息
class Client:
    def __init__(self, main_node_list: MainNodeList):
        self.mainNodeList = main_node_list
        logger.info("客户端初始化完成")

    def sendMessageByNodeID(self, node_id, data: bytes):
        with zmq.Context() as context:
            with context.socket(zmq.REQ) as socket:
                socket.setsockopt(zmq.LINGER, 0)
                socket.setsockopt(zmq.RCVTIMEO, 5000)
                ip = ""
                for main_node in self.mainNodeList.getNodeList():
                    if main_node["node_info"]["node_id"] == node_id:
                        ip = main_node["node_info"]["node_ip"]
                ip = "tcp://" + ip + ":23334"
                socket.connect(ip)
                socket.send(data)
                message = socket.recv()
                logger.info("消息发送完成，对方ip为" + ip)
                return message

    def sendMessageByMainNodeUserPk(self, user_pk, data: bytes):
        with zmq.Context() as context:
            with context.socket(zmq.REQ) as socket:
                socket.setsockopt(zmq.LINGER, 0)
                socket.setsockopt(zmq.RCVTIMEO, 5000)
                ip = ""
                for main_node in self.mainNodeList.getNodeList():
                    if main_node["node_info"]["user_pk"] == user_pk:
                        ip = main_node["node_info"]["node_ip"]
                ip = "tcp://" + ip + ":23334"
                socket.connect(ip)
                socket.send(data)
                message = socket.recv()
                logger.info("消息发送完成，对方公钥为" + user_pk)
                logger.info("消息发送完成，对方ip为" + ip)
                return message

    @staticmethod
    def sendMessageByIP(ip, data: bytes):
        with zmq.Context() as context:
            with context.socket(zmq.REQ) as socket:
                socket.setsockopt(zmq.LINGER, 0)
                socket.setsockopt(zmq.RCVTIMEO, 5000)
                ip = "tcp://" + ip + ":23334"
                socket.connect(ip)
                socket.send(data)
                message = socket.recv()
                logger.info("消息发送完成，对方ip为" + ip)
                return message


# 订阅消息
# 订阅者
class SUB(threading.Thread):
    def __init__(self, ip, pub: PUB, client: Client, blockListOfBeings: BlockListOfBeings,
                 storage_of_garbage: StorageOfGarbage,
                 user: User, node_manager: NodeManager, web_server_sdk: SDK, storage_of_beings: StorageOfBeings,
                 storage_of_galaxy: StorageOfGalaxy, vote_count: VoteCount, getEpoch, getElectionPeriod,
                 main_node: MainNode, reSubscribe, storage_of_temp: StorageOfTemp, node_del_application_form_list):
        super().__init__()
        self.name = str(ip)
        self.reSubscribe = reSubscribe
        self.blockListOfBeings = blockListOfBeings
        self.pub = pub
        self.client = client
        self.mainNode = main_node
        self.user = user
        self.nodeManager = node_manager
        self.storageOfTemp = storage_of_temp
        self.storageOfBeings = storage_of_beings
        self.storageOfGalaxy = storage_of_galaxy
        self.storageOfGarbage = storage_of_garbage
        self.voteCount = vote_count
        self.getEpoch = getEpoch
        self.getElectionPeriod = getElectionPeriod
        self.nodeDelApplicationFormList = node_del_application_form_list
        self.webServerSdk = web_server_sdk

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        ip = "tcp://" + ip + ":23333"
        self.socket.connect(ip)
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getBlockTopicOfBeings())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getBlockTopicOfTimes())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfDelete())

        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfJoin())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfApplyJoin())

        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfApplyDelete())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfDelete())

        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfActiveConfirmDelete())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfActiveApplyDelete())

        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getVoteMessage())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getLongTermVoteMessage())
        self.stopFlag = True
        logger.info("订阅者初始化完成，订阅ip为" + ip)

    def stop(self):
        self.stopFlag = False
        logger.info("订阅者关闭，订阅ip为" + self.name)

    def run(self):
        self.receive()
        logger.info("订阅者启动")

    def receive(self):
        while self.stopFlag:
            try:
                message = self.socket.recv()
                logger.info("订阅者收到消息：")
                logger.debug(message)
                try:
                    # 收集其他节点产生的众生区块
                    if message[
                       0:len(SubscribeTopics.getBlockTopicOfBeings())] == SubscribeTopics.getBlockTopicOfBeings():
                        block_mess = literal_eval(
                            bytes(message[len(SubscribeTopics.getBlockTopicOfBeings()):]).decode("utf-8"))
                        if block_mess["message_type"] == NetworkMessageType.NEW_BLOCK:
                            net_block_dict = block_mess["message"]
                            # 反序列化
                            block = SerializationBeings.deserialization(
                                data_of_beings=str(net_block_dict).encode("utf-8"))
                            # 是否已经存在
                            if self.mainNode.currentBlockList.userPkIsBlock(user_pk=block.getUserPk()[1]):
                                logger.info("区块已经存在，区块id为：" + block.getBlockID())
                                continue
                            # 验证是否在有生成权限的节点内
                            if not self.mainNode.currentMainNode.userPKisExit(user_pk=block.getUserPk()[1]):
                                logger.info("当前节点没有生成权限，用户公钥为：" + block.getUserPk()[1])
                                continue
                            # 签名验证
                            header = block.getBlockHeader()
                            result = True
                            for i in range(len(header["userPK"])):
                                result = result and CipherSuites.verify(pk=header["userPK"][i],
                                                                        signature=header["bodySignature"][i],
                                                                        message=block.body)
                            if result:
                                # 保存
                                self.blockListOfBeings.addBlock(block=block)
                                # 广播消息
                                self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=block_mess)
                                logger.info("已保存区块，区块id为：" + block.getBlockID())
                            else:
                                logger.info("区块签名验证失败，区块id为：" + block.getBlockID())
                        # 本次被选中，但是不生产区块的消息
                        if block_mess["message_type"] == NetworkMessageType.NO_BLOCK:
                            empty_block_dict = block_mess["message"]
                            empty_block = EmptyBlock(user_pk=empty_block_dict["user_pk"],
                                                     epoch=empty_block_dict["epoch"])
                            empty_block.setSignature(empty_block_dict["signature"])
                            # 是否已经存在
                            if self.mainNode.currentBlockList.userPkIsEmptyBlock(user_pk=empty_block.userPk):
                                logger.info("空区块消息已经存在，用户公钥为：" + empty_block.userPk)
                                continue
                            # 验证是否在有生成权限的节点内
                            if not self.mainNode.currentMainNode.userPKisExit(user_pk=empty_block.userPk):
                                logger.info("当前节点没有生成权限，用户公钥为：" + empty_block.userPk)
                                continue
                            # 验证签名
                            if not CipherSuites.verify(pk=empty_block.userPk, signature=empty_block.signature,
                                                       message=str(empty_block.getInfo()).encode("utf-8")):
                                logger.info("签名验证失败，用户公钥为：" + empty_block.userPk)
                                continue
                            self.blockListOfBeings.addMessageOfNoBlock(empty_block=empty_block)
                            self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=block_mess)
                            logger.info("已保存不产生区块消息，该消息用户公钥为：" + empty_block.userPk)
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 收集其他节点产生的时代区块
                try:
                    if message[0:len(SubscribeTopics.getBlockTopicOfTimes())] == SubscribeTopics.getBlockTopicOfTimes():
                        serial_vote_list, serial_block_of_times = literal_eval(
                            bytes(message[len(SubscribeTopics.getBlockTopicOfTimes()):]).decode("utf-8"))
                        vote_message_list = []
                        for vote_i in serial_vote_list:
                            # 判断是长期票还是短期票
                            if "main_user_pk" in vote_i:
                                # 短期票
                                vote_message_list.append(
                                    SerializationVoteMessage.deserialization(str(vote_i).encode("utf-8")))
                            else:
                                # 长期票
                                vote_message_list.append(
                                    SerializationLongTermVoteMessage.deserialization(str(vote_i).encode("utf-8")))
                        if len(vote_message_list) <= 0:
                            logger.info("收到的生成时代区块的投票消息为空")
                            continue
                        # 检测是否已经收到该消息
                        user_pk_list = self.storageOfBeings.getUserPkByBlockId(block_id=vote_message_list[0].blockId)
                        if self.storageOfGalaxy.isExitBlockOfGalaxy(user_pk=vote_message_list[0].toMainNodeUserPk,
                                                                    beings_block_id=vote_message_list[0].blockId,
                                                                    beings_simple_user_pk=user_pk_list[0],
                                                                    beings_main_node_user_pk=user_pk_list[1]):
                            logger.info("该区块已经被选为时代区块")
                            continue
                        block_of_times = SerializationTimes.deserialization(str(serial_block_of_times).encode("utf-8"))
                        body_dict = literal_eval(bytes(block_of_times.body).decode("utf-8"))
                        # 验证票数和签名
                        if not self.voteCount.checkVotesOfGenerateTimesBlock(beings_block_id=body_dict["block_id"],
                                                                             vote_message_list=vote_message_list):
                            logger.info("票数和签名验证失败,未能达到生成时代区块的要求")
                            continue
                        # 验证投票信息与时代区块body中的公钥信息是否相符
                        beings_simple_user_pk, beings_main_node_user_pk = self.storageOfBeings.getUserPkByBlockId(
                            body_dict["block_id"])
                        if body_dict["users_pk"][0] != beings_simple_user_pk:
                            logger.info("时代区块body中的普通用户公钥与众生区块存储的不符")
                            continue
                        if body_dict["users_pk"][1] != beings_main_node_user_pk:
                            logger.info("时代区块body中的主节点用户公钥与众生区块存储的不符")
                            continue
                        # 广播生成时代区块的投票信息
                        logger.info("广播生成时代区块的投票信息")
                        serial_block_of_times = SerializationTimes.serialization(block_of_times)
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfTimes(),
                                             message=[serial_vote_list, serial_block_of_times])
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 收集其他节点产生的垃圾区块
                try:
                    if message[
                       0:len(SubscribeTopics.getBlockTopicOfGarbage())] == SubscribeTopics.getBlockTopicOfGarbage():
                        serial_vote_list, serial_block_of_garbage = literal_eval(
                            bytes(message[len(SubscribeTopics.getBlockTopicOfGarbage()):]).decode("utf-8"))
                        vote_message_list = []
                        for vote_i in serial_vote_list:
                            # 判断是长期票还是短期票
                            if "main_user_pk" in vote_i:
                                # 短期票
                                vote_message_list.append(
                                    SerializationVoteMessage.deserialization(str(vote_i).encode("utf-8")))
                            else:
                                # 长期票
                                vote_message_list.append(
                                    SerializationLongTermVoteMessage.deserialization(str(vote_i).encode("utf-8")))
                        if len(vote_message_list) <= 0:
                            logger.info("收到的生成垃圾区块的投票消息为空")
                            continue
                        # 检测是否已经收到该消息
                        user_pk_list = self.storageOfBeings.getUserPkByBlockId(block_id=vote_message_list[0].blockId)
                        if self.storageOfGarbage.isExitBlockOfGarbage(user_pk=vote_message_list[0].toMainNodeUserPk,
                                                                      beings_block_id=vote_message_list[0].blockId,
                                                                      beings_simple_user_pk=user_pk_list[0],
                                                                      beings_main_node_user_pk=user_pk_list[1]):
                            logger.info("该区块已经被选为垃圾区块")
                            continue
                        block_of_garbage = SerializationGarbage.deserialization(
                            str(serial_block_of_garbage).encode("utf-8"))
                        body_dict = literal_eval(bytes(block_of_garbage.body).decode("utf-8"))
                        # 验证票数和签名
                        if not self.voteCount.checkVotesOfGenerateGarbageBlock(beings_block_id=body_dict["block_id"],
                                                                               vote_message_list=vote_message_list):
                            logger.info("票数和签名验证失败,未能达到生成垃圾区块的要求")
                            continue
                        # 验证投票信息与垃圾区块body中的公钥信息是否相符
                        beings_simple_user_pk, beings_main_node_user_pk = self.storageOfBeings.getUserPkByBlockId(
                            body_dict["block_id"])
                        if body_dict["users_pk"][0] != beings_simple_user_pk:
                            logger.info("垃圾区块body中的普通用户公钥与众生区块存储的不符")
                            continue
                        if body_dict["users_pk"][1] != beings_main_node_user_pk:
                            logger.info("垃圾区块body中的主节点用户公钥与众生区块存储的不符")
                            continue
                        # 广播垃圾时代区块的投票信息
                        logger.info("广播生成时代区块的投票信息")
                        serial_block_of_garbage = SerializationGarbage.serialization(block_of_garbage)
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfGarbage(),
                                             message=[serial_vote_list, serial_block_of_garbage])
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 新节点申请加入 消息
                # 保存到暂存区（以便审核后回复）广播
                try:
                    if message[
                       0:len(SubscribeTopics.getNodeTopicOfApplyJoin())] == SubscribeTopics.getNodeTopicOfApplyJoin():
                        serial_application_form = literal_eval(
                            bytes(message[len(SubscribeTopics.getNodeTopicOfApplyJoin()):]).decode(
                                "utf-8"))
                        application_form = SerializationApplicationForm.deserialization(
                            str(serial_application_form).encode("utf-8"))
                        # 检测是当前主节点申请的
                        if self.user.getUserPKString() == application_form.mainNode["user_pk"]:
                            logger.info("该申请书为当前节点主动申请，新节点用户公钥：" + application_form.newNodeInfo["user_pk"])
                            continue
                        # 保证节点不能同时有多个申请书
                        if self.storageOfTemp.isApplicationForm(
                                new_node_user_pk=application_form.newNodeInfo["user_pk"]):
                            logger.info("该申请书已经存在，新节点用户公钥：" + application_form.newNodeInfo["user_pk"])
                            continue
                        # 验证申请书新节点信息和签名
                        if not CipherSuites.verify(pk=application_form.newNodeInfo["user_pk"],
                                                   signature=application_form.newNodeSignature,
                                                   message=str(application_form.newNodeInfo).encode("utf-8")):
                            logger.info("申请书新节点信息和签名不匹配，新节点用户公钥为：" + application_form.newNodeInfo["user_pk"])
                            continue
                        # 验证新节点对申请书的签名
                        if not CipherSuites.verify(pk=application_form.newNodeInfo["user_pk"],
                                                   signature=application_form.applicationSignatureByNewNode,
                                                   message=str(application_form.application["content"]).encode(
                                                       "utf-8")):
                            logger.info("新节点对申请书的签名不匹配,新节点用户公钥" + application_form.newNodeInfo["user_pk"])
                            continue
                        # 验证主节点对申请书的签名
                        if not CipherSuites.verify(pk=application_form.mainNode["user_pk"],
                                                   signature=application_form.mainNode["application_signature"],
                                                   message=str(application_form.application).encode("utf-8")):
                            logger.info("主节点对申请书的签名不匹配,新节点用户公钥" + application_form.newNodeInfo["user_pk"])
                            continue
                        # 广播
                        self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyJoin(),
                                             message=serial_application_form)
                        # 保存
                        self.storageOfTemp.insertApplicationFormByOtherMainNode(application_form)
                        logger.info("已保存申请书信息,新节点用户公钥" + application_form.newNodeInfo["user_pk"])
                        continue
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 新节点确认加入主节点消息
                try:
                    if message[0:len(SubscribeTopics.getNodeTopicOfJoin())] == SubscribeTopics.getNodeTopicOfJoin():
                        serial_application_form, list_of_serial_reply_application_form = \
                            literal_eval(bytes(message[len(SubscribeTopics.getNodeTopicOfJoin()):]).decode("utf-8"))
                        list_of_reply_application_form = []
                        application_form = SerializationApplicationForm.deserialization(
                            str(serial_application_form).encode("utf-8"))
                        node_info = application_form.newNodeInfo
                        # 检测该节点是否已经是主节点
                        if self.mainNode.mainNodeList.userPKisExit(node_info["user_pk"]):
                            logger.info("当前节点已经存在，节点用户公钥为：" + node_info["user_pk"])
                            continue
                        new_node = NodeInfo(node_id=node_info["node_id"], user_pk=node_info["user_pk"],
                                            node_ip=node_info["node_ip"], create_time=node_info["create_time"],
                                            server_url=node_info["server_url"])
                        new_node.setNodeSignature(application_form.newNodeSignature)
                        for serial_reply_application_form in list_of_serial_reply_application_form:
                            reply_application_form = SerializationReplyApplicationForm.deserialization(
                                serial_reply_application_form)
                            list_of_reply_application_form.append(reply_application_form)
                        # 验证新节点信息和签名
                        if not CipherSuites.verify(pk=new_node.userPk, signature=new_node.nodeSignature,
                                                   message=str(new_node.getInfo()).encode("utf-8")):
                            logger.info("新节点签名不匹配，新节点公钥：" + new_node.userPk)
                            continue
                        # 验证所有同意节点的时间和签名
                        if self.nodeManager.verifyAgreeInfo(application_form=application_form,
                                                            reply_application_form_list=list_of_reply_application_form):
                            # 全网广播节点加入确认消息
                            self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfJoin(),
                                                 message=[serial_application_form,
                                                          list_of_serial_reply_application_form])
                            # 将新节点加入数据库
                            # 检测主节点列表中是否已经有该节点
                            if not self.mainNode.mainNodeList.userPKisExit(user_pk=new_node.userPk):
                                self.mainNode.mainNodeList.addMainNode(node_info=new_node)
                                logger.info("新节点已加入，节点信息为：")
                                logger.info(new_node.getInfo())
                                # 重新计算订阅列表，重新创建32个订阅链接
                                self.reSubscribe()
                            else:
                                logger.info("节点已经存在，节点ID为：" + new_node.nodeId)
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 申请删除主节点消息
                # 被选中，但是没有产生区块
                # 注意：此处应该先检测投票数量是否符合条件，若投票数量符合条件，则直接删除节点，若不符合条件，再考虑其他情况
                try:
                    if message[
                       0:len(
                           SubscribeTopics.getNodeTopicOfApplyDelete())] == SubscribeTopics.getNodeTopicOfApplyDelete():
                        node_del_application_form_mess = literal_eval(bytes(
                            message[len(SubscribeTopics.getNodeTopicOfApplyDelete()):]).decode("utf-8"))
                        del_node_id = node_del_application_form_mess["del_node_id"]
                        del_node_user_pk = node_del_application_form_mess["del_node_user_pk"]
                        current_epoch = node_del_application_form_mess["current_epoch"]
                        apply_user_pk = node_del_application_form_mess["apply_user_pk"]
                        apply_signature = node_del_application_form_mess["apply_signature"]
                        votes = node_del_application_form_mess["votes"]
                        node_del_application_form = NodeDelApplicationForm(del_node_id=del_node_id,
                                                                           del_user_pk=del_node_user_pk,
                                                                           current_epoch=current_epoch)
                        node_del_application_form.setApplySignature(apply_signature)
                        node_del_application_form.setApplyUserPk(apply_user_pk)
                        # 检测是否有该节点，没有说明已收到过此消息，已经删除
                        if not self.mainNode.mainNodeList.userPKisExit(user_pk=del_node_user_pk):
                            continue
                        # 检测申请节点是否有申请权限
                        if not self.mainNode.currentMainNode.userPKisExit(user_pk=apply_user_pk):
                            continue
                        # 验证申请节点签名
                        if not CipherSuites.verify(pk=apply_user_pk, signature=apply_signature,
                                                   message=(str(node_del_application_form.getInfo()).encode("utf-8"))):
                            continue
                        # 检测申请书的投票数量是否达到标准
                        if self.nodeManager.confirmDelNodes(node_del_application_form=node_del_application_form):
                            logger.info("确认删除节点，节点用户公钥为:" + del_node_user_pk)
                            # 添加该删除节点的不产生区块的消息
                            self.mainNode.currentBlockList.addMessageOfNoBlock(
                                empty_block=EmptyBlock(user_pk=del_node_user_pk, epoch=current_epoch))
                            logger.info("已添加不产生区块的消息")
                            # 删除节点
                            self.mainNode.mainNodeList.delMainNodeById(node_id=del_node_id)
                            self.reSubscribe()
                            continue
                        # 检测申请被删除的节点当前是否应该生成区块
                        if not self.mainNode.currentMainNode.userPKisExit(user_pk=del_node_user_pk):
                            continue
                        # 检测自己是否收到该区块
                        if self.mainNode.currentBlockList.userPkIsExit(user_pk=del_node_user_pk):
                            if self.mainNode.currentBlockList.userPkIsBlock(user_pk=del_node_user_pk):
                                block = self.mainNode.currentBlockList.getBlockByUserPk(user_pk=del_node_user_pk)
                                network_message = NetworkMessage(NetworkMessageType.NEW_BLOCK, message=block)
                                network_message.setClientInfo(user_pk=self.user.getUserPKString())
                                signature = self.user.sign(
                                    message=str(network_message.getClientAndMessageDigest()).encode("utf-8"))
                                network_message.setSignature(signature)
                                serial_network_message = SerializationNetworkMessage.serialization(network_message)
                                self.client.sendMessageByNodeID(node_id=apply_user_pk[0:16],
                                                                data=str(serial_network_message).encode("utf-8"))
                            else:
                                # 不产生区块的消息
                                network_message = NetworkMessage(NetworkMessageType.NO_BLOCK,
                                                                 message=self.mainNode.currentBlockList.getMessageOfNoBlock(
                                                                     user_pk=del_node_user_pk).getMessage())
                                network_message.setClientInfo(user_pk=self.user.getUserPKString())
                                signature = self.user.sign(
                                    message=str(network_message.getClientAndMessageDigest()).encode("utf-8"))
                                network_message.setSignature(signature)
                                serial_network_message = SerializationNetworkMessage.serialization(network_message)
                                self.client.sendMessageByNodeID(node_id=apply_user_pk[0:16],
                                                                data=str(serial_network_message).encode("utf-8"))
                        else:
                            # 检测是否是已经收到过该广播消息
                            is_receive = False
                            for node_del_application_form in self.nodeDelApplicationFormList:
                                if del_node_id == node_del_application_form.delNodeId:
                                    is_receive = True
                                    is_new = False
                                    for vote in votes:
                                        # 加入收集表中没有的签名数据
                                        if node_del_application_form.userPkIsVotes(user_pk=vote["user_pk"]):
                                            continue
                                        # 验证签名
                                        if not CipherSuites.verify(pk=vote["user_pk"], signature=vote["signature"],
                                                                   message=str(
                                                                       node_del_application_form.getInfo()).encode(
                                                                       "utf-8")):
                                            continue
                                        node_del_application_form.addVotes(user_pk=vote["user_pk"],
                                                                           signature=vote["signature"])
                                        is_new = True
                                    # 添加新数据，再次广播
                                    if is_new:
                                        self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyDelete(),
                                                             message=node_del_application_form.getMessage())
                            # 没收到该广播消息
                            if not is_receive:
                                self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyDelete(),
                                                     message=node_del_application_form.getMessage())
                                self.nodeDelApplicationFormList.append(node_del_application_form)
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 主动申请删除主节点的消息
                # 保存到暂存区（以便审核后回复）广播
                try:
                    if message[
                       0:len(
                           SubscribeTopics.getNodeTopicOfActiveApplyDelete())] == SubscribeTopics.getNodeTopicOfActiveApplyDelete():
                        serial_application_form_active_delete = literal_eval(
                            bytes(message[len(SubscribeTopics.getNodeTopicOfActiveApplyDelete()):]).decode(
                                "utf-8"))
                        application_form_active_delete = SerializationApplicationFormActiveDelete.deserialization(
                            str(serial_application_form_active_delete).encode("utf-8"))
                        # 检测是当前主节点申请的
                        if self.user.getUserPKString() == application_form_active_delete.applyMainNode["user_pk"]:
                            logger.info("该申请书为当前节点主动申请，申请删除的节点ID为：" + application_form_active_delete.delNodeId)
                            continue
                        # 检测是否已经存在
                        if self.storageOfTemp.isApplicationFormActiveDelete(
                                del_node_id=application_form_active_delete.delNodeId,
                                application_start_time=application_form_active_delete.application["start_time"],
                                apply_user_pk=application_form_active_delete.applyMainNode["user_pk"]):
                            logger.info("申请书已存在")
                            logger.info(application_form_active_delete.getInfo())
                            continue
                        # 验证申请书新节点信息和签名
                        if not CipherSuites.verify(pk=application_form_active_delete.applyMainNode["user_pk"],
                                                   signature=application_form_active_delete.applyMainNode["signature"],
                                                   message=str(application_form_active_delete.getInfo()).encode(
                                                       "utf-8")):
                            logger.info("申请书签名不匹配")
                            logger.info(application_form_active_delete.applyMainNode)
                            continue
                        # 保存
                        self.storageOfTemp.insertApplicationFormActiveDeleteOfOther(application_form_active_delete)
                        logger.info("已保存申请书信息")
                        logger.info(application_form_active_delete.getInfo())
                        # 广播
                        self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfActiveApplyDelete(),
                                             message=serial_application_form_active_delete)
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 主动删除节点确认消息
                try:
                    if message[
                       0:len(
                           SubscribeTopics.getNodeTopicOfActiveConfirmDelete())] == SubscribeTopics.getNodeTopicOfActiveConfirmDelete():
                        serial_application_form_active_delete, list_of_serial_reply_application_form_active_delete = \
                            literal_eval(
                                bytes(message[len(SubscribeTopics.getNodeTopicOfActiveConfirmDelete()):]).decode(
                                    "utf-8"))

                        list_of_reply_application_form_active_delete = []
                        application_form_active_delete = SerializationApplicationFormActiveDelete.deserialization(
                            str(serial_application_form_active_delete).encode("utf-8"))
                        # 检测该节点是否存在
                        if not self.mainNode.mainNodeList.nodeIdIsExit(
                                node_id=application_form_active_delete.delNodeId):
                            continue

                        for serial_reply_application_form_active_delete in list_of_serial_reply_application_form_active_delete:
                            reply_application_form = SerializationReplyApplicationFormActiveDelete.deserialization(
                                str(serial_reply_application_form_active_delete).encode("utf-8"))
                            list_of_reply_application_form_active_delete.append(reply_application_form)

                        # 验证所有同意节点的时间和签名
                        if self.nodeManager.verifyAgreeInfoOfActiveDelete(
                                application_form_active_delete=application_form_active_delete,
                                reply_application_form_active_delete_list=list_of_reply_application_form_active_delete):
                            # 删除主节点
                            self.mainNode.mainNodeList.delMainNodeById(node_id=application_form_active_delete.delNodeId)
                            # 重新订阅
                            self.reSubscribe()
                            # 全网广播节点加入确认消息
                            self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfActiveConfirmDelete(),
                                                 message=[serial_application_form_active_delete,
                                                          list_of_serial_reply_application_form_active_delete])
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 短期票投票消息
                try:
                    if message[0:len(SubscribeTopics.getVoteMessage())] == SubscribeTopics.getVoteMessage():
                        vote_message_bytes = literal_eval(message[len(SubscribeTopics.getVoteMessage()):])
                        vote_message = SerializationVoteMessage.deserialization(vote_message_bytes)
                        # 检测是否已经存在该投票消息
                        if self.storageOfTemp.isExitVoteDigest(election_period=vote_message.electionPeriod,
                                                               block_id=vote_message.blockId,
                                                               vote_message_digest=hashlib.md5(
                                                                   str(vote_message.getVoteMessage()).encode(
                                                                       "utf-8")).hexdigest()):
                            logger.info("投票信息已经存在")
                            logger.info("推荐区块ID为" + vote_message.blockId)
                            continue
                        # 验证签名
                        if not CipherSuites.verify(pk=vote_message.mainUserPk, signature=vote_message.getSignature(),
                                                   message=str(vote_message.getVoteInfo()).encode("utf-8")):
                            logger.warning("签名验证失败")
                            logger.warning(vote_message.getVoteMessage())
                            continue
                        # 验证主节点票数是否足够 增加主节点已使用的票数
                        main_node_vote = self.storageOfTemp.getMainNodeVoteByMainNodeUserPk(
                            main_node_user_pk=vote_message.mainUserPk)
                        if (main_node_vote["total_vote"] - main_node_vote["used_vote"]) < vote_message.numberOfVote:
                            logger.warning("申请的主节点剩余票数不足")
                            logger.warning(vote_message.getVoteMessage())
                        else:
                            self.storageOfTemp.addUsedVoteByNodeUserPk(vote=vote_message.numberOfVote,
                                                                       main_node_user_pk=vote_message.mainUserPk)
                        # 该短期票投票是否是针对当前主节点推荐的区块
                        if self.webServerSdk.isExitTimesBlockQueueByBlockId(
                                vote_message.blockId) and self.user.getUserPKString() == vote_message.toMainNodeUserPk and int(
                            vote_message.voteType) == 1:
                            self.webServerSdk.addVoteOfTimesBlockQueue(beings_block_id=vote_message.blockId,
                                                                       vote_message=vote_message)
                        if self.webServerSdk.isExitGarbageBlockQueueByBlockId(
                                vote_message.blockId) and self.user.getUserPKString() == vote_message.toMainNodeUserPk and int(
                            vote_message.voteType) == 2:
                            self.webServerSdk.addVoteOfGarbageBlockQueue(beings_block_id=vote_message.blockId,
                                                                         vote_message=vote_message)
                            # 广播
                        self.pub.sendMessage(topic=SubscribeTopics.getVoteMessage(),
                                             message=SerializationVoteMessage.serialization(vote_message=vote_message))
                        logger.debug("广播完成")
                except Exception as err:
                    logger.error(err, exc_info=True)

                # 长期票投票消息
                try:
                    if message[
                       0:len(SubscribeTopics.getLongTermVoteMessage())] == SubscribeTopics.getLongTermVoteMessage():
                        long_term_vote_message_bytes = literal_eval(
                            message[len(SubscribeTopics.getLongTermVoteMessage()):])
                        long_term_vote_message = SerializationLongTermVoteMessage.deserialization(
                            long_term_vote_message_bytes)
                        # 检测是否已经存在该投票消息
                        if self.storageOfTemp.isExitVoteDigest(election_period=long_term_vote_message.electionPeriod,
                                                               block_id=long_term_vote_message.blockId,
                                                               vote_message_digest=hashlib.md5(
                                                                   str(long_term_vote_message.getVoteMessage()).encode(
                                                                       "utf-8")).hexdigest()):
                            logger.info("投票信息已经存在")
                            logger.info("推荐区块ID为" + long_term_vote_message.blockId)
                            continue
                        # 验证签名
                        if not CipherSuites.verify(pk=long_term_vote_message.simpleUserPk,
                                                   signature=long_term_vote_message.getSignature(),
                                                   message=str(long_term_vote_message.getVoteInfo()).encode("utf-8")):
                            logger.warning("签名验证失败")
                            logger.warning(long_term_vote_message.getVoteMessage())
                            continue
                        # 验证主节点票数是否足够 增加主节点已使用的票数
                        simple_user_permanent_vote = self.storageOfTemp.getSimpleUserPermanentVoteByUserPk(
                            simple_user_pk=long_term_vote_message.simpleUserPk)
                        if (simple_user_permanent_vote["total_vote"] - simple_user_permanent_vote[
                            "used_vote"]) < long_term_vote_message.numberOfVote:
                            logger.warning("剩余票数不足")
                            logger.warning(long_term_vote_message.getVoteMessage())
                        else:
                            self.storageOfTemp.addUsedPermanentVoteOfSimpleUser(
                                vote=long_term_vote_message.numberOfVote,
                                simple_user_pk=long_term_vote_message.simpleUserPk)
                        # 该投票是否是针对当前主节点推荐的区块
                        # 该长期票投票是否是针对当前主节点推荐的区块
                        to_main_node_info = self.mainNode.mainNodeList.getMainNodeByNodeId(
                            node_id=long_term_vote_message.toMainNodeId)
                        to_main_node_user_pk = to_main_node_info["node_info"]["user_pk"]
                        if self.webServerSdk.isExitTimesBlockQueueByBlockId(
                                long_term_vote_message.blockId) and self.user.getUserPKString() == to_main_node_user_pk and long_term_vote_message.voteType == 1:
                            self.webServerSdk.addPermanentVoteOfTimesBlockQueue(
                                beings_block_id=long_term_vote_message.blockId,
                                long_term_vote_message=long_term_vote_message)
                        if self.webServerSdk.isExitGarbageBlockQueueByBlockId(
                                long_term_vote_message.blockId) and self.user.getUserPKString() == to_main_node_user_pk and long_term_vote_message.voteType == 2:
                            self.webServerSdk.addPermanentVoteOfGarbageBlockQueue(
                                beings_block_id=long_term_vote_message.blockId,
                                long_term_vote_message=long_term_vote_message)
                        # 广播
                        self.pub.sendMessage(topic=SubscribeTopics.getLongTermVoteMessage(),
                                             message=SerializationLongTermVoteMessage.serialization(
                                                 long_term_vote_message=long_term_vote_message))
                        logger.debug("长期票投票消息广播完成")
                except Exception as err:
                    logger.error(err, exc_info=True)

            except Exception as err:
                logger.error(err, exc_info=True)


# 监听接受消息
class Server(threading.Thread):
    def __init__(self, user: User, pub: PUB, main_node: MainNode, storage_of_temp: StorageOfTemp,
                 node_manager: NodeManager, vote_count: VoteCount, getEpoch, getElectionPeriod):
        super().__init__()
        self.stopFlag = True
        self.nodeManager = node_manager
        self.pub = pub
        self.mainNode = main_node
        self.mainNodeList = self.mainNode.mainNodeList
        self.storageOfTemp = storage_of_temp
        self.voteCount = vote_count
        self.getEpoch = getEpoch
        self.getElectionPeriod = getElectionPeriod
        self.user = user

        self.workerUrl = "inproc://workers"  # 内部使用
        self.context = zmq.Context(io_threads=50)
        self.server = self.context.socket(zmq.XREP)
        self.server.bind("tcp://*:23334")
        self.workers = self.context.socket(zmq.XREQ)
        self.workers.bind(self.workerUrl)
        for i in range(0, 8):
            threading.Thread(target=self.worker, args=(self.workerUrl, self.context, i)).start()
        logger.info("服务端初始化完成")

    def worker(self, inner_url, context, thread_i):
        sock = context.socket(zmq.REP)
        sock.connect(inner_url)
        while self.stopFlag:
            #  Wait for next request from client
            serial_network_message = sock.recv()
            logger.info("服务端收到消息," + str(thread_i) + "号线程。")
            logger.info(serial_network_message)
            try:
                network_message = SerializationNetworkMessage.deserialization(serial_network_message)
                mess_type = network_message.messType
                # #获取主节点列表的请求、当前Epoch请求、数据同步的请求不验证签名

                # 获取主节点列表请求
                if mess_type == NetworkMessageType.Get_Main_Node_List:
                    node_list = self.mainNode.mainNodeList.getNodeList()
                    sock.send((str(node_list).encode("utf-8")))
                    continue

                # 当前Epoch请求
                if mess_type == NetworkMessageType.Get_Current_Epoch:
                    sock.send(str(self.getEpoch()).encode("utf-8"))
                    continue

                # 检查发送方签名，核对对方是否为主节点
                # 签名有效期为八秒
                client_info = network_message.clientInfo
                signature = network_message.signature
                if (STime.getTimestamp() - int(client_info["send_time"])) > 8:
                    # 超过有效时间
                    logger.info("发送方签名时间超过有效时间，用户公钥：" + client_info["user_pk"])
                    sock.send(b'0')
                    continue
                if not self.mainNode.mainNodeList.userPKisExit(user_pk=client_info["user_pk"]):
                    # 发送方不是主节点
                    logger.info("发送方不是主节点，用户公钥：" + client_info["user_pk"])
                    sock.send(b'0')
                    continue
                certification_digest = network_message.getClientAndMessageDigest()
                if not CipherSuites.verify(pk=client_info["user_pk"], signature=signature,
                                           message=str(certification_digest).encode("utf-8")):
                    # 签名验证失败
                    logger.info("签名验证失败，用户公钥：" + client_info["user_pk"])
                    sock.send(b'0')
                    continue
                # 新节点申请加入回复消息
                if mess_type == NetworkMessageType.ReplayNewNodeApplicationJoin:
                    reply_application_form = SerializationReplyApplicationForm.deserialization(network_message.message)
                    # 处理回复消息
                    self.nodeManager.replyApplyJoin(reply_application_form)
                    sock.send(b'1')
                    continue
                # 主动申请删除节点的回复消息
                if mess_type == NetworkMessageType.ReplyNodeActiveDeleteApplication:
                    reply_application_form_active_delete = SerializationReplyApplicationFormActiveDelete.deserialization(
                        network_message.message)
                    # 处理回复消息
                    self.nodeManager.replyNodeActiveDelete(
                        reply_application_form_active_delete=reply_application_form_active_delete)
                    sock.send(b'1')
                    continue
            # 其他消息类型
            except Exception as err:
                # 非规定数据结构
                logger.error(err, exc_info=True)
                sock.send(b'0')

    def run(self):
        logger.info("服务端启动")
        self.receive()

    def stop(self):
        self.stopFlag = False
        logger.info("服务端关闭")

    def receive(self):
        zmq.device(zmq.QUEUE, self.server, self.workers)
