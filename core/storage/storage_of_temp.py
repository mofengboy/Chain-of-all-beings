from ast import literal_eval

from core.config.cycle_Info import ElectionPeriodValue
from core.data.vote_info import WaitVote
from core.storage.sqlite import Sqlite
from core.utils.system_time import STime
from core.consensus.data import ApplicationForm, ReplyApplicationForm
from core.data.node_info import NodeInfo


class StorageOfTemp(Sqlite):
    def __init__(self):
        super().__init__()

    def saveData(self, user_pk, body_signature, body):
        create_time = STime.getTimestamp()
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into block(user_pk, body_signature, body, is_release, create_time) 
        values (?,?,?,0,?)
        """, (user_pk, body_signature, str(body).encode("utf-8"), create_time))
        self.tempConn.commit()

    def saveBatchData(self, beings_list):
        create_time = STime.getTimestamp()
        cursor = self.tempConn.cursor()
        data_list = []
        for beings in beings_list:
            data_list.append(
                (beings["user_pk"], beings["body_signature"], beings["body"], 0, create_time)
            )
        cursor.executemany("""
        insert into block(user_pk, body_signature, body, is_release, create_time) 
        values (?,?,?,?,?)
        """, data_list)
        self.tempConn.commit()

    def getTopData(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id,user_pk,body_signature,body from block 
        where is_release = 0 limit 1
        """)
        res = cursor.fetchone()
        current_id = res[0]
        data = {
            "user_pk": res[1],
            "body_signature": res[2],
            "body": res[3]
        }
        cursor.execute("""
        update block set is_release = 1 where id = ?
        """, (current_id,))
        self.tempConn.commit()
        return data

    # 查询待发布的数据数量
    def getDataCount(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(*) from block where is_release = 0
        """)
        res = cursor.fetchone()
        data_count = res[0]
        return data_count

    # 将从其他主节点接受到的新节点申请表加入数据库
    def insertApplicationFormByOtherMainNode(self, application_form: ApplicationForm):
        node_id = application_form.newNodeId
        user_pk = application_form.newNodeInfo["user_pk"]
        node_ip = application_form.newNodeInfo["node_ip"]
        server_url = application_form.newNodeInfo["server_url"]
        node_create_time = application_form.newNodeInfo["create_time"]
        node_signature = application_form.newNodeSignature
        application = application_form.application["content"]
        application_time = application_form.application["start_time"]
        application_signature = application_form.applicationSignatureByNewNode
        main_node_user_pk = application_form.mainNode["user_pk"]
        main_node_signature = application_form.mainNode["application_signature"]

        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into node_join_other(node_id, user_pk, node_ip,server_url, node_create_time, node_signature, 
        application, application_time, application_signature, main_node_user_pk, 
        main_node_signature, is_audit, create_time)
        values (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (node_id, user_pk, node_ip, server_url, node_create_time, node_signature,
              application, application_time, application_signature, main_node_user_pk, main_node_signature,
              0, STime.getTimestamp()))
        self.tempConn.commit()

    # 检测该节点申请表是否存在
    def isApplicationForm(self, new_node_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(*) from node_join_other
        where user_pk = ?
        """, (new_node_user_pk,))
        res = cursor.fetchone()
        if res[0] > 0:
            return True
        else:
            return False

    # 获取已经完成审核的申请表（同意或拒绝）
    def getListOfFinishAuditApplicationForm(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id,node_id, user_pk, node_create_time, is_audit,main_node_user_pk
        from node_join_other where is_audit = 1 or is_audit = 2 limit 2
        """)
        res = cursor.fetchall()
        application_form_list = []
        for data in res:
            application_form_list.append({
                "node_id": data[1],
                "user_pk": data[2],
                "node_create_time": int(data[3]),
                "is_audit": data[4],
                "main_node_user_pk": data[5]
            })
            cursor.execute("""
            update node_join_other set is_audit = 3
            where id = ?
            """, (data[0],))
        self.tempConn.commit()
        return application_form_list

    # 查询接受到的待审核的新节点数量
    def getCountOfNodeApply(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(*) from node_join_other where is_audit = 0
        """)
        res = cursor.fetchone()
        data_count = res[0]
        return data_count

    # 将新节点申请表加入数据库,准备接受其他主节点的意见
    # is_audit = 0表示正在申请阶段，=1表示申请通过，=2表示申请失败或者已经过期
    def insertApplicationForm(self, node_id, user_pk, node_ip, server_url, node_create_time, node_signature,
                              application, application_time, application_signature, agree_count, main_node_signature,
                              main_node_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into node_join(node_id, user_pk, node_ip, server_url,node_create_time, node_signature, 
        application, application_time, application_signature, agree_count, 
        is_audit ,main_node_signature,main_node_user_pk,create_time)
        values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (node_id, user_pk, node_ip, server_url, node_create_time, node_signature,
              application, application_time, application_signature, agree_count, 0, main_node_signature,
              main_node_user_pk, STime.getTimestamp()))
        self.tempConn.commit()

    # 增加对该节点的同意数量
    def addAgreeCount(self, new_node_id, count):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select agree_count from node_join
        where  node_id = ? and is_audit = 0
        """, (new_node_id,))
        res = cursor.fetchone()
        total_count = res[0] + count
        cursor.execute("""
        update node_join set agree_count = ?
        where node_id = ? and is_audit = 0
        """, (total_count, new_node_id))
        self.tempConn.commit()

    # 设置该节点的同意数量
    def setAgreeCount(self, new_node_id, count):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join set agree_count = ?
        where node_id = ? and is_audit = 0
        """, (count, new_node_id))
        self.tempConn.commit()

    # 获取正在申请阶段申请表ID
    def getNodeIdListOfWaitingAuditApplicationForm(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select node_id from node_join
        where is_audit = 0
        """)
        node_id_list = []
        res = cursor.fetchall()
        for data in res:
            node_id_list.append(data[0])
        return node_id_list

    # 获取申请表
    def getApplicationFormByNodeId(self, new_node_id) -> ApplicationForm:
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select node_id, user_pk, node_ip, server_url, node_create_time, node_signature, application, 
        application_time, application_signature,main_node_signature,main_node_user_pk, create_time 
        from node_join
        where node_id = ?
        """, (new_node_id,))
        res = cursor.fetchone()
        node_info = NodeInfo(node_id=res[0], user_pk=res[1], node_ip=res[2], server_url=res[3], create_time=res[4])
        node_info.setNodeSignature(res[5])
        application_form = ApplicationForm(node_info=node_info, start_time=int(res[7]), content=res[6],
                                           application_signature_by_new_node=res[8])
        application_form.setMainNodeUserPk(res[10])
        application_form.setMainNodeSignature(res[9])
        return application_form

    # 删除申请书，将is_audit置为2
    def delApplicationFormByNodeId(self, new_node_id):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join set is_audit = 2
        where node_id = ? and is_audit = 0
        """, (new_node_id,))
        self.tempConn.commit()

    # 申请完成，将is_audit置为1
    def finishApplicationFormByNodeId(self, new_node_id):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join set is_audit = 1
        where node_id = ? and is_audit = 0
        """, (new_node_id,))
        self.tempConn.commit()

    # 获取申请书的同意数量
    def getAgreeCountByNodeId(self, new_node_id):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select agree_count from node_join
        where node_id = ?
        """, (new_node_id,))
        res = cursor.fetchone()
        return res[0]

    # 插入其他节点的同意消息
    def insertApplicationFormReply(self, reply_application_form: ReplyApplicationForm):
        new_node_id = reply_application_form.newNodeId
        start_time = reply_application_form.startTime
        reply_application_form_info = str(reply_application_form.getInfo()).encode("utf-8")
        main_node_user_pk = reply_application_form.userPk
        main_node_signature = reply_application_form.signature
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into node_join_agree(new_node_id,start_time, reply_application_form_info, 
        main_node_user_pk, main_node_signature, create_time) 
        values (?,?,?,?,?,?)
        """, (new_node_id, start_time, reply_application_form_info, main_node_user_pk, main_node_signature,
              STime.getTimestamp()))
        self.tempConn.commit()

    # 查询该回复消息是否存在
    def isApplicationFormReply(self, new_node_id, start_time, main_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(id) from node_join_agree
        where new_node_id = ? and start_time = ? and main_node_user_pk = ?
        """, (new_node_id, start_time, main_user_pk))
        res = cursor.fetchone()
        if res[0] > 0:
            return True
        else:
            return False

    # 获取与节点ID和节点申请开始时间同时匹配的申请书回复表
    def getListOfReplyApplicationFormInfo(self, new_node_id, start_time):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select reply_application_form_info, main_node_signature, main_node_user_pk 
        from node_join_agree
        where new_node_id = ? and start_time = ?
        """, (new_node_id, start_time))
        res = cursor.fetchall()
        reply_application_form_list = []
        for data in res:
            reply_application_form_info = literal_eval(bytes(data[0]).decode("utf-8"))
            reply_application_form = ReplyApplicationForm(new_node_id=reply_application_form_info["new_node_id"],
                                                          new_node_user_pk=reply_application_form_info[
                                                              "new_node_user_pk"],
                                                          start_time=reply_application_form_info[
                                                              "new_node_create_time"],
                                                          is_agree=reply_application_form_info["is_agree"])
            reply_application_form.setSignature(data[1])
            reply_application_form.setUserPk(data[2])
            reply_application_form_list.append(reply_application_form)
        return reply_application_form_list

    # 审核新节点请求
    def auditNodeOfApplication(self, db_id, is_audit, application, start_time=None, main_node_signature=None,
                               main_node_user_pk=None):
        application["start_time"] = start_time
        application["main_node_signature"] = main_node_signature
        application["main_node_user_pk"] = main_node_user_pk
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join 
        set is_audit= ?, application = ? 
        where id = ?  
        """, (is_audit, application, db_id))
        self.tempConn.commit()

    # 修改新节点的申请状态
    def modifyStateOfNewNode(self, db_id, is_audit):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update node_join 
        set is_audit= ?
        where id = ?  
        """, (is_audit, db_id))
        self.tempConn.commit()

    def getSimpleUserVoteByUserPk(self, user_pk, election_period):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select total_vote,used_vote from simple_user_vote 
        where user_pk = ? and election_period= ?
        """, (user_pk, election_period))
        res = cursor.fetchone()
        if res is None:
            return 0.0
        else:
            return res[0] - res[1]

    def setEpoch(self, current_epoch):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update core_info
        set content = ?, update_time = ?
        where info_name = ?
        """, (current_epoch, STime.getTimestamp(), "current_epoch"))
        self.tempConn.commit()

    def getEpoch(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select content from core_info
        where info_name = ?
        """, ("current_epoch",))
        res = cursor.fetchone()
        if res is None:
            return 0
        else:
            return int(res[0])

    def getElectionPeriod(self):
        current_epoch = self.getEpoch()
        if current_epoch is None:
            return None
        return int(current_epoch / ElectionPeriodValue)

    def setNodeInfo(self, node_info: NodeInfo):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(id) from core_info
        where info_name = ?
        """, ("node_info",))
        res = cursor.fetchone()
        if res[0] == 0:
            create_time = STime.getTimestamp()
            cursor.execute("""
            insert into core_info(info_id, info_name, content, update_time, create_time)
            values (?,?,?,?,?)
            """, (2, "node_info", str(node_info.getMessage()).encode("utf-8"), create_time, create_time))
            self.tempConn.commit()
        else:
            cursor.execute("""
            update core_info
            set content = ?, update_time = ?
            where info_name = ?
            """, (str(node_info.getMessage()).encode("utf-8"), STime.getTimestamp(), "node_info"))
            self.tempConn.commit()

    def getNodeInfo(self) -> NodeInfo:
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select content from core_info
        where info_name = ?
        """, ("node_info",))
        res = cursor.fetchone()
        node_info_dict = literal_eval(bytes(res[0]).decode("utf-8"))
        node_info = NodeInfo(node_id=node_info_dict["node_id"], user_pk=node_info_dict["user_pk"],
                             node_ip=node_info_dict["node_ip"], server_url=node_info_dict["server_url"],
                             create_time=node_info_dict["create_time"])
        node_info.setNodeSignature(node_info_dict["signature"])
        return node_info

    def addMainNodeVote(self, main_node_id, main_node_user_pk, total_vote):
        create_time = STime.getTimestamp()
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into main_node_vote(main_node_id, main_node_user_pk, total_vote, used_vote, update_time, create_time)
        values (?,?,?,?,?,?)
        """, (main_node_id, main_node_user_pk, total_vote, 0, create_time, create_time))
        self.tempConn.commit()

    def getMainNodeVoteByMainNodeUserPk(self, main_node_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id, main_node_id, main_node_user_pk, total_vote, used_vote, update_time, create_time
        from main_node_vote
        where main_node_user_pk = ?
        """, (main_node_user_pk,))
        res = cursor.fetchone()
        if res is not None:
            return {
                "id": res[0],
                "main_node_id": res[1],
                "main_node_user_pk": res[2],
                "total_vote": res[3],
                "used_vote": res[4],
                "update_time": res[5],
                "create_time": res[6],
            }
        else:
            return None

    def addUsedVoteByNodeUserPk(self, vote: float, main_node_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select used_vote from main_node_vote
        where main_node_user_pk = ?
        """, (main_node_user_pk,))
        res = cursor.fetchone()
        if res is not None:
            total_used_vote = float(res[0]) + vote
            cursor.execute("""
            update main_node_vote
            set used_vote = ?,update_time = ?
            where main_node_user_pk = ?
            """, (total_used_vote, STime.getTimestamp(), main_node_user_pk))
            self.tempConn.commit()

    def getListOfMainNodeVote(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select main_node_id, main_node_user_pk from main_node_vote
        """)
        res = cursor.fetchall()
        data_list = []
        for data in res:
            data_list.append({
                "node_id": data[0],
                "node_user_Pk": data[1]
            })
        return data_list

    def clearAllMainNodeVote(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        delete from main_node_vote
        """)
        self.tempConn.commit()

    def getVoteMessage(self, status: int):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id, to_node_id, election_period, block_id, user_pk, vote_info, signature,status, create_time 
        from wait_votes
        where status = ? limit 10
        """, (status,))
        res = cursor.fetchall()
        wait_vote_list = []
        for data in res:
            vote_info_dict = literal_eval(bytes(data[5]).decode("utf-8"))
            wait_vote = WaitVote()
            wait_vote.setInfo(election_period=vote_info_dict["election_period"],
                              to_node_id=vote_info_dict["to_node_id"], vote_type=vote_info_dict["vote_type"],
                              block_id=vote_info_dict["block_id"], vote=vote_info_dict["vote"],
                              simple_user_pk=vote_info_dict["simple_user_pk"])
            wait_vote.setSignature(data[6])
            wait_vote_list.append(wait_vote)
        return wait_vote_list

    def modifyStatusOfWaitVote(self, status, wait_vote: WaitVote):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update wait_votes
        set status = ?
        where election_period = ? and block_id = ? and user_pk = ? and to_node_id = ? and signature = ?
        """, (status, wait_vote.electionPeriod, wait_vote.blockId, wait_vote.simpleUserPk, wait_vote.toNodeId,
              wait_vote.signature))
        self.tempConn.commit()

    def getLongTermVoteMessage(self, status: int):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id, to_node_id, election_period, block_id, user_pk, vote_info, signature,status, create_time 
        from wait_votes_of_long
        where status = ? limit 10
        """, (status,))
        res = cursor.fetchall()
        wait_vote_list = []
        for data in res:
            vote_info_dict = literal_eval(bytes(data[5]).decode("utf-8"))
            wait_vote = WaitVote()
            wait_vote.setInfo(election_period=vote_info_dict["election_period"],
                              to_node_id=vote_info_dict["to_node_id"], vote_type=vote_info_dict["vote_type"],
                              block_id=vote_info_dict["block_id"], vote=vote_info_dict["vote"],
                              simple_user_pk=vote_info_dict["simple_user_pk"])
            wait_vote.setSignature(data[6])
            wait_vote_list.append(wait_vote)
        return wait_vote_list

    def modifyStatusOfLongTermWaitVote(self, status, wait_vote: WaitVote):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        update wait_votes_of_long
        set status = ?
        where election_period = ? and block_id = ? and user_pk = ? and to_node_id = ? and signature = ?
        """, (status, wait_vote.electionPeriod, wait_vote.blockId, wait_vote.simpleUserPk, wait_vote.toNodeId,
              wait_vote.signature))
        self.tempConn.commit()

    def addVoteDigest(self, election_period, block_id, vote_message_digest):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        insert into vote_digest(election_period, block_id, vote_message_digest, create_time)
        values (?,?,?,?)
        """, (election_period, block_id, vote_message_digest, STime.getTimestamp()))
        self.tempConn.commit()

    def isExitVoteDigest(self, election_period, block_id, vote_message_digest):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select count(id) from vote_digest
        where election_period = ? and block_id = ? and vote_message_digest = ?
        """, (election_period, block_id, vote_message_digest))
        res = cursor.fetchone()
        if res[0] > 0:
            return True
        else:
            return False

    def clearVoteDigest(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        delete from vote_digest
        """)
        self.tempConn.commit()

    def clearAllSimpleUserPermanentVote(self):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        delete from simple_user_permanent_vote
        """)
        self.tempConn.commit()

    def addBatchPermanentVoteOfSimpleUser(self, data_dict: dict):
        data_list = []
        current_time = STime.getTimestamp()
        for key in data_dict.keys():
            data_list.append(
                (
                    key,
                    data_dict[key],
                    0,
                    current_time,
                    current_time
                )
            )
        cursor = self.tempConn.cursor()
        cursor.executemany("""
        insert into simple_user_permanent_vote(simple_user_pk, total_vote, used_vote, update_time, create_time)
        values (?,?,?,?,?)
        """, data_list)
        self.tempConn.commit()

    def addUsedPermanentVoteOfSimpleUser(self, vote: float, simple_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select used_vote from simple_user_permanent_vote
        where simple_user_pk = ?
        """, (simple_user_pk,))
        res = cursor.fetchone()
        if res is not None:
            total_used_vote = float(res[0]) + vote
            cursor.execute("""
            update simple_user_permanent_vote
            set used_vote = ?, update_time = ?
            where simple_user_pk = ?
            """, (total_used_vote, STime.getTimestamp(), simple_user_pk))
            self.tempConn.commit()

    def getSimpleUserPermanentVoteByUserPk(self, simple_user_pk):
        cursor = self.tempConn.cursor()
        cursor.execute("""
        select id, simple_user_pk, total_vote, used_vote, update_time, create_time
        from simple_user_permanent_vote
        where simple_user_pk = ?
        """, (simple_user_pk,))
        res = cursor.fetchone()
        if res is not None:
            return {
                "id": res[0],
                "simple_user_pk": res[1],
                "total_vote": res[2],
                "used_vote": res[3],
                "update_time": res[4],
                "create_time": res[5],
            }
        else:
            return None
