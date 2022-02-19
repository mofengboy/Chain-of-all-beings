import threading
import zmq
from ast import literal_eval

from core.consensus.vote import VoteCount
from core.consensus.node_management import NodeManager, ManagerOfReplyNewNode
from core.consensus.data import ApplicationForm, VoteInformation, WaitGalaxyBlock, ConformationOfGalaxyBlock, \
    NodeDelApplicationForm
from core.node.main_node import MainNode
from core.storage.storage_of_temp import StorageOfTemp
from core.storage.storage_of_galaxy import StorageOfGalaxy
from core.user.user import User
from core.utils.ciphersuites import CipherSuites
from core.utils.system_time import STime
from core.data.network_message import SubscribeTopics, NetworkMessage, NetworkMessageType
from core.data.block_of_beings import BlockListOfBeings, EmptyBlock
from core.data.node_info import MainNodeList, NodeInfo


# 订阅消息
# 发布者
# 端口23333
class PUB(threading.Thread):
    def __init__(self):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)

    def initBind(self):
        self.socket.bind('tcp://*:23333')

    def sendMessage(self, topic: bytes, message):
        self.socket.send(topic + str(message).encode("utf-8"))

    def run(self):
        self.initBind()


# 指定IP发送消息
class Client:
    def __init__(self, main_node_list: MainNodeList):
        self.mainNodeList = main_node_list
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)

    def sendMessageByNodeID(self, node_id, data: bytes):
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        ip = ""
        for main_node in self.mainNodeList.getNodeList():
            if main_node["node_info"].nodeId == node_id:
                ip = main_node["node_info"].nodeIp
        ip = "tcp://" + ip + ":23334"
        self.socket.connect(ip)
        self.socket.send(data)
        message = self.socket.recv()
        self.socket.disconnect(ip)
        return message

    def sendMessageByIP(self, ip, data: bytes):
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        ip = "tcp://" + ip + ":23334"
        self.socket.connect(ip)
        self.socket.send(data)
        message = self.socket.recv()
        self.socket.disconnect(ip)
        return message


# 订阅消息
# 订阅者
class SUB(threading.Thread):
    def __init__(self, ip, pub: PUB, client: Client, blockListOfBeings: BlockListOfBeings,
                 node_list_of_apply: [ApplicationForm],
                 user: User, manager_of_reply_new_node_list: [ManagerOfReplyNewNode],
                 storage_of_galaxy: StorageOfGalaxy, vote_count: VoteCount, getEpoch, getElectionPeriod,
                 manager_of_reply_delete_node_list, main_node: MainNode, reSubscribe, storage_of_temp: StorageOfTemp,
                 current_main_node, node_del_application_form_list: []):
        super().__init__()
        self.name = str(ip)
        self.reSubscribe = reSubscribe
        self.blockListOfBeings = blockListOfBeings
        self.nodeListOfApply = node_list_of_apply
        self.pub = pub
        self.client = client
        self.mainNode = main_node
        self.user = user
        self.nodeManager = NodeManager(manager_of_reply_new_node_list=manager_of_reply_new_node_list,
                                       node_list_of_delete=manager_of_reply_delete_node_list, user=user,
                                       main_node=main_node)
        self.storageOfTemp = storage_of_temp
        self.storageOfGalaxy = storage_of_galaxy
        self.voteCount = vote_count
        self.getEpoch = getEpoch
        self.getElectionPeriod = getElectionPeriod
        self.currentMainNode = current_main_node
        self.nodeDelApplicationFormList = node_del_application_form_list

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        ip = "tcp://" + ip + ":23333"
        self.socket.connect(ip)
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getBlockTopicOfBeings())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfJoin())
        self.socket.setsockopt(zmq.SUBSCRIBE, SubscribeTopics.getNodeTopicOfApplyJoin())
        self.stopFlag = True

    def stop(self):
        self.stopFlag = False

    def run(self):
        self.receive()

    def receive(self):
        while self.stopFlag:
            message = self.socket.recv_multipart()
            print(f'Received: {message}')

            # 收集其他节点产生的众生区块
            if message[0:len(SubscribeTopics.getBlockTopicOfBeings())] == SubscribeTopics.getBlockTopicOfBeings():
                block_mess = message[len(SubscribeTopics.getBlockTopicOfBeings()):]
                if block_mess["mess_type"] == NetworkMessageType.NEW_BLOCK:
                    block = block_mess["message"]
                    # 是否已经存在
                    if self.mainNode.currentBlockList.userPkIsBlock(user_pk=block.getUserPk()):
                        continue
                    # 验证是否在有生成权限的节点内
                    if not self.currentMainNode.userPKisExit(user_pk=block.getUserPk()):
                        continue
                    # 签名验证
                    header = block.getBlockHeader()
                    result = True
                    for i in range(len(header["userPK"])):
                        result = result and CipherSuites.verify(pk=header["userPK"][i],
                                                                signature=header["bodySignature"][i],
                                                                message=block.body)
                    if result:
                        # 广播消息
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=block_mess)
                        # 保存
                        self.blockListOfBeings.addBlock(block=block)

                # 本次被选中，但是不生产区块的消息
                if block_mess["mess_type"] == NetworkMessageType.NO_BLOCK:
                    empty_block_dict = literal_eval(block_mess["message"])
                    empty_block = EmptyBlock(user_pk=empty_block_dict["user_pk"], epoch=empty_block_dict["epoch"])
                    empty_block.setSignature(empty_block_dict["signature"])
                    # 是否已经存在
                    if self.mainNode.currentBlockList.userPkIsBlock(user_pk=empty_block.userPk):
                        continue
                    # 验证是否在有生成权限的节点内
                    if not self.currentMainNode.userPKisExit(user_pk=empty_block.userPk):
                        continue
                    # 验证签名
                    if not CipherSuites.verify(pk=empty_block.userPk, signature=empty_block.signature,
                                               message=str(empty_block.getInfo()).encode("utf-8")):
                        continue
                    self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=block_mess)
                    self.blockListOfBeings.addMessageOfNoBlock(empty_block=empty_block)

            # 收集其他节点产生的银河区块
            if message[0:len(SubscribeTopics.getBlockTopicOfGalaxy())] == SubscribeTopics.getBlockTopicOfGalaxy():
                conformation_Of_galaxy_message = literal_eval(message[len(SubscribeTopics.getBlockTopicOfGalaxy()):])
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
                if total < self.voteCount.getVotesOfGalaxyGenerate(current_election_cycle=self.getElectionPeriod()):
                    continue
                header = block_of_galaxy.getBlockHeader()
                total = self.voteCount.getAndVerifyVotes(votes=votes, main_node_id_of_block=header["userPK"][0][0:16],
                                                         block_id_of_block=header["blockID"],
                                                         election_period_of_block=header["electionPeriod"])
                if total < self.voteCount.getVotesOfGalaxyGenerate(current_election_cycle=self.getElectionPeriod()):
                    continue
                # 广播
                self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfGalaxy(),
                                     message=str(conformation_Of_galaxy_message).encode("utf-8"))

                # 存入数据库
                self.storageOfGalaxy.addBlockOfGalaxy(block_of_galaxy=block_of_galaxy)

            # 新节点申请加入 消息
            # 保存到暂存区（以便审核后回复）广播
            if message[0:len(SubscribeTopics.getNodeTopicOfApplyJoin())] == SubscribeTopics.getNodeTopicOfApplyJoin():
                application_form = message[len(SubscribeTopics.getNodeTopicOfApplyJoin()):]
                # 保证节点不能同时有多个申请书
                node_id_list = []
                for af in self.nodeListOfApply:
                    node_id_list.append(af.nodeInfo.nodeId)
                if application_form.nodeInfo.nodeId not in node_id_list:
                    # 验证
                    # 验证新节点信息和签名
                    node_signature = application_form.nodeSignature
                    node_info = application_form.nodeInfo
                    new_node_user_pk = node_info["user_pk"]
                    # 新节点信息与签名匹配
                    if CipherSuites.verify(pk=new_node_user_pk, signature=node_signature,
                                           message=str(node_info).encode("utf-8")):
                        # 验证申请书和签名
                        # 申请书与新节点签名匹配
                        application_content = application_form.application["content"]
                        new_node_signature = application_form.application["new_node_signature"]
                        if CipherSuites.verify(pk=new_node_user_pk, signature=new_node_signature,
                                               message=application_content):
                            # 保存到暂存区 并广播
                            self.nodeListOfApply.append(application_form)
                            self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyJoin(),
                                                 message=application_form)

            # 新节点确认加入主节点消息
            if message[0:len(SubscribeTopics.getNodeTopicOfJoin())] == SubscribeTopics.getNodeTopicOfJoin():
                agree_info = literal_eval(message[len(SubscribeTopics.getNodeTopicOfJoin()):])["message"]
                # 验证新节点信息和签名
                # 验证所有同意节点的时间和签名
                if self.nodeManager.verifyAgreeInfo(current_main_node_count=self.mainNode.mainNodeList.getNodeCount(),
                                                    agree_info=agree_info):
                    new_node_id = agree_info["node_info"]["node_id"]
                    new_user_pk = agree_info["node_info"]["user_pk"]
                    new_node_ip = agree_info["node_info"]["node_ip"]
                    new_create_time = agree_info["start_time"]

                    node_info = NodeInfo(node_id=new_node_id, user_pk=new_user_pk, node_ip=new_node_ip,
                                         create_time=new_create_time)
                    # 广播
                    mess = NetworkMessage(mess_type=NetworkMessageType.NewNodeJoin, message=agree_info).getNetMessage()
                    self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfJoin(), message=mess)
                    # 将新节点加入数据库
                    self.mainNode.mainNodeList.addMainNode(node_info=node_info)
                    # 重新计算订阅列表，重新创建32个订阅链接
                    self.reSubscribe()

            # 申请删除主节点消息
            # 被选中，但是没有产生区块
            # 注意：此处应该先检测投票数量是否符合条件，若投票数量符合条件，则直接删除节点，若不符合条件，再考虑其他情况
            if message[
               0:len(SubscribeTopics.getNodeTopicOfApplyDelete())] == SubscribeTopics.getNodeTopicOfApplyDelete():
                node_del_application_form_mess = literal_eval(
                    message[len(SubscribeTopics.getNodeTopicOfApplyDelete()):])
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
                if not self.currentMainNode.userPKisExit(user_pk=apply_user_pk):
                    continue
                # 检测申请被删除的节点当前是否应该生成区块
                if not self.currentMainNode.userPKisExit(user_pk=del_node_user_pk):
                    continue
                # 验证申请节点签名
                if not CipherSuites.verify(pk=apply_user_pk, signature=apply_signature,
                                           message=(str(node_del_application_form.getInfo()).encode("utf-8"))):
                    continue

                # 检测申请书的投票数量是否达到标准
                if self.nodeManager.confirmDelNodes(node_del_application_form=node_del_application_form):
                    # 删除节点
                    self.mainNode.mainNodeList.delMainNodeById(node_id=del_node_id)
                    # 广播
                    self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyDelete(),
                                         message=node_del_application_form_mess)
                    continue

                # 检测自己是否收到该区块
                if self.mainNode.currentBlockList.userPkIsExit(user_pk=del_node_user_pk):
                    if self.mainNode.currentBlockList.userPkIsBlock(user_pk=del_node_user_pk):
                        block = self.mainNode.currentBlockList.getBlockByUserPk(user_pk=del_node_user_pk)
                        network_message = NetworkMessage(NetworkMessageType.NEW_BLOCK, message=block)
                        network_message.setCertification(node_id=self.user.getUserPKString()[0:16],
                                                         user_pk=self.user.getUserPKString())
                        user_signature = self.user.sign(message=str(network_message.getCertification()).encode("utf-8"))
                        network_message.setSignature(user_signature)
                        self.client.sendMessageByNodeID(node_id=apply_user_pk[0:16],
                                                        data=str(network_message.getNetMessage()).encode("utf-8"))
                    else:
                        # 不产生区块的消息
                        network_message = NetworkMessage(NetworkMessageType.NO_BLOCK,
                                                         message=self.mainNode.currentBlockList.getMessageOfNoBlock(
                                                             user_pk=del_node_user_pk))
                        self.client.sendMessageByNodeID(node_id=apply_user_pk[0:16],
                                                        data=str(network_message.getNetMessage()).encode("utf-8"))
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
                                                           message=str(node_del_application_form.getInfo()).encode(
                                                               "utf-8")):
                                    continue
                                node_del_application_form.addVotes(user_pk=vote["user_pk"], signature=vote["signature"])
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

            # 投票确认消息
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
                        self.pub.sendMessage(topic=SubscribeTopics.getVoteConfirmation(), message=vote_information)


# 监听接受消息
class Server(threading.Thread):
    def __init__(self, user: User, manager_of_reply_new_node_list: [ManagerOfReplyNewNode],
                 manager_of_reply_delete_node_list, pub: PUB, main_node: MainNode, storage_of_temp: StorageOfTemp,
                 storage_of_galaxy: StorageOfGalaxy,
                 wait_galaxy_block: WaitGalaxyBlock, vote_count: VoteCount, getEpoch, getElectionPeriod,
                 newBlockOfGalaxy, current_main_node):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind("tcp://*:23334")
        self.stopFlag = True
        self.nodeManager = NodeManager(manager_of_reply_new_node_list=manager_of_reply_new_node_list,
                                       node_list_of_delete=manager_of_reply_delete_node_list, user=user,
                                       main_node=main_node)
        self.pub = pub
        self.mainNode = main_node
        self.mainNodeList = self.mainNode.mainNodeList
        self.storageOfTemp = storage_of_temp
        self.storageOfGalaxy = storage_of_galaxy
        self.waitGalaxyBlock = wait_galaxy_block
        self.voteCount = vote_count
        self.getEpoch = getEpoch
        self.getElectionPeriod = getElectionPeriod
        self.newBlockOfGalaxy = newBlockOfGalaxy
        self.currentMainNode = current_main_node
        self.user = user

    def run(self):
        self.receive()

    def stop(self):
        self.stopFlag = False

    def receive(self):
        while self.stopFlag:
            #  Wait for next request from client
            message = self.socket.recv()
            try:
                print(f"Received request: {message}")
                net_message = literal_eval(bytes(message).decode())
                mess_type = net_message["mess_type"]
                # 检查发送方签名，核对对方是否为主节点
                # 签名有效期为八秒
                client_info = net_message["client_info"]
                signature = net_message["signature"]
                if (STime.getTimestamp() - client_info["send_time"]) > 8:
                    # 超过有效时间
                    continue
                if not self.mainNode.mainNodeList.userPKisExit(user_pk=client_info["user_pk"]):
                    # 发送方不是主节点
                    continue
                if not CipherSuites.verify(pk=client_info["user_pk"], signature=signature,
                                           message=str(client_info).encode("utf-8")):
                    # 签名验证失败
                    continue

                # 新节点加入申请的回复消息
                if mess_type == NetworkMessageType.ReplayNewNodeApplicationJoin:
                    reply_application_form = net_message["message"]
                    self.nodeManager.replyApplyJoin(pub=self.pub,
                                                    current_main_node_count=self.mainNodeList.getNodeCount(),
                                                    storage_of_temp=self.storageOfTemp,
                                                    reply_application_form=reply_application_form)
                    self.socket.send(str(NetworkMessage(mess_type=NetworkMessageType.RECEIVE_CONFIRMATION,
                                                        message="get").getNetMessage()).encode("utf-8"))

                # 投票信息
                if mess_type == NetworkMessageType.Vote_Info:
                    vote_info = net_message["message"]
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

                # 申请获得区块的消息
                if mess_type == NetworkMessageType.APPLY_GET_BLOCK:
                    current_epoch = net_message["message"]
                    # 检查当前周期内，自己是否生成众生区块
                    if not self.currentMainNode.getNodeList().userPKisExit(user_pk=self.user.getUserSK()):
                        continue
                    # 检查epoch是否匹配
                    if current_epoch != self.getEpoch():
                        continue
                    # 发送区块，或不生成区块的消息
                    user_pk = self.user.getUserPKString()
                    if self.mainNode.currentBlockList.userPkIsExit(user_pk=user_pk):
                        block = self.mainNode.currentBlockList.getBlockByUserPk(user_pk=user_pk)
                        network_message = NetworkMessage(NetworkMessageType.NEW_BLOCK, message=block)
                        self.socket.send(data=str(network_message.getNetMessage()).encode("utf-8"))
                    else:
                        network_message = NetworkMessage(NetworkMessageType.NEW_BLOCK, message=None)
                        self.socket.send(str(network_message).encode("utf-8"))

                # 新区块消息
                if mess_type == NetworkMessageType.NEW_BLOCK:
                    block = literal_eval(net_message["message"])
                    # 检测自己是否收到了该区块
                    if self.mainNode.currentBlockList.userPkIsExit(user_pk=block.getUserPk()[1]):
                        continue
                    # 检测自己是否是负责本次生成的节点
                    if not self.currentMainNode.userPKisExit(user_pk=self.user.getUserPKString()):
                        continue
                    # 检测该区块是否应该为本次生成，通过生成节点的用户公钥检验
                    if not self.currentMainNode.userPKisExit(user_pk=block.getUserPk()[1]):
                        continue
                    # 验证签名
                    header = block.getBlockHeader()
                    result = True
                    for i in range(len(header["userPK"])):
                        result = result and CipherSuites.verify(pk=header["userPK"][i],
                                                                signature=header["bodySignature"][i],
                                                                message=block.body)
                    if result:
                        # 广播消息
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(),
                                             message=net_message)
                        # 保存
                        self.mainNode.currentBlockList.addBlock(block=block)

                # 不产生新区块消息
                if mess_type == NetworkMessageType.NO_BLOCK:
                    empty_block_dict = literal_eval(net_message["message"])
                    empty_block = EmptyBlock(user_pk=empty_block_dict["user_pk"], epoch=empty_block_dict["epoch"])
                    empty_block.setSignature(empty_block_dict["signature"])
                    # 检测自己是否收到了该区块
                    if self.mainNode.currentBlockList.userPkIsExit(user_pk=empty_block.userPk):
                        continue
                    # 检测自己是否是负责本次生成的节点
                    if not self.currentMainNode.userPKisExit(user_pk=self.user.getUserPKString()):
                        continue
                    # 检测该区块是否应该为本次生成，通过生成节点的用户公钥检验
                    if not self.currentMainNode.userPKisExit(user_pk=empty_block.userPk):
                        continue
                    # 验证签名
                    if not CipherSuites.verify(pk=empty_block.userPk, signature=empty_block.signature,
                                               message=str(empty_block.getInfo()).encode("utf-8")):
                        continue

                    # 广播
                    self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(),
                                         message=empty_block.getMessage())
                    # 保存
                    self.mainNode.currentBlockList.addMessageOfNoBlock(empty_block=empty_block)

            # 其他消息类型

            except Exception:
                # 非规定数据结构
                pass


if __name__ == "__main__":
    a = b'block b asdfsdfa'
    l = len(SubscribeTopics.getBlockTopicOfBeings())
    print(l)
    print(a)
    print(a[0:l - 1])
    print(a[l:])

    # server = Server()
    # server.runAccept()
    # print("over")
