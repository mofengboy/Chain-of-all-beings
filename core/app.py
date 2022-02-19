import random
from ast import literal_eval

from core.data.block_of_beings import EmptyBlock
from core.data.block_of_galaxy import BodyOfGalaxyBlock, BlockOfGalaxy
from core.data.node_info import NodeInfo
from core.data.network_message import NetworkMessageType, NetworkMessage, SubscribeTopics
from core.user.user import User
from core.node.main_node import MainNode
from core.network.net import PUB, SUB, Server, Client
from core.consensus.block_generate import CurrentMainNode, NewBlockOfBeings, NewBlockOfGalaxy
from core.consensus.node_management import ManagerOfReplyNewNode
from core.consensus.vote import VoteCount
from core.consensus.data import VoteInformation, ApplicationForm, ReplyApplicationForm, WaitGalaxyBlock
from core.consensus.data import NodeDelApplicationForm
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_temp import StorageOfTemp
from core.storage.storage_of_galaxy import StorageOfGalaxy
from core.utils.ciphersuites import CipherSuites
from core.utils.system_time import STime


class APP:
    def __init__(self):
        self.currentEpoch = 0  # 当前epoch
        self.electionPeriod = 0  # 选举期次
        self.managerOfReplyNewNodeList = []  # 新节点申请回复信息管理
        self.nodeDelApplicationFormList = []  # 申请删除节点以及投票信息列表
        self.storageOfBeings = StorageOfBeings()  # 众生区块存储类
        self.storageOfTemp = StorageOfTemp()  # 临时区存储类
        self.storageOfGalaxy = StorageOfGalaxy()  # 银河区块存储类

        self.user = User()  # 用户
        self.mainNode = MainNode(self.user)  # 主节点
        # 当前epoch生成区块的节点列表
        self.currentMainNode = CurrentMainNode(self.mainNode.mainNodeList,
                                               self.storageOfBeings.getLastBlockByCache()).getNodeList()
        self.waitGalaxyBlock = WaitGalaxyBlock(main_node_id=self.mainNode.getNodeId(),
                                               main_user_pk=self.user.getUserPKString())  # 推荐成为银河区块的众生区块列表
        self.voteCount = VoteCount(storage_of_beings=self.storageOfBeings, storage_of_temp=self.storageOfTemp)  # 票数计算

        self.pub = PUB()  # 发布者
        self.pub.start()
        self.subList = []  # 订阅列表
        self.client = Client(main_node_list=self.mainNode.mainNodeList)  # 客户端
        self.server = Server(user=self.user, manager_of_reply_new_node_list=self.managerOfReplyNewNodeList,
                             manager_of_reply_delete_node_list=[], pub=self.pub, main_node=self.mainNode,
                             storage_of_temp=self.storageOfTemp, wait_galaxy_block=self.waitGalaxyBlock,
                             vote_count=self.voteCount, getEpoch=self.getEpoch, storage_of_galaxy=self.storageOfGalaxy,
                             getElectionPeriod=self.getElectionPeriod, newBlockOfGalaxy=self.newBlockOfGalaxy,
                             current_main_node=self.currentMainNode)  # 服务端
        self.server.start()

    def addEpoch(self):
        self.currentEpoch += 1

    def getEpoch(self):
        return self.currentEpoch

    def addElectionPeriod(self):
        self.electionPeriod += 1

    def getElectionPeriod(self):
        return self.electionPeriod

    # 增加订阅
    def addSub(self, ip):
        sub = SUB(ip=ip, pub=self.pub, blockListOfBeings=self.mainNode.currentBlockList,
                  node_list_of_apply=self.mainNode.nodeListOfApply, user=self.user, vote_count=self.voteCount,
                  manager_of_reply_new_node_list=self.managerOfReplyNewNodeList, manager_of_reply_delete_node_list=[],
                  main_node=self.mainNode, reSubscribe=self.reSubscribe, storage_of_temp=self.storageOfTemp,
                  getEpoch=self.getEpoch, getElectionPeriod=self.getElectionPeriod,
                  storage_of_galaxy=self.storageOfGalaxy, current_main_node=self.currentMainNode,
                  node_del_application_form_list=[], client=self.client)
        sub.start()
        self.subList.append(sub)

    # 删除订阅
    def delSub(self, ip: str):
        for i in range(len(self.subList)):
            if ip == self.subList[i].name:
                self.subList[i].stop()
                del self.subList[i]
                break

    # 重新订阅32个链接
    def reSubscribe(self):
        lastSub = self.subList.copy()
        node = self.mainNode.mainNodeList.getNodeCount()
        NUMBER_OF_SUBSCRIPTION = 32
        count = NUMBER_OF_SUBSCRIPTION
        if node < NUMBER_OF_SUBSCRIPTION:
            count = node
        node_list = random.sample(self.mainNode.mainNodeList.getNodeList(), count)
        for node_i in node_list:
            ip = node_i["node_info"].nodeIp
            self.addSub(ip)
        # 删除之前订阅
        for sub_i in lastSub:
            ip = sub_i.name
            self.delSub(ip)

    # 创建推荐区块数据结构，准备接受其他节点的投票信息
    def recommendedBlock(self, block_id):
        self.waitGalaxyBlock.addGalaxyBlock(block_id=block_id)

    # 简单节点用户发起的投票
    def voteForGalaxy(self, simple_vote_information: VoteInformation):
        # 首先计算当前主节点拥有的票数，然后计算授权给简单节点用户的票数
        num_of_main_user_vote = self.voteCount.computeMainUserVote(user_pk=self.user.getUserPKString(),
                                                                   current_election_cycle=self.getElectionPeriod())
        if simple_vote_information.numberOfVote > num_of_main_user_vote:
            # 超出当前主节点拥有的最大投票数量
            pass
        num_of_simple_user_vote = self.voteCount.computeSimpleUserVote(simple_user_pk=simple_vote_information.userPK,
                                                                       current_election_cycle=self.getElectionPeriod())
        if simple_vote_information.numberOfVote > num_of_simple_user_vote:
            # 超出当前简单节点被授权的最大投票数量
            pass
        # 将用户公钥和签名转为主节点的签名，因为对其他主节点而言，只能看到主节点拥有的票数
        vote_information = VoteInformation(main_node_id=simple_vote_information.mainNodeId,
                                           block_id=simple_vote_information.blockId,
                                           election_period=simple_vote_information.electionPeriod,
                                           number_of_vote=simple_vote_information.numberOfVote,
                                           user_pk=self.user.getUserPKString())
        signature = self.user.sign(message=str(vote_information.getVoteInfo()).encode("utf-8"))
        vote_information.setSignature(signature)
        # 发送消息进行投票 不是发送广播
        network_mess = NetworkMessage(mess_type=NetworkMessageType.Vote_Info,
                                      message=vote_information.getMessage())
        res = self.client.sendMessageByNodeID(node_id=vote_information.mainNodeId,
                                              data=str(network_mess).encode("utf-8"))

        # 获取投票结果
        return res

    # 回复新节点加入申请，同意或拒绝
    def replyNewNodeJoin(self, new_node_id, start_time, is_agree):
        reply_time = STime.getTimestamp()
        reply_application_form = ReplyApplicationForm(new_node_id=new_node_id, start_time=start_time, is_agree=is_agree,
                                                      reply_time=reply_time)
        signature = self.mainNode.sign(str(reply_application_form.getInfo()).encode("utf-8"))
        reply_application_form.setSignature(signature)
        reply_application_form.setUserPk(self.user.getUserPKString())
        # 发送同意或拒绝消息
        net_message = NetworkMessage(mess_type=NetworkMessageType.ReplayNewNodeApplicationJoin,
                                     message=reply_application_form).getNetMessage()

        res = self.client.sendMessageByNodeID(node_id=new_node_id, data=str(net_message).encode("utf-8"))
        # 要弄清是异步还是同步
        if res != b"get":
            # 抛出错误，发送失败
            pass

        # 删除暂存区的消息
        i = 0
        for application_form in self.mainNode.nodeListOfApply:
            if application_form.nodeInfo.nodeId != new_node_id:
                i += 1
            else:
                break
        del self.mainNode.nodeListOfApply[i]

    # 向全网广播新节点申请请求
    # 此时，当前主节点已经审核通过
    def applyNewNodeJoin(self, application_form: ApplicationForm):
        # 验证新节点信息和签名
        node_signature = application_form.nodeSignature
        node_info = application_form.nodeInfo
        new_node_user_pk = node_info["user_pk"]
        if not CipherSuites.verify(pk=new_node_user_pk, signature=node_signature,
                                   message=str(node_info).encode("utf-8")):
            # 抛出错误 新节点信息与签名不匹配
            pass

        # 验证申请书和签名
        application_content = application_form.application["content"]
        new_node_signature = application_form.application["new_node_signature"]
        if not CipherSuites.verify(pk=new_node_user_pk, signature=new_node_signature, message=application_content):
            # 抛出错误 申请书与新节点签名不匹配
            pass

        # 增加当前主节点签名 公钥和开始时间
        main_node_signature = self.mainNode.sign(message=application_content)
        main_node_user_pk = self.user.getUserPKString()
        start_time = STime.getTimestamp()
        application_form.setMainNodeSignature(main_node_signature)
        application_form.setMainNodeUserPk(main_node_user_pk)
        application_form.setStartTime(start_time)

        # 修改数据库数据，准备接受其他主节点的意见
        self.storageOfTemp.auditNodeOfApplication(db_id=application_form.dbID, is_audit=1,
                                                  application=application_form.application, start_time=start_time,
                                                  main_node_signature=main_node_signature,
                                                  main_node_user_pk=main_node_user_pk)
        # 统计数据
        new_node_id = application_form.nodeInfo["node_id"]
        new_user_pk = application_form.nodeInfo["user_pk"]
        new_node_ip = application_form.nodeInfo["node_ip"]
        new_create_time = application_form.nodeInfo["create_time"]
        node_info = NodeInfo(node_id=new_node_id, user_pk=new_user_pk, node_ip=new_node_ip, create_time=new_create_time)
        manager_of_reply_new_node = ManagerOfReplyNewNode(db_id=application_form.dbID,
                                                          new_node_id=application_form.nodeId, start_time=start_time,
                                                          node_info=node_info)
        self.managerOfReplyNewNodeList.append(manager_of_reply_new_node)

        # 全网广播
        self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyJoin(), message=application_form)

    # 众生区块生成周期
    def startNewEpoch(self):
        # 获取本次产生区块的节点列表
        self.currentMainNode = CurrentMainNode(self.mainNode.mainNodeList,
                                               self.storageOfBeings.getLastBlockByCache()).getNodeList()
        # 当前节点是否生成区块
        for node in self.currentMainNode.getNodeList():
            if node.nodeInfo.nodeId == self.mainNode.nodeInfo.nodeId:
                # 判断临时存储区是否有数据，若有数据，则生成区块，否则发送不生成区块的消息
                if self.storageOfTemp.getDataCount() > 0:
                    # 生成区块
                    prev_block_header = []
                    pre_block = []
                    for block in self.storageOfBeings.currentBlockListOfBeing.getList():
                        prev_block_header.append(block.getBlockHeaderSHA256())
                        pre_block.append(block.getBlockSHA256())

                    epoch = self.storageOfBeings.currentBlockListOfBeing.getList()[0].getEpoch()

                    data = self.storageOfTemp.getTopData()
                    body = data["body"]
                    user_pk = [data["user_pk"], self.user.getUserPKString()]
                    main_node_user_signature = self.user.sign(body)
                    body_signature = [data["body_signature"], main_node_user_signature]

                    new_block = NewBlockOfBeings(user_pk=user_pk, body_signature=body_signature, body=body, epoch=epoch,
                                                 pre_block=pre_block, prev_block_header=prev_block_header).getBlock()

                    # 广播消息
                    block_mess = NetworkMessage(mess_type=NetworkMessageType.NEW_BLOCK,
                                                message=new_block).getNetMessage()
                    self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=block_mess)
                    # 保存至当前区块列表
                    self.mainNode.currentBlockList.addBlock(block=new_block)
                else:
                    # 广播无区块产生的消息
                    empty_block = EmptyBlock(user_pk=self.user.getUserPKString(), epoch=self.getEpoch())
                    signature = self.user.sign(str(empty_block.getInfo()).encode("utf-8"))
                    empty_block.setSignature(signature)
                    mess = NetworkMessage(mess_type=NetworkMessageType.NO_BLOCK, message=empty_block.getMessage())
                    self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=mess)
                    # 保存至当前区块列表
                    self.mainNode.currentBlockList.addMessageOfNoBlock(net_message=empty_block.getMessage())

    # 生成银河区块
    def newBlockOfGalaxy(self, block_id) -> BlockOfGalaxy:
        # 获取生成该众生区块的用户公钥列表（简单节点用户公钥和主节点用户公钥）
        users_pk = self.storageOfBeings.getUserPkByBlockId(block_id=block_id)
        body = BodyOfGalaxyBlock(users_pk=users_pk, block_id=block_id)
        signature = self.user.sign(message=str(body.getBody()).encode("utf-8"))
        current_election_period = self.getElectionPeriod()
        [pre_block, prev_block_header] = self.storageOfGalaxy.getBlockAbstractByElectionPeriod(
            election_period=current_election_period)
        while pre_block is None:
            # 此时表明上一选举时期没有银河区块产生，继续向前寻找
            current_election_period -= 1
            [pre_block, prev_block_header] = self.storageOfGalaxy.getBlockAbstractByElectionPeriod(
                election_period=current_election_period)

        new_block_of_galaxy = NewBlockOfGalaxy(user_pk=[self.user.getUserPKString()],
                                               election_period=self.getElectionPeriod(), body_signature=[signature],
                                               body=body.getBody(), epoch=self.getEpoch(),
                                               pre_block=pre_block,
                                               prev_block_header=prev_block_header).getBlock()
        return new_block_of_galaxy

    # 新周期开始16秒后，检查并执行
    def startCheckAndApplyDeleteNode(self):
        if self.currentMainNode.userPKisExit(user_pk=self.user.getUserPKString()):
            # 该节点为本次发布节点的其中之一
            for node in self.currentMainNode.getNodeList():
                user_pk = node["node_info"].userPk
                node_id = node["node_info"].nodeId
                # 检查是否存在应该收到，但是未收到的区块
                if not self.mainNode.currentBlockList.userPkIsExit(user_pk=user_pk):
                    # 没有收到该节点产生的区块或消息
                    # 制作申请书，删除该节点
                    node_del_application_form = NodeDelApplicationForm(del_node_id=node_id, del_user_pk=user_pk,
                                                                       current_epoch=self.getEpoch())
                    signature = self.user.sign(str(node_del_application_form.getInfo()).encode("utf-8"))
                    node_del_application_form.setApplySignature(signature)
                    node_del_application_form.setApplyUserPk(self.user.getUserPKString())
                    # 广播申请删除该节点的消息
                    self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyDelete(),
                                         message=node_del_application_form.getMessage())

    # 新周期开始24秒后执行
    def startCheckAndGetBlock(self):
        if not self.currentMainNode.userPKisExit(user_pk=self.user.getUserPKString()):
            # 该节点不负责本次区块生成
            for node in self.currentMainNode.getNodeList():
                user_pk = node["node_info"].userPk
                node_id = node["node_info"].nodeId
                # 检查是否存在应该收到，但是未收到的区块
                if not self.mainNode.currentBlockList.userPkIsExit(user_pk=user_pk):
                    # 直接发送请求，获取生成的区块
                    network_message = NetworkMessage(NetworkMessageType.APPLY_GET_BLOCK,
                                                     message=self.getEpoch())
                    network_message.setCertification(node_id=self.user.getUserPKString()[0:16],
                                                     user_pk=self.user.getUserPKString())
                    signature = self.user.sign(message=str(network_message.getCertification()).encode("utf-8"))
                    network_message.setSignature(signature)
                    res = self.client.sendMessageByNodeID(node_id=node_id,
                                                          data=str(network_message.getNetMessage()).encode("utf-8"))
                    res = literal_eval(res)
                    if res["mess_type"] == NetworkMessageType.NEW_BLOCK:
                        self.mainNode.currentBlockList.addBlock(block=res["message"])
                    if res["mess_type"] == NetworkMessageType.NO_BLOCK:
                        self.mainNode.currentBlockList.addMessageOfNoBlock(user_pk=user_pk)
