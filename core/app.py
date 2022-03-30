import random
import logging.config
import time
from ast import literal_eval

from core.data.block_of_beings import EmptyBlock, BlockListOfBeings
from core.data.block_of_galaxy import BodyOfGalaxyBlock, BlockOfGalaxy
from core.data.node_info import NodeInfo
from core.data.network_message import NetworkMessageType, NetworkMessage, SubscribeTopics
from core.data.genesis_block import GenesisBlock
from core.user.user import User
from core.node.main_node import MainNode
from core.network.net import PUB, SUB, Server, Client
from core.consensus.node_management import NodeManager
from core.consensus.block_generate import CurrentMainNode, NewBlockOfBeings, NewBlockOfGalaxy
from core.consensus.vote import VoteCount
from core.consensus.data import VoteInformation, ApplicationForm, ReplyApplicationForm, WaitGalaxyBlock
from core.consensus.data import NodeDelApplicationForm
from core.consensus.block_verify import BlockVerify
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_temp import StorageOfTemp
from core.storage.storage_of_galaxy import StorageOfGalaxy
from core.utils.ciphersuites import CipherSuites
from core.utils.server_sdk import SDK, ChainAsset
from core.utils.serialization import SerializationBeings, SerializationApplicationForm, \
    SerializationReplyApplicationForm, SerializationNetworkMessage
from core.utils.network_request import MainNodeIp
from core.utils.system_time import STime
from core.utils.download import RemoteChainAsset

logger = logging.getLogger("main")


class APP:
    def __init__(self, sk_string, pk_string, server_url):
        self.currentEpoch = 0  # 当前epoch
        self.electionPeriod = 0  # 选举期次

        self.storageOfBeings = StorageOfBeings()  # 众生区块存储类
        self.storageOfTemp = StorageOfTemp()  # 临时区存储类
        self.storageOfGalaxy = StorageOfGalaxy()  # 银河区块存储类

        self.user = User()  # 用户
        self.user.login(sk_string, pk_string)
        self.mainNode = MainNode(self.user, server_url)  # 主节点
        self.nodeManager = NodeManager(user=self.user, main_node=self.mainNode,
                                       storage_of_temp=self.storageOfTemp)  # 节点管理
        self.waitGalaxyBlock = WaitGalaxyBlock(main_node_id=self.mainNode.getNodeId(),
                                               main_user_pk=self.user.getUserPKString())  # 推荐成为银河区块的众生区块列表
        self.voteCount = VoteCount(storage_of_beings=self.storageOfBeings, storage_of_temp=self.storageOfTemp)  # 票数计算
        self.blockVerify = BlockVerify(storage_of_beings=self.storageOfBeings)

        self.pub = PUB()  # 发布者
        self.pub.start()
        self.subList = []  # 订阅列表
        self.client = Client(main_node_list=self.mainNode.mainNodeList)  # 客户端
        self.server = Server(user=self.user, node_manager=self.nodeManager,
                             pub=self.pub, main_node=self.mainNode,
                             storage_of_temp=self.storageOfTemp, wait_galaxy_block=self.waitGalaxyBlock,
                             vote_count=self.voteCount, getEpoch=self.getEpoch, storage_of_galaxy=self.storageOfGalaxy,
                             getElectionPeriod=self.getElectionPeriod, newBlockOfGalaxy=self.newBlockOfGalaxy,
                             current_main_node=self.mainNode.currentMainNode,
                             storage_of_beings=self.storageOfBeings)  # 服务端
        self.server.start()
        # 后端sdk
        self.webServerSDK = SDK()
        # server部分的区块资源
        self.chainAsset = ChainAsset()
        # 其他主节点的区块资源
        self.remoteChainAsset = RemoteChainAsset()

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
                  user=self.user, vote_count=self.voteCount, node_manager=self.nodeManager,
                  main_node=self.mainNode, reSubscribe=self.reSubscribe, storage_of_temp=self.storageOfTemp,
                  getEpoch=self.getEpoch, getElectionPeriod=self.getElectionPeriod,
                  storage_of_galaxy=self.storageOfGalaxy,
                  node_del_application_form_list=self.mainNode.nodeDelApplicationFormList, client=self.client)
        sub.start()
        self.subList.append(sub)

    # 删除订阅
    def delSub(self, ip: str):
        count = len(self.subList)
        for i in range(count):
            if ip == self.subList[i].name:
                self.subList[i].stop()
                del self.subList[i]
                break

    # 删除所有订阅
    def stopAllSub(self, last_sub):
        lastSub = last_sub
        for sub_i in lastSub:
            ip = sub_i.name
            self.delSub(ip)
        logger.info("已删除之前订阅，当前订阅数量为" + str(self.mainNode.mainNodeList.getNodeCount()))

    # 重新订阅32个链接
    def reSubscribe(self):
        logger.info("开始重新订阅")
        lastSub = self.subList.copy()
        node = self.mainNode.mainNodeList.getNodeCount()
        NUMBER_OF_SUBSCRIPTION = 32
        count = NUMBER_OF_SUBSCRIPTION
        if node < NUMBER_OF_SUBSCRIPTION:
            count = node
        node_list = random.sample(self.mainNode.mainNodeList.getNodeList(), count)
        for node_i in node_list:
            ip = node_i["node_info"]["node_ip"]
            self.addSub(ip)
        logger.info("订阅完成，当前订阅数量为" + str(self.mainNode.mainNodeList.getNodeCount()))
        # 删除之前订阅
        self.stopAllSub(lastSub)
        logger.info("重新订阅完成")

    # 读入主节点列表，通过配置文件提供的种子IP
    def loadMainNodeListBySeed(self):
        ip_list = MainNodeIp().getTpList()
        data = NetworkMessage(mess_type=NetworkMessageType.Get_Main_Node_List, message=None)
        serial_data = SerializationNetworkMessage.serialization(data)
        is_get = False
        for ip in ip_list:
            logger.info("连接主节点IP:" + str(ip))
            try:
                res = self.client.sendMessageByIP(ip=ip, data=str(serial_data).encode("utf-8"))
                self.mainNode.mainNodeList.setNodeList(literal_eval(bytes(res).decode("utf-8")))
                logger.info("连接主节点IP:" + str(ip))
                is_get = True
                break
            except Exception as err:
                logger.warning(err)
        return is_get

    # 通过其他主节点获取当前epoch
    def getCurrentEpochByOtherMainNode(self):
        node_ip_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            node_ip_list.append(main_node["node_info"]["node_ip"])
        random.shuffle(node_ip_list)
        serial_data = SerializationNetworkMessage.serialization(
            NetworkMessage(NetworkMessageType.Get_Current_Epoch, message=None))
        for ip in node_ip_list:
            try:
                res = self.client.sendMessageByIP(ip=ip, data=str(serial_data).encode("utf-8"))
                self.setEpoch(int(res))
                break
            except Exception as err:
                logger.warning(err)

    # 同步区块
    def synchronizedBlockOfBeings(self):
        server_url_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            server_url_list.append(main_node["node_info"]["server_url"])
        logger.info("众生区块开始同步")
        # 检测已经存储的区块
        storage_epoch = self.storageOfBeings.getMaxEpoch()
        logger.info("目前已经存储的区块的epoch为：" + str(storage_epoch))
        verify_epoch = self.blockVerify.verifyBlockOfBeings(storage_epoch)
        logger.info("经过验证的存储区块的epoch为：" + str(verify_epoch))
        self.storageOfBeings.delBlocksByEpoch(verify_epoch, storage_epoch)
        if self.getEpoch() > 0:
            start_epoch = 0
            while True:
                server_url = random.choice(server_url_list)
                try:
                    if start_epoch + 1024 < self.getEpoch():
                        end_epoch = start_epoch + 1024
                    else:
                        end_epoch = self.getEpoch()
                    epoch_list = self.remoteChainAsset.getEpochListOfBeingsChain(server_url, start_epoch,
                                                                                 end_epoch - start_epoch)
                    if epoch_list == "500":
                        logger.warning("获取epoch列表失败，server_url:" + server_url)
                        time.sleep(1)
                        continue
                    for epoch_i in epoch_list:
                        logger.info("众生区块同步中,epoch:" + str(epoch_i))
                        server_url = random.choice(server_url_list)
                        block_list_of_beings = self.remoteChainAsset.getChainOfBeings(url=server_url, epoch=epoch_i)
                        i = 0
                        while block_list_of_beings == "500":
                            i += 1
                            logger.warning("第" + str(i) + "次尝试,epoch:" + str(epoch_i) + "server_url:" + server_url)
                            server_url = random.choice(server_url_list)
                            block_list_of_beings = self.remoteChainAsset.getChainOfBeings(url=server_url, epoch=epoch_i)

                        self.chainAsset.saveBatchBlockOfBeings(block_list_of_beings)
                        self.storageOfBeings.saveBatchBlock(block_list_of_beings)

                    logger.info("区块Epoch已经同步至：" + str(end_epoch))
                    if end_epoch == self.getEpoch():
                        logger.info("众生区块同步完成")
                        break
                except Exception as err:
                    logger.warning("区块同步获取失败，远程主节点url:" + server_url)
                    logger.warning(err)
                    time.sleep(1)

    # 数据恢复
    def blockRecoveryOfBeings(self, epoch):
        logger.info("开始恢复众生区块")
        server_url_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            server_url_list.append(main_node["node_info"]["server_url"])
        # 需要检测没有产生区块的节点是否已经被删除
        server_url = random.choice(server_url_list)
        block_list_of_beings = self.remoteChainAsset.getChainOfBeings(url=server_url, epoch=epoch)
        if block_list_of_beings != "500":
            self.chainAsset.saveBatchBlockOfBeings(block_list_of_beings)
            self.storageOfBeings.saveBatchBlock(block_list_of_beings)

    # 存储创世区块
    def storageGenesisBlock(self):
        genesis_block = GenesisBlock().getBlockOfBeings()
        block_list_of_beings = BlockListOfBeings()
        block_list_of_beings.addBlock(block=genesis_block)
        self.storageOfBeings.saveCurrentBlockOfBeings(blockListOfBeings=block_list_of_beings)
        self.chainAsset.saveBlockOfBeings(block_list_of_beings=block_list_of_beings)
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

    # 通过检测数据库中的node_join_other表，当存在is_audit=1或2时,即有消息要回复
    # 回复新节点加入申请，同意或拒绝
    def replyNewNodeJoin(self):
        application_form_list = self.storageOfTemp.getListOfFinishAuditApplicationForm()
        for info in application_form_list:
            reply_application_form = ReplyApplicationForm(new_node_id=info["node_id"], new_node_user_pk=info["user_pk"],
                                                          start_time=info["node_create_time"],
                                                          is_agree=info["is_audit"])
            reply_signature = self.user.sign(str(reply_application_form.getInfo()).encode("utf-8"))
            reply_application_form.setSignature(reply_signature)
            reply_application_form.setUserPk(self.user.getUserPKString())
            serial_reply_application_form = SerializationReplyApplicationForm.serialization(reply_application_form)
            # 消息签名
            network_message = NetworkMessage(mess_type=NetworkMessageType.ReplayNewNodeApplicationJoin,
                                             message=serial_reply_application_form)
            network_message.setClientInfo(user_pk=info["main_node_user_pk"])
            client_signature = self.user.sign(network_message.getClientAndMessageDigest())
            network_message.setSignature(client_signature)
            serial_network_message = SerializationNetworkMessage.serialization(network_message)
            self.client.sendMessageByMainNodeUserPk(user_pk=info["main_node_user_pk"],
                                                    data=str(serial_network_message).encode("utf-8"))

    # 向全网广播新节点申请请求
    # 此时，当前主节点已经审核通过
    def applyNewNodeJoin(self):
        # 调用SDK读取审核通过，但是待广播的主节点加入申请书
        application_form_dict_list = self.webServerSDK.getApplicationForm()
        for application_form_dict in application_form_dict_list:
            node_id = application_form_dict["node_id"]
            user_pk = application_form_dict["user_pk"]
            node_ip = application_form_dict["node_ip"]
            server_url = application_form_dict["server_url"]
            node_create_time = int(application_form_dict["node_create_time"])
            node_signature = application_form_dict["node_signature"]
            application = application_form_dict["application"]
            application_time = STime.getTimestamp()
            application_signature = application_form_dict["application_signature"]
            node_info = NodeInfo(node_id=node_id, user_pk=user_pk, node_ip=node_ip, create_time=node_create_time,
                                 server_url=server_url)
            node_info.nodeSignature = node_signature
            application_form = ApplicationForm(node_info=node_info, start_time=application_time, content=application,
                                               application_signature_by_new_node=application_signature)
            # 验证新节点信息和签名
            if not CipherSuites.verify(pk=user_pk, signature=node_signature,
                                       message=str(node_info.getInfo()).encode("utf-8")):
                # 新节点信息与签名不匹配
                logger.warning("新节点信息与签名不匹配")
                continue
            # 验证申请书和签名
            if not CipherSuites.verify(pk=user_pk, signature=application_signature,
                                       message=str(application).encode("utf-8")):
                # 申请书与新节点签名不匹配
                logger.warning("申请书与新节点签名不匹配")
                continue
            # 增加当前主节点签名
            main_node_signature = self.user.sign(str(application_form.application).encode("utf-8"))
            application_form.setMainNodeSignature(main_node_signature)
            application_form.setMainNodeUserPk(self.user.getUserPKString())
            #  添加数据库数据，准备接受其他主节点的意见
            self.storageOfTemp.insertApplicationForm(node_id=node_id, user_pk=user_pk, node_ip=node_ip,
                                                     server_url=server_url,
                                                     node_create_time=node_create_time, node_signature=node_signature,
                                                     application=application, application_time=application_time,
                                                     application_signature=application_signature,
                                                     agree_count=1, main_node_user_pk=self.user.getUserPKString(),
                                                     main_node_signature=main_node_signature)
            serial_application_form = SerializationApplicationForm.serialization(application_form)
            # 全网广播
            self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfApplyJoin(), message=serial_application_form)

    # 通过检测数据库中的node_join表
    # 当agree_count的值达到一定标准时，立即广播节点加入确认消息
    # 当超过规定时间还未收到确认消息时，删除该申请信息
    def checkNewNodeJoin(self):
        # 获取node_join表中所有is_audit=0的申请表
        for node_id in self.storageOfTemp.getNodeIdListOfWaitingAuditApplicationForm():
            # 检测是否超过有效时间，若超过删除该申请书
            if not self.nodeManager.isTimeReplyApplicationForm(node_id):
                logger.info("该申请书已经超过有效时间，申请书新节点ID为：" + node_id)
                continue
            # 检测是否达到成为新节点的条件
            res = self.nodeManager.isSuccessReplyApplicationForm(node_id)
            if res[0]:
                list_of_serial_reply_application_form = res[1]
                application_form = self.storageOfTemp.getApplicationFormByNodeId(new_node_id=node_id)
                serial_application_form = SerializationApplicationForm.serialization(application_form)
                # 全网广播节点加入确认消息
                self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfJoin(),
                                     message=[serial_application_form, list_of_serial_reply_application_form])
                # 将该节点加入主节点列表
                application_form = self.storageOfTemp.getApplicationFormByNodeId(new_node_id=node_id)
                node_info = NodeInfo(node_id=application_form.newNodeInfo["node_id"],
                                     user_pk=application_form.newNodeInfo["user_pk"],
                                     node_ip=application_form.newNodeInfo["node_ip"],
                                     create_time=application_form.newNodeInfo["create_time"],
                                     server_url=application_form.newNodeInfo["server_url"])
                node_info.setNodeSignature(application_form.newNodeSignature)
                # 检测主节点列表中是否已经有该节点
                if not self.mainNode.mainNodeList.userPKisExit(user_pk=node_info.userPk):
                    self.mainNode.mainNodeList.addMainNode(node_info=node_info)
                    logger.info("新节点已加入，节点信息为：")
                    logger.info(node_info.getInfo())
                    # 将该申请书设置为已经完成申请
                    self.storageOfTemp.finishApplicationFormByNodeId(node_id)
                    # 重新计算订阅列表，重新创建32个订阅链接
                    self.reSubscribe()
                else:
                    logger.warning("节点已经存在，节点ID为：" + node_info.nodeId)

    # 众生区块生成周期
    # 0-30S
    def startNewEpoch(self):
        logger.info("众生区块生成周期开始，Epoch:" + str(self.getEpoch()) + ",ElectionPeriod:" + str(self.getElectionPeriod()))
        # 获取本次产生区块的节点列表
        self.mainNode.currentMainNode = CurrentMainNode(self.mainNode.mainNodeList,
                                                        self.storageOfBeings.getLastBlockByCache(),
                                                        self.getEpoch).getNodeListOfGenerateBlock()
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
                    for block in self.storageOfBeings.getLastBlockList().getListOfOrthogonalOrder():
                        prev_block_header.append(block.getBlockHeaderSHA256())
                        pre_block.append(block.getBlockSHA256())
                    epoch = self.getEpoch()
                    try:
                        new_block = NewBlockOfBeings(user_pk=user_pk, body_signature=body_signature, body=body,
                                                     epoch=epoch,
                                                     pre_block=pre_block,
                                                     prev_block_header=prev_block_header).getBlock()
                        serialization_block = SerializationBeings.serialization(block_of_beings=new_block)
                        # 广播消息
                        serial_block_mess = SerializationNetworkMessage.serialization(
                            NetworkMessage(mess_type=NetworkMessageType.NEW_BLOCK, message=serialization_block))
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=serial_block_mess)
                        # 保存至当前区块列表
                        self.mainNode.currentBlockList.addBlock(block=new_block)
                    except Exception as err:
                        # 产生错误（如签名验证错误）后，发送不产生区块消息
                        logger.error(err)
                        # 广播无区块产生的消息
                        logger.info("当前节点不生成区块")
                        empty_block = EmptyBlock(user_pk=self.user.getUserPKString(), epoch=self.getEpoch())
                        signature = self.user.sign(str(empty_block.getInfo()).encode("utf-8"))
                        empty_block.setSignature(signature)
                        mess = NetworkMessage(mess_type=NetworkMessageType.NO_BLOCK, message=empty_block.getMessage())
                        serial_mess = SerializationNetworkMessage.serialization(mess)
                        # 保存至当前区块列表
                        self.mainNode.currentBlockList.addMessageOfNoBlock(empty_block=empty_block)
                        self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=serial_mess)
                else:
                    # 广播无区块产生的消息
                    logger.info("当前节点不生成区块")
                    empty_block = EmptyBlock(user_pk=self.user.getUserPKString(), epoch=self.getEpoch())
                    signature = self.user.sign(str(empty_block.getInfo()).encode("utf-8"))
                    empty_block.setSignature(signature)
                    mess = NetworkMessage(mess_type=NetworkMessageType.NO_BLOCK, message=empty_block.getMessage())
                    serial_mess = SerializationNetworkMessage.serialization(mess)
                    # 保存至当前区块列表
                    self.mainNode.currentBlockList.addMessageOfNoBlock(empty_block=empty_block)
                    self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfBeings(), message=serial_mess)
                break
            # 没被选中
        if not is_selected:
            # 读取待发布的众生区块
            if self.storageOfTemp.getDataCount() < 5:
                logger.info("检测server是否有待发布的区块")
                webserver_beings_list = self.webServerSDK.getBeings()
                self.storageOfTemp.saveBatchData(webserver_beings_list)
            # 检测有无已经审核通过的，提交在本节点的申请书
            logger.info("检测有无已经审核通过的，提交在本节点的申请书")
            self.applyNewNodeJoin()
            # 检测有无已经审核通过的，从其他主节点接受到的申请书
            logger.info("检测有无已经审核通过的，从其他主节点接受到的申请书")
            self.replyNewNodeJoin()
            # 检测是否有投票完成确认加入或被拒绝加入主节点的申请书
            logger.info("检测是否有投票完成确认加入或被拒绝加入主节点的申请书")
            self.checkNewNodeJoin()

    # 新周期开始30秒后，检查并执行
    def startCheckAndApplyDeleteNode(self):
        logger.info("众生区块生成周期开始30秒，Epoch:" + str(self.getEpoch()) + ",ElectionPeriod:" + str(self.getElectionPeriod()))
        node_of_check_node = CurrentMainNode(self.mainNode.mainNodeList, self.storageOfBeings.getLastBlockByCache(),
                                             self.getEpoch).getNodeListOfCheckNode()
        # 检测当前节点是否为本次发布节点的其中之一
        # 检测当前节点是否为有权限发送广播
        # 满足上述一项即可
        if self.mainNode.currentMainNode.userPKisExit(
                user_pk=self.user.getUserPKString()) or \
                node_of_check_node.userPKisExit(user_pk=self.user.getUserPKString()):
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

    # 检查是否收集完成所有区块，收集完成后保存到数据库
    # 每秒检查一次
    def startCheckAndSave(self) -> bool:
        logger.info("众生区块生成周期开始40秒后，Epoch:" + str(self.getEpoch()) + ",ElectionPeriod:" + str(self.getElectionPeriod()))
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
            self.chainAsset.saveBlockOfBeings(block_list_of_beings=self.mainNode.currentBlockList)
            # 存储完成，重置当前区块列表，准备下一个epoch收集
            self.mainNode.currentBlockList.reset()
        if self.chainAsset.beingsIsExitByEpoch(self.getEpoch()):
            return True
        return is_finish

    # 生成时代区块
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
