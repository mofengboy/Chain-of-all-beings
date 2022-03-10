import random
import logging.config
from ast import literal_eval

from core.data.block_of_beings import EmptyBlock, BlockListOfBeings
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
from core.utils.sdk import SDK
from core.utils.serialization import SerializationBeings
from core.utils.network_request import MainNodeIp
from core.data.genesis_block import GenesisBlock

logger = logging.getLogger("main")


class APP:
    def __init__(self):
        self.currentEpoch = 0  # 当前epoch
        self.electionPeriod = 0  # 选举期次

        self.storageOfBeings = StorageOfBeings()  # 众生区块存储类
        self.storageOfTemp = StorageOfTemp()  # 临时区存储类
        self.storageOfGalaxy = StorageOfGalaxy()  # 银河区块存储类

        self.user = User()  # 用户
        # 注册或者登录用户
        self.user.register()

        self.mainNode = MainNode(self.user)  # 主节点
        self.waitGalaxyBlock = WaitGalaxyBlock(main_node_id=self.mainNode.getNodeId(),
                                               main_user_pk=self.user.getUserPKString())  # 推荐成为银河区块的众生区块列表
        self.voteCount = VoteCount(storage_of_beings=self.storageOfBeings, storage_of_temp=self.storageOfTemp)  # 票数计算

        self.pub = PUB()  # 发布者
        self.pub.start()
        self.subList = []  # 订阅列表
        self.client = Client(main_node_list=self.mainNode.mainNodeList)  # 客户端
        self.server = Server(user=self.user, manager_of_reply_new_node_list=self.mainNode.managerOfReplyNewNodeList,
                             manager_of_reply_delete_node_list=[], pub=self.pub, main_node=self.mainNode,
                             storage_of_temp=self.storageOfTemp, wait_galaxy_block=self.waitGalaxyBlock,
                             vote_count=self.voteCount, getEpoch=self.getEpoch, storage_of_galaxy=self.storageOfGalaxy,
                             getElectionPeriod=self.getElectionPeriod, newBlockOfGalaxy=self.newBlockOfGalaxy,
                             current_main_node=self.mainNode.currentMainNode,
                             storage_of_beings=self.storageOfBeings)  # 服务端
        self.server.start()
        # 存储创世区块
        self.storageGenesisBlock()
        # 后端sdk
        self.webServerSDK = SDK()

    def addEpoch(self):
        self.currentEpoch += 1

    def getEpoch(self):
        return self.currentEpoch

    def setEpoch(self, epoch):
        self.currentEpoch = epoch

    def addElectionPeriod(self):
        self.electionPeriod += 1

    def getElectionPeriod(self):
        return self.electionPeriod

    def setElectionPeriod(self, election_period):
        self.electionPeriod = election_period

    # 增加订阅
    def addSub(self, ip):
        sub = SUB(ip=ip, pub=self.pub, blockListOfBeings=self.mainNode.currentBlockList,
                  node_list_of_apply=self.mainNode.nodeListOfApply, user=self.user, vote_count=self.voteCount,
                  manager_of_reply_new_node_list=self.mainNode.managerOfReplyNewNodeList,
                  manager_of_reply_delete_node_list=[],
                  main_node=self.mainNode, reSubscribe=self.reSubscribe, storage_of_temp=self.storageOfTemp,
                  getEpoch=self.getEpoch, getElectionPeriod=self.getElectionPeriod,
                  storage_of_galaxy=self.storageOfGalaxy, current_main_node=self.mainNode.currentMainNode,
                  node_del_application_form_list=self.mainNode.nodeDelApplicationFormList, client=self.client)
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
        logger.info("订阅完成，当前订阅数量为" + str(self.mainNode.mainNodeList.getNodeCount()))
        # 删除之前订阅
        for sub_i in lastSub:
            ip = sub_i.name
            self.delSub(ip)
        logger.info("已删除之前订阅，当前订阅数量为" + str(self.mainNode.mainNodeList.getNodeCount()))

    # 读入主节点列表，通过配置文件提供的种子IP
    def loadMainNodeListBySeed(self):
        ip_list = MainNodeIp().getTpList()
        data = NetworkMessage(mess_type=NetworkMessageType.Get_Main_Node_List, message=None).getNetMessage()
        for ip in ip_list:
            try:
                res = self.client.sendMessageByIP(ip=ip, data=str(data).encode("utf-8"))
                self.mainNode.mainNodeList.setNodeList(literal_eval(res))
                break
            except Exception as err:
                logger.warning(err)

    # 通过其他主节点获取当前epoch
    def getCurrentEpochByOtherMainNode(self):
        node_ip_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            node_ip_list.append(main_node["node_info"]["node_ip"])
        random.shuffle(node_ip_list)
        data = NetworkMessage(NetworkMessageType.Get_Current_Epoch, message=None).getNetMessage()
        for ip in node_ip_list:
            try:
                res = self.client.sendMessageByIP(ip=ip, data=str(data).encode("utf-8"))
                self.setEpoch(res)
                break
            except Exception as err:
                logger.warning(err)

    # 同步区块
    def synchronizedBlockOfBeings(self):
        node_ip_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            node_ip_list.append(main_node["node_info"]["node_ip"])
        logger.info("众生区块开始同步")
        start = 0
        while True:
            if start + 10 <= self.getEpoch():
                end = start + 10
            else:
                end = self.getEpoch()
            data = NetworkMessage(NetworkMessageType.Get_Beings_Data,
                                  message=[start, end]).getNetMessage()
            ip = random.choice(node_ip_list)
            try:
                res = self.client.sendMessageByIP(ip=ip, data=str(data).encode("utf-8"))
                block_list = literal_eval(res)
                block_list_of_beings = []
                for block_i in block_list:
                    block = SerializationBeings.deserialization(block_i)
                    block_list_of_beings.append(block)
                self.storageOfBeings.saveBatchBlock(block_list_of_beings)
                logger.info("众生区块同步中,epoch:" + str(start) + "-" + str(end))

                if end == self.getEpoch():
                    logger.info("众生区块同步完成")
                    break
                start += 10
            except Exception as err:
                logger.warning(err)

    # 存储创世区块
    def storageGenesisBlock(self):
        genesis_block = GenesisBlock()
        block_list_of_beings = BlockListOfBeings()
        block_list_of_beings.addBlock(block=genesis_block.getBlockOfBeings())
        self.storageOfBeings.saveCurrentBlockOfBeings(blockListOfBeings=block_list_of_beings)
        logger.info("创世区块存储完成")

    # 创建推荐区块数据结构，准备接受其他节点的投票信息
    def recommendedBlock(self, block_id):
        # 检查数据库数据，是否有推荐区块
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
        # 创建投票统计
        new_node_id = application_form.nodeInfo["node_id"]
        new_user_pk = application_form.nodeInfo["user_pk"]
        new_node_ip = application_form.nodeInfo["node_ip"]
        new_create_time = application_form.nodeInfo["create_time"]
        node_info = NodeInfo(node_id=new_node_id, user_pk=new_user_pk, node_ip=new_node_ip, create_time=new_create_time)
        manager_of_reply_new_node = ManagerOfReplyNewNode(db_id=application_form.dbID,
                                                          new_node_id=application_form.nodeId, start_time=start_time,
                                                          node_info=node_info)
        self.mainNode.managerOfReplyNewNodeList.append(manager_of_reply_new_node)

        # 全网广播
        self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyJoin(), message=application_form)

    # 众生区块生成周期
    # 0-30S
    def startNewEpoch(self):
        logger.info("众生区块生成周期开始，Epoch:" + str(self.getEpoch()) + ",ElectionPeriod:" + str(self.getElectionPeriod()))
        # 获取本次产生区块的节点列表
        self.mainNode.currentMainNode = CurrentMainNode(self.mainNode.mainNodeList,
                                                        self.storageOfBeings.getLastBlockByCache()).getNodeList()
        #
        # 若本次主节点被选中产生区块，则检查暂存区数据数量，若大于0,则直接产生区块，若等于0，则调用后端sdk获取数据。只有在没获得数据的情况，
        # 才广播不产生区块的消息。
        # 若本次主节点没有被选中产生区块，则检查暂存区数据数量，若数量大于5，则不进行任何操作，若小于5，则调用后端SDK获取数据。
        #
        is_selected = False
        for node in self.mainNode.currentMainNode.getNodeList():
            # 当前节点是否生成区块
            if node["node_info"]["node_id"] == self.mainNode.nodeInfo.nodeId:
                is_selected = True
                logger.info("当前节点已被共识机制选中")
                # 判断临时存储区是否有数据，若有数据，则生成区块，否则发送不生成区块的消息
                temp_beings_count = self.storageOfTemp.getDataCount()
                if (temp_beings_count > 0) or (self.webServerSDK.getBeingsCount() > 0):
                    logger.info("当前节点生成区块")
                    # 生成区块
                    if temp_beings_count <= 0:
                        logger.info("调用web server SDK 读入数据")
                        webserver_beings_list = self.webServerSDK.getBeings()
                        self.storageOfTemp.saveBatchData(webserver_beings_list)

                    data = self.storageOfTemp.getTopData()
                    body = data["body"]
                    user_pk = [data["user_pk"], self.user.getUserPKString()]
                    main_node_user_signature = self.user.sign(body)
                    body_signature = [data["body_signature"], main_node_user_signature]

                    prev_block_header = []
                    pre_block = []
                    for block in self.storageOfBeings.currentBlockListOfBeing.list:
                        prev_block_header.append(block.getBlockHeaderSHA256())
                        pre_block.append(block.getBlockSHA256())

                    epoch = self.getEpoch()
                    new_block = NewBlockOfBeings(user_pk=user_pk, body_signature=body_signature, body=body, epoch=epoch,
                                                 pre_block=pre_block, prev_block_header=prev_block_header).getBlock()

                    serialization_block = SerializationBeings.serialization(block_of_beings=new_block)
                    # 广播消息
                    block_mess = NetworkMessage(mess_type=NetworkMessageType.NEW_BLOCK,
                                                message=serialization_block).getNetMessage()
                    self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=block_mess)
                    # 保存至当前区块列表
                    self.mainNode.currentBlockList.addBlock(block=new_block)
                else:
                    # 广播无区块产生的消息
                    logger.info("当前节点不生成区块")
                    empty_block = EmptyBlock(user_pk=self.user.getUserPKString(), epoch=self.getEpoch())
                    signature = self.user.sign(str(empty_block.getInfo()).encode("utf-8"))
                    empty_block.setSignature(signature)
                    mess = NetworkMessage(mess_type=NetworkMessageType.NO_BLOCK, message=empty_block.getMessage())
                    self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=mess.getNetMessage())
                    # 保存至当前区块列表
                    self.mainNode.currentBlockList.addMessageOfNoBlock(empty_block=empty_block)
                break
            # 没被选中
        if not is_selected:
            if self.storageOfTemp.getDataCount() < 5:
                webserver_beings_list = self.webServerSDK.getBeings()
                self.storageOfTemp.saveBatchData(webserver_beings_list)

    # 新周期开始30秒后，检查并执行
    def startCheckAndApplyDeleteNode(self):
        logger.info("众生区块生成周期开始30秒，Epoch:" + str(self.getEpoch()) + ",ElectionPeriod:" + str(self.getElectionPeriod()))
        if self.mainNode.currentMainNode.userPKisExit(user_pk=self.user.getUserPKString()):
            # 该节点为本次发布节点的其中之一
            for node in self.mainNode.currentMainNode.getNodeList():
                user_pk = node["node_info"]["user_pk"]
                node_id = node["node_info"]["node_id"]
                # 检查是否存在应该收到，但是未收到的区块
                if not self.mainNode.currentBlockList.userPkIsExit(user_pk=user_pk):
                    logger.info("存在应该产生区块，但是未收到信息的节点")
                    logger.info("节点ID为：" + node_id)
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
                    # 暂存该申请书
                    # 在遇到其他节点申请时直接同意或收到区块后取消
                    self.mainNode.nodeDelApplicationFormList.append(node_del_application_form)

    # 新周期开始40秒后执行
    def startCheckAndGetBlock(self):
        logger.info("众生区块生成周期开始40秒，Epoch:" + str(self.getEpoch()) + ",ElectionPeriod:" + str(self.getElectionPeriod()))
        if not self.mainNode.currentMainNode.userPKisExit(user_pk=self.user.getUserPKString()):
            # 该节点不负责本次区块生成
            for node in self.mainNode.currentMainNode.getNodeList():
                user_pk = node["node_info"]["user_pk"]
                node_id = node["node_info"]["node_id"]
                # 检查是否存在应该收到，但是未收到的区块
                if not self.mainNode.currentBlockList.userPkIsExit(user_pk=user_pk):
                    logger.info("存在应该产生区块，但是未收到信息的节点")
                    logger.info("节点ID为：" + node_id)
                    # 直接发送请求，获取生成的区块
                    network_message = NetworkMessage(NetworkMessageType.APPLY_GET_BLOCK,
                                                     message=self.getEpoch())
                    network_message.setClientInfo(user_pk=self.user.getUserPKString())
                    signature = self.user.sign(message=str(network_message.getCertificationAbstract()).encode("utf-8"))
                    network_message.setSignature(signature)
                    network_message.setSignature(signature)
                    res = self.client.sendMessageByNodeID(node_id=node_id,
                                                          data=str(network_message.getNetMessage()).encode("utf-8"))
                    res = literal_eval(res)
                    if res["mess_type"] == NetworkMessageType.NEW_BLOCK:
                        self.mainNode.currentBlockList.addBlock(block=res["message"])
                    if res["mess_type"] == NetworkMessageType.NO_BLOCK:
                        self.mainNode.currentBlockList.addMessageOfNoBlock(empty_block=res["message"])

    # 检查是否收集完成所有区块，收集完成后保存到数据库
    # 后10秒，每秒检查一次
    def startCheckAndSave(self) -> bool:
        logger.info("众生区块生成周期开始50秒后，Epoch:" + str(self.getEpoch()) + ",ElectionPeriod:" + str(self.getElectionPeriod()))
        is_finish = True
        for node in self.mainNode.currentMainNode.getNodeList():
            user_pk = node["node_info"]["user_pk"]
            node_id = node["node_info"]["node_id"]
            # 检查是否存在应该收到，但是未收到的区块
            if not self.mainNode.currentBlockList.userPkIsExit(user_pk=user_pk):
                is_finish = False
                logger.info("存在未收到的区块,应产生该区块的节点ID为：" + str(node_id))
        if is_finish:
            self.storageOfBeings.saveCurrentBlockOfBeings(blockListOfBeings=self.mainNode.currentBlockList)
            # 存储完成，重置当前区块列表，准备下一个epoch收集
            self.mainNode.currentBlockList.reset()
        return is_finish

    # 开始数据恢复阶段
    def startDataRecovery(self):
        logger.info("进入数据恢复阶段")
        ip_list = []
        for node in self.mainNode.mainNodeList.getNodeList():
            ip_list.append(node["node_info"]["node_ip"])
        i = 0
        last_block_id = ""
        while True:
            ip = random.choice(ip_list)
            net_mess = NetworkMessage(NetworkMessageType.Data_Recovery_Req, message=self.getEpoch())
            # 增加签名
            net_mess.setClientInfo(user_pk=self.user.getUserPKString())
            signature = self.user.sign(message=str(net_mess.getCertificationAbstract()).encode("utf-8"))
            net_mess.setSignature(signature)
            res = self.client.sendMessageByIP(ip, data=str(net_mess.getNetMessage()).encode("utf-8"))
            data = literal_eval(res)
            if data["mess_type"] == NetworkMessageType.No_Data_Recovery:
                continue
            if data["mess_type"] == NetworkMessageType.Data_Recovery:
                block_list = data["message"]
                block_id = ""
                for block_i in block_list:
                    block = SerializationBeings.deserialization(data_of_beings=block_i)
                    block_id += block.getBlockID()
                if last_block_id == block_id:
                    i += 1
                else:
                    last_block_id = block_id
                if i >= 3:
                    block_list_of_beings = BlockListOfBeings()
                    for block_i in block_list:
                        block = SerializationBeings.deserialization(data_of_beings=block_i)
                        block_list_of_beings.addBlock(block)

                    self.storageOfBeings.saveCurrentBlockOfBeings(blockListOfBeings=block_list_of_beings)
                    logging.info("数据恢复成功")
                    break

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
