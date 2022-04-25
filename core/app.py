import hashlib
import random
import logging.config
import threading
import time
from ast import literal_eval

from core.data.block_of_beings import EmptyBlock, BlockListOfBeings
from core.data.block_of_garbage import BodyOfGarbageBlock
from core.data.block_of_times import BodyOfTimesBlock
from core.data.node_info import NodeInfo
from core.data.network_message import NetworkMessageType, NetworkMessage, SubscribeTopics
from core.data.genesis_block import GenesisBlock
from core.storage.storage_of_garbage import StorageOfGarbage
from core.user.user import User
from core.node.main_node import MainNode
from core.network.net import PUB, SUB, Server, Client
from core.consensus.node_management import NodeManager
from core.consensus.block_generate import CurrentMainNode, NewBlockOfBeings, NewBlockOfTimes, NewBlockOfGarbage
from core.consensus.vote_compute import VoteCount
from core.consensus.data import ApplicationForm, ReplyApplicationForm, VoteMessage, LongTermVoteMessage, \
    ApplicationFormActiveDelete, ReplyApplicationFormActiveDelete
from core.consensus.data import NodeDelApplicationForm
from core.consensus.block_verify import BlockVerify
from core.storage.storage_of_beings import StorageOfBeings
from core.storage.storage_of_temp import StorageOfTemp
from core.storage.storage_of_galaxy import StorageOfGalaxy
from core.utils.ciphersuites import CipherSuites
from core.utils.server_sdk import SDK, ChainAsset
from core.utils.serialization import SerializationBeings, SerializationApplicationForm, \
    SerializationReplyApplicationForm, SerializationNetworkMessage, SerializationVoteMessage, SerializationTimes, \
    SerializationLongTermVoteMessage, SerializationGarbage, SerializationApplicationFormActiveDelete, \
    SerializationReplyApplicationFormActiveDelete
from core.utils.network_request import MainNodeIp
from core.utils.system_time import STime
from core.utils.download import RemoteChainAsset
from core.config.cycle_Info import ElectionPeriodValue

logger = logging.getLogger("main")


class APP:
    def __init__(self, sk_string, pk_string, server_url):
        self.currentEpoch = 0  # 当前epoch

        self.storageOfBeings = StorageOfBeings()  # 众生区块存储类
        self.storageOfTemp = StorageOfTemp()  # 临时区存储类
        self.storageOfGalaxy = StorageOfGalaxy()  # 时代区块存储类
        self.storageOfGarbage = StorageOfGarbage()  # 垃圾区块存储类

        self.user = User()  # 用户
        self.user.login(sk_string, pk_string)
        self.mainNode = MainNode(self.user, server_url, self.storageOfTemp)  # 主节点
        self.nodeManager = NodeManager(user=self.user, main_node=self.mainNode,
                                       storage_of_temp=self.storageOfTemp)  # 节点管理
        self.voteCount = VoteCount(storage_of_beings=self.storageOfBeings, storage_of_temp=self.storageOfTemp,
                                   main_node=self.mainNode, storage_of_times=self.storageOfGalaxy,
                                   storage_of_garbage=self.storageOfGarbage)  # 票数计算
        self.blockVerify = BlockVerify(storage_of_beings=self.storageOfBeings)
        self.pub = PUB()  # 发布者
        self.pub.start()
        self.subList = []  # 订阅列表
        self.client = Client(main_node_list=self.mainNode.mainNodeList)  # 客户端
        self.server = Server(user=self.user, node_manager=self.nodeManager, pub=self.pub, main_node=self.mainNode,
                             storage_of_temp=self.storageOfTemp, vote_count=self.voteCount, getEpoch=self.getEpoch,
                             getElectionPeriod=self.getElectionPeriod)  # 服务端
        self.server.start()
        # 后端sdk
        self.webServerSDK = SDK()
        # server部分的区块资源
        self.chainAsset = ChainAsset()
        # 其他主节点的区块资源
        self.remoteChainAsset = RemoteChainAsset()

    def addEpoch(self):
        self.currentEpoch += 1
        self.storageOfTemp.setEpoch(self.currentEpoch)

    def getEpoch(self):
        logger.info("当前Epoch：" + str(self.currentEpoch))
        return self.currentEpoch

    def setEpoch(self, epoch):
        self.currentEpoch = epoch
        self.storageOfTemp.setEpoch(epoch)

    def getElectionPeriod(self):
        current_election_period = int(self.getEpoch() / ElectionPeriodValue)
        logger.info("当前ElectionPeriod：" + str(current_election_period))
        return current_election_period

    # 周期处理的事件，单独线程执行
    def dealPeriodicEvents(self_out):
        class PeriodicEvents(threading.Thread):
            def __init__(self):
                super().__init__()
                self.name = "periodic_events"
                logger.info("周期事件处理器初始化完成")

            def run(self) -> None:
                logger.info("周期事件处理器启动完成")
                while True:
                    try:
                        if self_out.getEpoch() % ElectionPeriodValue == 0 and self_out.getEpoch() != 0:
                            logger.info("周期事件处理器暂停半小时")
                            time.sleep(60)
                        else:
                            time.sleep(30)
                        logger.info("周期事件开始处理")
                        # 读取待发布的众生区块
                        if self_out.storageOfTemp.getDataCount() < 5:
                            logger.info("检测server是否有待发布的区块")
                            webserver_beings_list = self_out.webServerSDK.getBeings()
                            self_out.storageOfTemp.saveBatchData(webserver_beings_list)
                        # 检测有无已经审核通过的，提交在本节点的申请书
                        logger.info("检测有无已经审核通过的，提交在本节点的申请书")
                        self_out.applyNewNodeJoin()

                        # 检测有无已经审核通过的，从其他主节点接受到的申请书
                        logger.info("检测有无已经审核通过的，从其他主节点接受到的申请书")
                        self_out.replyNewNodeJoin()

                        # 检测是否有投票完成确认加入或被拒绝加入主节点的申请书
                        logger.info("检测是否有投票完成确认加入或被拒绝加入主节点的申请书")
                        self_out.checkNewNodeJoin()

                        # 检测有无已经审核通过的，提交在本节点的申请书(主动删除节点)
                        logger.info("检测有无待广播的该主节点提交的申请书（主动删除节点）")
                        self_out.applyNodeDelete()

                        # 检测有无已经审核通过的，从其他主节点接受到的申请书(主动删除节点)
                        logger.info("检测有无已经审核通过的，从其他主节点接受到的申请书(主动删除节点)")
                        self_out.replyNodeActiveDelete()

                        # 检测是否有投票完成,同意删除节点或不同意删除
                        logger.info("检测是否有投票完成,同意删除节点或不同意删除")
                        self_out.checkNodActiveDelete()

                        logger.info("检测是否有待广播的短期票投票消息")
                        # 检测是否有待广播的短期票投票消息
                        self_out.broadcastVotingInfo()

                        # 检测是否有待广播的长期票消息
                        logger.info("检测是否有待广播的长期票消息")
                        self_out.broadcastLongTermVotingInfo()

                        # 检测是否有待生成的时代区块
                        logger.info("检测是否有待生成的时代区块")
                        self_out.checkAndGenerateBlockOfTimes()

                        # 检测是否有待生成的垃圾区块
                        logger.info("检测是否有待生成的垃圾区块")
                        self_out.checkAndGenerateBlockOfGarbage()
                        logger.info("周期事件处理完成")
                    except Exception as err:
                        logging.error("周期事件出现错误")
                        logging.exception(err)

        periodic_events = PeriodicEvents()
        periodic_events.start()

    # 增加订阅
    def addSub(self, ip):
        sub = SUB(ip=ip, pub=self.pub, blockListOfBeings=self.mainNode.currentBlockList,
                  web_server_sdk=self.webServerSDK, storage_of_garbage=self.storageOfGarbage,
                  user=self.user, vote_count=self.voteCount, node_manager=self.nodeManager,
                  main_node=self.mainNode, reSubscribe=self.reSubscribe, storage_of_temp=self.storageOfTemp,
                  getEpoch=self.getEpoch, getElectionPeriod=self.getElectionPeriod,
                  storage_of_galaxy=self.storageOfGalaxy, storage_of_beings=self.storageOfBeings,
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
        ip_list = MainNodeIp().getIpList()
        logger.info("已经获得主节点列表")
        logger.info(ip_list)
        data = NetworkMessage(mess_type=NetworkMessageType.Get_Main_Node_List, message=None)
        serial_data = SerializationNetworkMessage.serialization(data)
        is_get = False
        for ip in ip_list:
            logger.info("连接主节点IP:" + str(ip))
            try:
                res = self.client.sendMessageByIP(ip=ip, data=str(serial_data).encode("utf-8"))
                self.mainNode.mainNodeList.setNodeList(literal_eval(bytes(res).decode("utf-8")))
                logger.info("已经连接主节点,IP:" + str(ip))
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
        while True:
            ip = random.choice(node_ip_list)
            try:
                res = self.client.sendMessageByIP(ip=ip, data=str(serial_data).encode("utf-8"))
                if self.getEpoch() == int(res):
                    return True
                else:
                    self.setEpoch(int(res))
                    return False
            except Exception as err:
                time.sleep(1)
                logger.warning(err)

    # 同步众生区块
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
            start_epoch = verify_epoch
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
                    start_epoch = end_epoch
                except Exception as err:
                    logger.warning("众生区块同步获取失败，远程主节点url:" + server_url)
                    logger.warning(err)
                    time.sleep(1)

    # 同步时代区块
    def synchronizedBlockOfTimes(self):
        server_url_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            server_url_list.append(main_node["node_info"]["server_url"])
        logger.info("时代区块开始同步")
        if self.getEpoch() > 0:
            start_election_period = 0
            while True:
                server_url = random.choice(server_url_list)
                try:
                    res = self.remoteChainAsset.getChainOfTimes(url=server_url, election_period=start_election_period)
                    if res != "500":
                        if res == "404":
                            start_election_period += 1
                        else:
                            self.storageOfGalaxy.addBatchBlockOfGalaxy(block_list_of_galaxy=res)
                            self.chainAsset.saveBlockOfTimes(res)
                            start_election_period += 1
                    else:
                        logger.warning("时代区块同步获取失败，远程主节点url:" + server_url)
                        time.sleep(1)
                    if start_election_period >= self.getElectionPeriod():
                        logger.info("时代区块同步完成")
                        break
                except Exception as err:
                    logger.warning("时代区块同步获取失败，远程主节点url:" + server_url)
                    logger.warning(err)
                    time.sleep(1)

    # 同步垃圾区块
    def synchronizedBlockOfGarbage(self):
        server_url_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            server_url_list.append(main_node["node_info"]["server_url"])
        logger.info("时代区块开始同步")
        if self.getEpoch() > 0:
            start_election_period = 0
            while True:
                server_url = random.choice(server_url_list)
                try:
                    res = self.remoteChainAsset.getChainOfGarbage(url=server_url, election_period=start_election_period)
                    if res != "500":
                        if res == "404":
                            start_election_period += 1
                        else:
                            self.storageOfGarbage.addBatchBlockOfGarbage(block_list_of_garbage=res)
                            self.chainAsset.saveBlockOfGarbage(res)
                            start_election_period += 1
                    else:
                        logger.warning("时代区块同步获取失败，远程主节点url:" + server_url)
                        time.sleep(1)
                    if start_election_period >= self.getElectionPeriod():
                        logger.info("时代区块同步完成")
                        break
                except Exception as err:
                    logger.warning("时代区块同步获取失败，远程主节点url:" + server_url)
                    logger.warning(err)
                    time.sleep(1)

    # 数据恢复
    def blockRecoveryOfBeings(self):
        logger.info("开始恢复众生区块")
        info_list = []
        for main_node in self.mainNode.mainNodeList.getNodeList():
            info_list.append([main_node["node_info"]["server_url"], main_node["node_info"]["node_ip"]])
        info = random.choice(info_list)
        logger.info("获取最新期次数量")
        i = 0
        is_sync = self.remoteChainAsset.getCurrentEpoch(self.getEpoch, self.client, info[1])
        while is_sync <= 0:
            i += 1
            logger.warning("获取最新期次数量失败，第" + str(i) + "次尝试")
            info = random.choice(info_list)
            is_sync = self.remoteChainAsset.getCurrentEpoch(self.getEpoch, self.client, info[1])

        epoch_list = self.remoteChainAsset.getEpochListOfBeingsChain(url=info[0], offset=self.getEpoch(), count=is_sync)
        logger.info("获取未同步的期次列表")
        i = 0
        while epoch_list == "500":
            i += 1
            logger.warning("获取未同步的期次列表失败，第" + str(i) + "次尝试")
            epoch_list = self.remoteChainAsset.getEpochListOfBeingsChain(url=info[0], offset=self.getEpoch(),
                                                                         count=is_sync)
        for epoch_i in epoch_list:
            info = random.choice(info_list)
            block_list_of_beings = self.remoteChainAsset.getChainOfBeings(url=info[0], epoch=epoch_i)

            while block_list_of_beings == "500":
                info = random.choice(info_list)
                block_list_of_beings = self.remoteChainAsset.getChainOfBeings(url=info[0], epoch=epoch_i)

            # 此时该期次的区块已经同步完成
            self.storageOfBeings.saveBatchBlock(block_list_of_beings)
            self.chainAsset.saveBatchBlockOfBeings(block_list_of_beings)
            logger.info("epoch:" + str(epoch_i) + ",众生区块恢复完成")
        self.mainNode.currentBlockList.setFinish()
        logger.info("众生区块全部恢复完成")

    # 存储创世区块
    def storageGenesisBlock(self):
        genesis_block = GenesisBlock()
        block_list_of_beings = BlockListOfBeings()
        block_list_of_beings.addBlock(block=genesis_block.getBlockOfBeings())
        self.storageOfBeings.saveCurrentBlockOfBeings(blockListOfBeings=block_list_of_beings)
        self.chainAsset.saveBlockOfBeings(block_list_of_beings=block_list_of_beings)
        logger.info("众生创世区块存储完成")
        block_of_times = genesis_block.getBlockOfTimes()
        self.storageOfGalaxy.addBlockOfGalaxy(block_of_galaxy=block_of_times)
        self.chainAsset.saveBlockOfTimes([block_of_times])
        logger.info("时代创世区块存储完成")
        block_of_garbage = genesis_block.getBlockOfGarbage()
        self.storageOfGarbage.addBlockOfGarbage(block_of_garbage=block_of_garbage)
        self.chainAsset.saveBlockOfGarbage([block_of_garbage])
        logger.info("垃圾创世区块存储完成")

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

    # 通过检测数据库中的node_delete_other_active表，当存在is_audit=1或2时,即有消息要回复
    # 回复主节点删除申请
    def replyNodeActiveDelete(self):
        application_form_active_delete = self.storageOfTemp.getFinishApplicationFormActiveDelete()
        if application_form_active_delete is None:
            return
        del_node_id = application_form_active_delete["del_node_id"]
        application_content = application_form_active_delete["application_content"]
        application_time = application_form_active_delete["application_time"]
        is_audit = application_form_active_delete["is_audit"]
        main_node_user_pk = application_form_active_delete["main_node_user_pk"]
        main_node_signature = application_form_active_delete["main_node_signature"]

        reply_application_form_active_delete = ReplyApplicationFormActiveDelete(del_node_id=del_node_id,
                                                                                start_time=application_time,
                                                                                is_agree=is_audit,
                                                                                apply_user_pk=main_node_user_pk)
        reply_signature = self.user.sign(str(reply_application_form_active_delete.getInfo()).encode("utf-8"))
        reply_application_form_active_delete.setSignature(reply_signature)
        reply_application_form_active_delete.setUserPk(self.user.getUserPKString())
        serial_reply_application_form_active_delete = SerializationReplyApplicationFormActiveDelete.serialization(
            reply_application_form_active_delete)
        # 消息签名
        network_message = NetworkMessage(mess_type=NetworkMessageType.ReplyNodeActiveDeleteApplication,
                                         message=serial_reply_application_form_active_delete)
        network_message.setClientInfo(user_pk=self.user.getUserPKString())
        client_signature = self.user.sign(network_message.getClientAndMessageDigest())
        network_message.setSignature(client_signature)
        serial_network_message = SerializationNetworkMessage.serialization(network_message)
        self.client.sendMessageByMainNodeUserPk(user_pk=main_node_user_pk,
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

    # 向全网广播主动删除节点申请请求
    def applyNodeDelete(self):
        # 调用SDK读取，待广播的主动删除某主节点的申请书
        application_form_active_delete_dict_list = self.webServerSDK.getApplicationFormActiveDelete()
        for application_form_active_delete_dict in application_form_active_delete_dict_list:
            node_id = application_form_active_delete_dict["node_id"]
            application_content = application_form_active_delete_dict["application_content"]
            application_time = STime.getTimestamp()
            application_form_active_delete = ApplicationFormActiveDelete(del_node_id=node_id,
                                                                         start_time=application_time,
                                                                         content=application_content)
            signature = self.user.sign(str(application_form_active_delete.getInfo()).encode("utf-8"))
            application_form_active_delete.setMainNodeSignature(signature)
            application_form_active_delete.setMainNodeUserPk(self.user.getUserPKString())
            # 验证申请书和签名
            if not CipherSuites.verify(pk=application_form_active_delete.getMainNodeUserPk(),
                                       signature=application_form_active_delete.getMainNodeSignature(),
                                       message=str(application_form_active_delete.getInfo()).encode("utf-8")):
                # 申请书与新节点签名不匹配
                logger.warning("申请书签名不匹配")
                continue
            # 增加当前主节点签名
            #  添加数据库数据，准备接受其他主节点的意见
            self.storageOfTemp.insertApplicationFormActiveDelete(node_id=node_id,
                                                                 application_content=application_content,
                                                                 application_time=application_time,
                                                                 main_node_signature=signature,
                                                                 main_node_user_pk=self.user.getUserPKString())
            serial_application_form_active_delete = SerializationApplicationFormActiveDelete.serialization(
                application_form_active_delete)
            # 广播
            self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfActiveApplyDelete(),
                                 message=serial_application_form_active_delete)

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

    # 当agree_count的值达到一定标准时，立即广播消息
    # 当超过规定时间还未收到确认消息时，删除该申请信息
    def checkNodActiveDelete(self):
        # 获取node_active_delete表中所有is_audit=0的申请表
        for node_id in self.storageOfTemp.getNodeIdListOfApplicationFormActiveDeleteInProgress():
            # 检测是否超过有效时间，若超过删除该申请书
            if not self.nodeManager.isTimeReplyApplicationFormActiveDelete(node_id):
                logger.info("该申请书已经超过有效时间,申请删除的节点ID为：" + node_id)
                continue
            # 检测是否达到成为新节点的条件
            res = self.nodeManager.isSuccessReplyApplicationFormActiveDelete(node_id)
            if res[0]:
                list_of_serial_reply_application_form_active_delete = res[1]
                application_form_active_delete = self.storageOfTemp.getApplicationFormActiveDeleteByNodeId(
                    del_node_id=node_id,
                    is_audit=0)
                serial_application_form_active_delete = SerializationApplicationFormActiveDelete.serialization(
                    application_form_active_delete)
                # 删除主节点
                self.mainNode.mainNodeList.delMainNodeById(node_id=application_form_active_delete.delNodeId)
                # 重新订阅
                self.reSubscribe()
                # 全网广播节点加入确认消息
                self.pub.sendMessage(topic=SubscribeTopics.getNodeTopicOfActiveConfirmDelete(),
                                     message=[serial_application_form_active_delete,
                                              list_of_serial_reply_application_form_active_delete])

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
        for node in self.mainNode.currentMainNode.getNodeList():
            # 当前节点是否生成区块
            if node["node_info"]["node_id"] == self.mainNode.nodeInfo.nodeId:
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
                                                     epoch=epoch, pre_block=pre_block,
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
                        logger.error(err, exc_info=True, stack_info=True)
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
        if not self.mainNode.currentBlockList.isFinish:
            logger.debug("收集到的空区块消息")
            for emptyBlock in self.mainNode.currentBlockList.listOfNoBlock:
                logger.debug(emptyBlock.getMessage())
            logger.debug("收集到的区块消息")
            for block in self.mainNode.currentBlockList.list:
                logger.debug(block.getBlockHeader())
            for node in self.mainNode.currentMainNode.getNodeList():
                user_pk = node["node_info"]["user_pk"]
                node_id = node["node_info"]["node_id"]
                # 检查是否存在应该收到，但是未收到的区块
                # 区块消息
                if not self.chainAsset.beingsIsExitByEpoch(self.getEpoch()):
                    if (not self.mainNode.currentBlockList.userPkIsBlock(
                            user_pk) and (not self.mainNode.currentBlockList.userPkIsEmptyBlock(user_pk))):
                        is_finish = False
                        logger.info("存在未收到的区块,应产生该区块的节点ID为：" + str(node_id))
        if is_finish:
            if not self.chainAsset.beingsIsExitByEpoch(self.getEpoch()):
                self.storageOfBeings.saveCurrentBlockOfBeings(blockListOfBeings=self.mainNode.currentBlockList)
                self.chainAsset.saveBlockOfBeings(block_list_of_beings=self.mainNode.currentBlockList)
                # 存储完成，重置当前区块列表，准备下一个epoch收集
            self.mainNode.currentBlockList.reset()
        return is_finish

    # 每个选举周期开始前
    # 初始化所有主节点的投票信息
    # 初始化所有拥有长期票的普通用户的票数信息
    def initVote(self_out):
        class InitVoteOfMainNode(threading.Thread):
            def __init__(self):
                super().__init__()
                self.name = "init_vote"
                self.current_election_period = self_out.getElectionPeriod()
                logger.info("init_vote初始化完成")

            def run(self) -> None:
                logger.info("开始计算所有主节点的票数信息")
                # 主节点用户
                # 初始化本次的票数数据
                self_out.voteCount.initVotesOfMainNode(current_election_cycle=self.current_election_period)
                # 普通用户的长期票
                self_out.voteCount.initPermanentVotesOfSimpleUser(current_election_cycle=self.current_election_period)
                logger.info("计算完成")

        init_vote_of_main_node = InitVoteOfMainNode()
        init_vote_of_main_node.start()

    def saveAssetOfTimesAndGarbage(self_out):
        class SaveAsset(threading.Thread):
            def __init__(self):
                super().__init__()
                self.name = "save_asset"
                self.current_election_period = self_out.getElectionPeriod()
                self.chainAsset = self_out.chainAsset
                self.storageOfGalaxy = self_out.storageOfGalaxy
                self.storageOfGarbage = self_out.storageOfGarbage
                logger.info("save_asset初始化完成")

            def run(self) -> None:
                logger.info("开始保存时代区块列表和垃圾区块列表，选举周期为：" + str(self.current_election_period))
                list_of_times = self.storageOfGalaxy.getListOfGalaxyBlockByElectionPeriod(
                    start=self.current_election_period - 1,
                    end=self.current_election_period)
                self.chainAsset.saveBlockOfTimes(block_list_of_times=list_of_times)
                list_of_garbage = self.storageOfGarbage.getListOfGarbageBlockByElectionPeriod(
                    start=self.current_election_period - 1,
                    end=self.current_election_period)
                self.chainAsset.saveBlockOfGarbage(block_list_of_garbage=list_of_garbage)
                logger.info("保存完成")

        save_asset = SaveAsset()
        save_asset.start()

    # 广播短期票投票消息
    def broadcastVotingInfo(self):
        logger.info("广播短期票投票消息")
        wait_vote_list = self.storageOfTemp.getVoteMessage(status=0)
        for wait_vote in wait_vote_list:
            logger.debug("待广播短期票投票消息")
            logger.debug(wait_vote.getMessage())
            # 验证投票信息签名
            if not CipherSuites.verify(pk=wait_vote.simpleUserPk, signature=wait_vote.getSignature(),
                                       message=str(wait_vote.getInfoOfSignature()).encode("utf-8")):
                logger.warning("签名验证失败,短期票投票信息为:")
                logger.warning(wait_vote.getInfo())
                # 将待广播短期票投票信息状态设为2
                self.storageOfTemp.modifyStatusOfWaitVote(status=2, wait_vote=wait_vote)
                continue
            # 封装短期票投票消息
            # 将toNodeId转为toNodeUserPk
            # 将普通用户公钥转为主节点用户公钥
            vote_message = VoteMessage()
            to_main_node_info = self.mainNode.mainNodeList.getMainNodeByNodeId(node_id=wait_vote.toNodeId)
            vote_message.setVoteInfo(to_main_node_user_pk=to_main_node_info["node_info"]["user_pk"],
                                     block_id=wait_vote.blockId, vote_type=wait_vote.voteType,
                                     election_period=wait_vote.electionPeriod, number_of_vote=wait_vote.vote,
                                     main_user_pk=self.user.getUserPKString())
            main_node_signature = self.user.sign(str(vote_message.getVoteInfo()).encode("utf-8"))
            vote_message.setSignature(main_node_signature)
            # 增加普通用户和主节点用户已使用的票数
            self.webServerSDK.addUsedVoteOfSimpleUser(user_pk=wait_vote.simpleUserPk, used_vote=wait_vote.vote,
                                                      election_period=self.getElectionPeriod())
            self.storageOfTemp.addUsedVoteByNodeUserPk(vote=wait_vote.vote,
                                                       main_node_user_pk=self.user.getUserPKString())
            # 暂存短期票投票消息摘要
            self.storageOfTemp.addVoteDigest(election_period=vote_message.electionPeriod, block_id=vote_message.blockId,
                                             vote_message_digest=hashlib.md5(
                                                 str(vote_message.getVoteMessage()).encode("utf-8")).hexdigest())

            # 该短期票投票是否是针对当前主节点推荐的区块
            if self.webServerSDK.isExitTimesBlockQueueByBlockId(
                    vote_message.blockId) and self.user.getUserPKString() == vote_message.toMainNodeUserPk and int(
                vote_message.voteType) == 1:
                self.webServerSDK.addVoteOfTimesBlockQueue(beings_block_id=vote_message.blockId,
                                                           vote_message=vote_message)
            if self.webServerSDK.isExitGarbageBlockQueueByBlockId(
                    vote_message.blockId) and self.user.getUserPKString() == vote_message.toMainNodeUserPk and int(
                vote_message.voteType) == 2:
                self.webServerSDK.addVoteOfGarbageBlockQueue(beings_block_id=vote_message.blockId,
                                                             vote_message=vote_message)
            # 修改读取到的短期票投票信息状态
            self.storageOfTemp.modifyStatusOfWaitVote(status=1, wait_vote=wait_vote)
            # 广播
            self.pub.sendMessage(topic=SubscribeTopics.getVoteMessage(),
                                 message=SerializationVoteMessage.serialization(vote_message=vote_message))
            logger.debug("短期票广播完成")

    # 广播长期票投票消息
    def broadcastLongTermVotingInfo(self):
        logger.info("广播长期票投票消息")
        long_term_wait_vote_list = self.storageOfTemp.getLongTermVoteMessage(status=0)
        for long_term_wait_vote in long_term_wait_vote_list:
            logger.debug("待广播长期票投票消息")
            logger.debug(long_term_wait_vote.getMessage())
            # 验证投票信息签名
            if not CipherSuites.verify(pk=long_term_wait_vote.simpleUserPk,
                                       signature=long_term_wait_vote.getSignature(),
                                       message=str(long_term_wait_vote.getInfoOfSignature()).encode("utf-8")):
                logger.warning("签名验证失败,长期投票信息为:")
                logger.warning(long_term_wait_vote.getInfo())
                # 将待广播短期票投票信息状态设为2
                self.storageOfTemp.modifyStatusOfLongTermWaitVote(status=2, wait_vote=long_term_wait_vote)
                continue
            # 增加普通用户已使用的长期票票数
            self.storageOfTemp.addUsedPermanentVoteOfSimpleUser(vote=long_term_wait_vote.vote,
                                                                simple_user_pk=long_term_wait_vote.simpleUserPk)
            # 封装长期票消息
            long_term_vote_message = LongTermVoteMessage()
            long_term_vote_message.setVoteInfo(to_main_node_id=long_term_wait_vote.toNodeId,
                                               block_id=long_term_wait_vote.blockId,
                                               vote_type=long_term_wait_vote.voteType,
                                               election_period=long_term_wait_vote.electionPeriod,
                                               number_of_vote=long_term_wait_vote.vote,
                                               simple_user_pk=long_term_wait_vote.simpleUserPk)
            long_term_vote_message.setSignature(signature=long_term_wait_vote.getSignature())
            # 暂存短期票投票消息摘要
            self.storageOfTemp.addVoteDigest(election_period=long_term_vote_message.electionPeriod,
                                             block_id=long_term_vote_message.blockId,
                                             vote_message_digest=hashlib.md5(
                                                 str(long_term_vote_message.getVoteMessage()).encode(
                                                     "utf-8")).hexdigest())

            # 该长期票投票是否是针对当前主节点推荐的区块
            to_main_node_info = self.mainNode.mainNodeList.getMainNodeByNodeId(node_id=long_term_wait_vote.toNodeId)
            to_main_node_user_pk = to_main_node_info["node_info"]["user_pk"]
            if self.webServerSDK.isExitTimesBlockQueueByBlockId(
                    long_term_vote_message.blockId) and self.user.getUserPKString() == to_main_node_user_pk and long_term_vote_message.voteType == 1:
                self.webServerSDK.addPermanentVoteOfTimesBlockQueue(beings_block_id=long_term_vote_message.blockId,
                                                                    long_term_vote_message=long_term_vote_message)
            if self.webServerSDK.isExitGarbageBlockQueueByBlockId(
                    long_term_vote_message.blockId) and self.user.getUserPKString() == to_main_node_user_pk and long_term_vote_message.voteType == 2:
                self.webServerSDK.addPermanentVoteOfGarbageBlockQueue(beings_block_id=long_term_vote_message.blockId,
                                                                      long_term_vote_message=long_term_vote_message)
            # 修改读取到的长期票投票信息状态
            self.storageOfTemp.modifyStatusOfLongTermWaitVote(status=1, wait_vote=long_term_wait_vote)
            # 广播
            self.pub.sendMessage(topic=SubscribeTopics.getLongTermVoteMessage(),
                                 message=SerializationLongTermVoteMessage.serialization(
                                     long_term_vote_message=long_term_vote_message))
            logger.debug("长期票广播完成")

    # 检测并且生成时代区块
    def checkAndGenerateBlockOfTimes(self):
        logger.info("检测并且生成时代区块")
        # 检测是否有投票数量达到要求的时代区块
        vote_of_times_block = self.voteCount.getVotesOfTimesBlockGenerate()
        res = self.webServerSDK.getTimesBlockQueueByVotes(votes=vote_of_times_block)
        if res is not None:
            # 再次验证投票
            beings_block_id = res["beings_block_id"]
            serial_vote_list = res["vote_list"]
            vote_message_list = []
            for vote_i in serial_vote_list:
                # 判断是长期票还是短期票
                if "main_user_pk" in vote_i:
                    # 短期票
                    vote_message_list.append(SerializationVoteMessage.deserialization(str(vote_i).encode("utf-8")))
                else:
                    # 长期票
                    vote_message_list.append(
                        SerializationLongTermVoteMessage.deserialization(str(vote_i).encode("utf-8")))
            if self.voteCount.checkVotesOfGenerateTimesBlock(beings_block_id=beings_block_id,
                                                             vote_message_list=vote_message_list):
                logger.info("生在生成时代区块,原众生区块ID为:" + beings_block_id)
                # 修改状态
                self.webServerSDK.modifyStatusOfTimesBlockQueue(beings_block_id=beings_block_id, status=2)
                beings_users_pk = self.storageOfBeings.getUserPkByBlockId(block_id=beings_block_id)
                body_of_times_block = BodyOfTimesBlock(users_pk=beings_users_pk, block_id=beings_block_id)
                body_signature = self.user.sign(str(body_of_times_block.getBody()).encode("utf-8"))
                current_election_period = self.getElectionPeriod() - 1
                prev_block_header, prev_block = self.storageOfGalaxy.getBlockAbstractByElectionPeriod(
                    election_period=current_election_period)
                while prev_block_header is None:
                    # 此时表明上一选举时期没有时代区块产生，继续向前寻找
                    logger.info("current_election_period:" + str(current_election_period) + "没有时代区块产生，继续向前寻找")
                    current_election_period -= 1
                    prev_block_header, prev_block = self.storageOfGalaxy.getBlockAbstractByElectionPeriod(
                        election_period=current_election_period)
                logger.debug("上一区块的区块头部哈希和区块哈希")
                logger.debug(prev_block_header)
                logger.debug(prev_block)
                new_block_of_times = NewBlockOfTimes(user_pk=[self.user.getUserPKString()],
                                                     election_period=self.getElectionPeriod(),
                                                     body_signature=[body_signature], body=body_of_times_block,
                                                     pre_block=prev_block,
                                                     prev_block_header=prev_block_header).getBlock()
                # 保存时代区块
                logger.info("保存时代区块,时代区块ID:" + new_block_of_times.getBlockID())
                self.storageOfGalaxy.addBlockOfGalaxy(block_of_galaxy=new_block_of_times)
                # 广播生成时代区块的投票信息和生成的时代区块
                logger.info("广播生成时代区块的投票信息和生成的时代区块")
                serial_block_of_times = SerializationTimes.serialization(new_block_of_times)
                self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfTimes(),
                                     message=[serial_vote_list, serial_block_of_times])
            else:
                # 修改状态
                self.webServerSDK.modifyStatusOfTimesBlockQueue(beings_block_id=beings_block_id, status=4)
                logger.warning("再次验证投票发现投票数量未达到生成时代区块标准")

    # 检测并且生成垃圾区块
    def checkAndGenerateBlockOfGarbage(self):
        logger.info("检测并且生成垃圾区块")
        # 检测是否有投票数量达到要求的垃圾区块
        vote_of_garbage_block = self.voteCount.getVotesOfGarbageBlockGenerate()
        res = self.webServerSDK.getGarbageBlockQueueByVotes(votes=vote_of_garbage_block)
        if res is not None:
            # 再次验证投票
            beings_block_id = res["beings_block_id"]
            serial_vote_list = res["vote_list"]
            vote_message_list = []
            for vote_i in serial_vote_list:
                # 判断是长期票还是短期票
                if "main_user_pk" in vote_i:
                    # 短期票
                    vote_message_list.append(SerializationVoteMessage.deserialization(str(vote_i).encode("utf-8")))
                else:
                    # 长期票
                    vote_message_list.append(
                        SerializationLongTermVoteMessage.deserialization(str(vote_i).encode("utf-8")))
            if self.voteCount.checkVotesOfGenerateGarbageBlock(beings_block_id=beings_block_id,
                                                               vote_message_list=vote_message_list):
                logger.info("生在生成垃圾区块,原众生区块ID为:" + beings_block_id)
                # 修改状态
                self.webServerSDK.modifyStatusOfGarbageBlockQueue(beings_block_id=beings_block_id, status=2)
                beings_users_pk = self.storageOfBeings.getUserPkByBlockId(block_id=beings_block_id)
                body_of_garbage_block = BodyOfGarbageBlock(users_pk=beings_users_pk, block_id=beings_block_id)
                body_signature = self.user.sign(str(body_of_garbage_block.getBody()).encode("utf-8"))
                current_election_period = self.getElectionPeriod() - 1
                prev_block_header, prev_block = self.storageOfGarbage.getBlockAbstractByElectionPeriod(
                    election_period=current_election_period)
                while prev_block_header is None:
                    # 此时表明上一选举时期没有垃圾区块产生，继续向前寻找
                    logger.info("current_election_period:" + str(current_election_period) + "没有垃圾区块产生，继续向前寻找")
                    current_election_period -= 1
                    prev_block_header, prev_block = self.storageOfGarbage.getBlockAbstractByElectionPeriod(
                        election_period=current_election_period)
                logger.debug("上一区块的区块头部哈希和区块哈希")
                logger.debug(prev_block_header)
                logger.debug(prev_block)
                new_block_of_garbage = NewBlockOfGarbage(user_pk=[self.user.getUserPKString()],
                                                         election_period=self.getElectionPeriod(),
                                                         body_signature=[body_signature], body=body_of_garbage_block,
                                                         pre_block=prev_block,
                                                         prev_block_header=prev_block_header).getBlock()
                # 保存时代区块
                logger.info("保存垃圾区块,垃圾区块ID:" + new_block_of_garbage.getBlockID())
                self.storageOfGarbage.addBlockOfGarbage(block_of_garbage=new_block_of_garbage)
                # 广播生成时代区块的投票信息和生成的时代区块
                logger.info("广播生成时代区块的投票信息和生成的垃圾区块")
                serial_block_of_garbage = SerializationGarbage.serialization(new_block_of_garbage)
                self.pub.sendMessage(topic=SubscribeTopics.getBlockTopicOfGarbage(),
                                     message=[serial_vote_list, serial_block_of_garbage])
            else:
                # 修改状态
                self.webServerSDK.modifyStatusOfGarbageBlockQueue(beings_block_id=beings_block_id, status=4)
                logger.warning("再次验证投票发现投票数量未达到生成垃圾区块标准")
