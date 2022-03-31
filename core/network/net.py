import logging
import threading
import zmq
from ast import literal_eval

from core.consensus.vote import VoteCount
from core.consensus.node_management import NodeManager
from core.consensus.data import ApplicationForm, VoteInformation, WaitGalaxyBlock, ConformationOfGalaxyBlock, \
    NodeDelApplicationForm
from core.node.main_node import MainNode
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_temp import StorageOfTemp
from core.storage.storage_of_galaxy import StorageOfGalaxy
from core.user.user import User
from core.utils.ciphersuites import CipherSuites
from core.utils.system_time import STime
from core.utils.serialization import SerializationBeings, SerializationApplicationForm, SerializationNetworkMessage, \
    SerializationReplyApplicationForm
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
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        logger.info("客户端初始化完成")

    def sendMessageByNodeID(self, node_id, data: bytes):
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        ip = ""
        for main_node in self.mainNodeList.getNodeList():
            if main_node["node_info"]["node_id"] == node_id:
                ip = main_node["node_info"]["node_ip"]
        ip = "tcp://" + ip + ":23334"
        self.socket.connect(ip)
        self.socket.send(data)
        message = self.socket.recv()
        self.socket.disconnect(ip)
        logger.info("消息发送完成，对方ip为" + ip)
        return message

    def sendMessageByMainNodeUserPk(self, user_pk, data: bytes):
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        ip = ""
        for main_node in self.mainNodeList.getNodeList():
            if main_node["node_info"]["user_pk"] == user_pk:
                ip = main_node["node_info"]["node_ip"]
        ip = "tcp://" + ip + ":23334"
        self.socket.connect(ip)
        self.socket.send(data)
        message = self.socket.recv()
        self.socket.disconnect(ip)
        logger.info("消息发送完成，对方ip为" + ip)
        return message

    def sendMessageByIP(self, ip, data: bytes):
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        ip = "tcp://" + ip + ":23334"
        self.socket.connect(ip)
        self.socket.send(data)
        message = self.socket.recv()
        self.socket.disconnect(ip)
        logger.info("消息发送完成，对方ip为" + ip)
        return message


# 订阅消息
# 订阅者
class SUB(threading.Thread):
    def __init__(self, ip, pub: PUB, client: Client, blockListOfBeings: BlockListOfBeings,
                 user: User, node_manager: NodeManager,
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
        self.storageOfGalaxy = storage_of_galaxy
        self.voteCount = vote_count
        self.getEpoch = getEpoch
        self.getElectionPeriod = getElectionPeriod
        self.nodeDelApplicationFormList = node_del_application_form_list

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        ip = "tcp://" + ip + ":23333"
        self.socket.connect(ip)
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getBlockTopicOfBeings())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfJoin())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfApplyJoin())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfApplyDelete())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getBlockTopicOfGalaxy())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfDelete())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getVoteConfirmation())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfProactiveApplyDelete())
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
                    logger.warning(err)
                # 收集其他节点产生的时代区块
                try:
                    if message[
                       0:len(SubscribeTopics.getBlockTopicOfGalaxy())] == SubscribeTopics.getBlockTopicOfGalaxy():
                        conformation_Of_galaxy_message = literal_eval(
                            message[len(SubscribeTopics.getBlockTopicOfGalaxy()):])
                        block_of_galaxy = conformation_Of_galaxy_message["block_of_galaxy"]
                        # 验证签名
                        header = block_of_galaxy.getBlockHeader()
                        if not CipherSuites.verify(pk=header["userPK"][0], signature=header["bodySignature"][0],
                                                   message=block_of_galaxy.body):
                            # 签名验证失败
                            continue
                        votes = conformation_Of_galaxy_message["votes"]
                        total = conformation_Of_galaxy_message["total"]
                        # 计算票数是否符合
                        if total < self.voteCount.getVotesOfGalaxyGenerate(
                                current_election_cycle=self.getElectionPeriod()):
                            continue
                        header = block_of_galaxy.getBlockHeader()
                        total = self.voteCount.getAndVerifyVotes(votes=votes,
                                                                 main_node_id_of_block=header["userPK"][0][0:16],
                                                                 block_id_of_block=header["blockID"],
                                                                 election_period_of_block=header["electionPeriod"])
                        if total < self.voteCount.getVotesOfGalaxyGenerate(
                                current_election_cycle=self.getElectionPeriod()):
                            continue
                        # 广播
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfGalaxy(),
                                             message=str(conformation_Of_galaxy_message).encode("utf-8"))
                        # 存入数据库
                        self.storageOfGalaxy.addBlockOfGalaxy(block_of_galaxy=block_of_galaxy)
                        continue
                except Exception as err:
                    logger.exception(err)
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
                    logger.exception(err)
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
                    logger.exception(err)

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
                            # 添加该删除节点的不产生区块的消息
                            self.mainNode.currentBlockList.addMessageOfNoBlock(
                                empty_block=EmptyBlock(user_pk=del_node_user_pk, epoch=current_epoch))
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
                    logger.exception(err)
                # 投票确认消息
                try:
                    if message[0:len(SubscribeTopics.getVoteConfirmation())] == SubscribeTopics.getVoteConfirmation():
                        vote_info = literal_eval(message[len(SubscribeTopics.getVoteConfirmation()):])
                        main_node_id = vote_info["main_node_id"]
                        block_id = vote_info["block_id"]
                        current_election_period = vote_info["current_election_period"]
                        number_of_vote = vote_info["number_of_vote"]
                        user_pk = vote_info["user_pk"]
                        signature = vote_info["signature"]
                        vote_information = VoteInformation(main_node_id=main_node_id, block_id=block_id,
                                                           election_period=current_election_period,
                                                           number_of_vote=number_of_vote, user_pk=user_pk)
                        vote_information.setSignature(signature)
                        # 验证签名
                        if CipherSuites.verify(pk=user_pk, signature=signature,
                                               message=str(vote_information.getVoteInfo()).encode("utf-8")):
                            # 检测数据库是否存在该组消息
                            if not self.storageOfTemp.voteIsExit(vote_information=vote_information):
                                # 存入数据库
                                self.storageOfTemp.addVotes(vote_information=vote_information)
                                # 广播
                                self.pub.sendMessage(topic=SubscribeTopics.getVoteConfirmation(),
                                                     message=vote_information)
                except Exception as err:
                    logger.warning(err)
            except Exception as err:
                logger.warning(err)


# 监听接受消息
class Server(threading.Thread):
    def __init__(self, user: User, pub: PUB, main_node: MainNode, storage_of_temp: StorageOfTemp,
                 storage_of_galaxy: StorageOfGalaxy, storage_of_beings: StorageOfBeings, node_manager: NodeManager,
                 wait_galaxy_block: WaitGalaxyBlock, vote_count: VoteCount, getEpoch, getElectionPeriod,
                 newBlockOfGalaxy, current_main_node):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:23334")
        self.stopFlag = True
        self.nodeManager = node_manager
        self.pub = pub
        self.mainNode = main_node
        self.mainNodeList = self.mainNode.mainNodeList
        self.storageOfTemp = storage_of_temp
        self.storageOfBeings = storage_of_beings
        self.storageOfGalaxy = storage_of_galaxy
        self.waitGalaxyBlock = wait_galaxy_block
        self.voteCount = vote_count
        self.getEpoch = getEpoch
        self.getElectionPeriod = getElectionPeriod
        self.newBlockOfGalaxy = newBlockOfGalaxy
        self.currentMainNode = current_main_node
        self.user = user
        logger.info("服务端初始化完成")

    def run(self):
        logger.info("服务端启动")
        self.receive()

    def stop(self):
        self.stopFlag = False
        logger.info("服务端关闭")

    def receive(self):
        while self.stopFlag:
            #  Wait for next request from client
            serial_network_message = self.socket.recv()
            logger.info("服务端收到消息")
            logger.info(serial_network_message)
            try:
                network_message = SerializationNetworkMessage.deserialization(serial_network_message)
                mess_type = network_message.messType
                # #获取主节点列表的请求、当前Epoch请求、数据同步的请求不验证签名

                # 获取主节点列表请求
                if mess_type == NetworkMessageType.Get_Main_Node_List:
                    node_list = self.mainNode.mainNodeList.getNodeList()
                    self.socket.send((str(node_list).encode("utf-8")))
                    continue

                # 当前Epoch请求
                if mess_type == NetworkMessageType.Get_Current_Epoch:
                    self.socket.send(str(self.getEpoch()).encode("utf-8"))
                    continue

                # 检查发送方签名，核对对方是否为主节点
                # 签名有效期为八秒
                client_info = network_message.clientInfo
                signature = network_message.signature
                if (STime.getTimestamp() - client_info["send_time"]) > 8:
                    # 超过有效时间
                    logger.info("发送方签名时间超过有效时间，用户公钥：" + client_info["user_pk"])
                    self.socket.send(b'0')
                    continue
                if not self.mainNode.mainNodeList.userPKisExit(user_pk=client_info["user_pk"]):
                    # 发送方不是主节点
                    logger.info("发送方不是主节点，用户公钥：" + client_info["user_pk"])
                    self.socket.send(b'0')
                    continue
                certification_digest = network_message.getClientAndMessageDigest()
                if not CipherSuites.verify(pk=client_info["user_pk"], signature=signature,
                                           message=str(certification_digest).encode("utf-8")):
                    # 签名验证失败
                    logger.info("签名验证失败，用户公钥：" + client_info["user_pk"])
                    self.socket.send(b'0')
                    continue

                # 新节点申请加入消息
                if mess_type == NetworkMessageType.ReplayNewNodeApplicationJoin:
                    reply_application_form = SerializationReplyApplicationForm.deserialization(network_message.message)
                    # 处理回复消息
                    self.nodeManager.replyApplyJoin(reply_application_form)
                    self.socket.send(b'1')
                    continue

                # 投票信息
                if mess_type == NetworkMessageType.Vote_Info:
                    vote_info = network_message.message
                    vote_information = VoteInformation(main_node_id=vote_info["main_node_id"],
                                                       block_id=vote_info["block_id"],
                                                       election_period=vote_info["election_period"],
                                                       number_of_vote=vote_info["number_of_vote"],
                                                       user_pk=vote_info["vote_info"])
                    vote_information.setSignature(signature=vote_info["signature"])
                    # 是否在当前选举阶段的投票信息
                    if vote_information.electionPeriod != self.getElectionPeriod():
                        # 不在当前选举阶段
                        err = [
                            False,
                            "不在当前选举阶段,当前选举阶段为:" + str(self.getElectionPeriod())
                        ]
                        self.socket.send(
                            str(NetworkMessage(mess_type=NetworkMessageType.RECEIVE_CONFIRMATION, message=err)).encode(
                                "utf-8"))
                        self.socket.send(b'0')
                        continue

                    # 验证签名
                    if not CipherSuites.verify(pk=vote_information.userPK, signature=vote_information.signature,
                                               message=str(vote_information.getVoteInfo()).encode("utf-8")):
                        # 投票签名不匹配
                        err = [
                            False,
                            "投票签名不匹配"
                        ]
                        self.socket.send(
                            str(NetworkMessage(mess_type=NetworkMessageType.RECEIVE_CONFIRMATION, message=err)).encode(
                                "utf-8"))
                        self.socket.send(b'0')
                        continue
                    # 检查是否有推荐该区块
                    if not self.waitGalaxyBlock.isExit(block_id=vote_information.blockId):
                        # 当前主节点没有推荐该区块
                        err = [
                            False,
                            "当前主节点没有推荐该区块"
                        ]
                        self.socket.send(
                            str(NetworkMessage(mess_type=NetworkMessageType.RECEIVE_CONFIRMATION, message=err)).encode(
                                "utf-8"))
                        self.socket.send(b'0')
                        continue
                    # 计算票数
                    count = self.voteCount.computeMainUserVote(user_pk=vote_information.userPK,
                                                               current_election_cycle=self.getElectionPeriod())
                    # 减去已经投的票
                    count -= self.voteCount.getVotesConsumedByCurrent(user_pk=vote_information.userPK,
                                                                      current_election_cycle=self.getElectionPeriod())
                    if vote_information.numberOfVote > count:
                        # 超过主节点拥有的最大票数
                        err = [
                            False,
                            "超过投票主节点拥有的最大票数，该主节点还剩余" + str(count) + "票"
                        ]
                        self.socket.send(
                            str(NetworkMessage(mess_type=NetworkMessageType.RECEIVE_CONFIRMATION, message=err)).encode(
                                "utf-8"))
                        self.socket.send(b'0')
                        continue

                    # 存入数据
                    self.waitGalaxyBlock.addVote(vote_info=vote_information)
                    # 广播该投票消息
                    self.pub.sendMessage(topic=SubscribeTopics.getVoteConfirmation(),
                                         message=vote_information.getMessage())
                    # 返回提示
                    info = [
                        True,
                        "投票成功"
                    ]
                    self.socket.send(
                        str(NetworkMessage(mess_type=NetworkMessageType.RECEIVE_CONFIRMATION, message=info)).encode(
                            "utf-8"))
                    # 判断是否达到生产银河区块的条件
                    total = self.waitGalaxyBlock.getTotalOfVotesByBlockId(block_id=vote_information.blockId)
                    if total > self.voteCount.getVotesOfGalaxyGenerate(current_election_cycle=self.getElectionPeriod()):
                        # 广播生成银河区块
                        block_of_galaxy = self.newBlockOfGalaxy(block_id=vote_information.blockId)
                        conformation_of_galaxy_block = ConformationOfGalaxyBlock(block_of_galaxy=block_of_galaxy,
                                                                                 votes=self.waitGalaxyBlock.getVotesByBlockId(
                                                                                     block_id=vote_information.blockId),
                                                                                 total=total).getMessage()
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfGalaxy(),
                                             message=conformation_of_galaxy_block)
                        # 存入数据库
                        self.storageOfGalaxy.addBlockOfGalaxy(block_of_galaxy=block_of_galaxy)
                        self.socket.send(b'1')
            # 其他消息类型
            except Exception as err:
                # 非规定数据结构
                logger.info(err)
                self.socket.send(b'0')
