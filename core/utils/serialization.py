import logging
from ast import literal_eval
import base64

from core.data.block_of_beings import BlockOfBeings, BlockListOfBeings
from core.data.block_of_garbage import BlockOfGarbage
from core.data.block_of_times import BlockOfTimes
from core.consensus.block_generate import NewBlockOfBeingsByExist, NewBlockOfTimesByExist, NewBlockOfGarbageByExist
from core.consensus.data import ApplicationForm, ReplyApplicationForm, VoteMessage, LongTermVoteMessage
from core.data.network_message import NetworkMessage
from core.data.node_info import NodeInfo

logger = logging.getLogger("main")


# 众生区块对象序列化与反序列化
class SerializationBeings:
    # 序列化
    @staticmethod
    def serialization(block_of_beings: BlockOfBeings):
        block_header = block_of_beings.getBlockHeader()
        body = block_of_beings.body
        data = {
            "header": block_header,
            "body": body
        }
        return data

    # 反序列化
    @staticmethod
    def deserialization(data_of_beings: bytes) -> BlockOfBeings:
        dict_of_beings = literal_eval(bytes(data_of_beings).decode("utf-8"))
        header = dict_of_beings["header"]
        body = dict_of_beings["body"]
        block_of_beings = NewBlockOfBeingsByExist(header=header, body=body).getBlock()
        return block_of_beings


# 时代区块对象序列化与反序列化
class SerializationTimes:
    # 序列化
    @staticmethod
    def serialization(block_of_times: BlockOfTimes):
        block_header = block_of_times.getBlockHeader()
        body = block_of_times.body
        return {
            "header": block_header,
            "body": body
        }

    # 反序列化
    @staticmethod
    def deserialization(block_of_times_bytes: bytes) -> BlockOfTimes:
        dict_of_times = literal_eval(bytes(block_of_times_bytes).decode("utf-8"))
        block_of_times = NewBlockOfTimesByExist(header=dict_of_times["header"], body=dict_of_times["body"]).getBlock()
        return block_of_times


# 垃圾区块对象序列化与反序列化
class SerializationGarbage:
    # 序列化
    @staticmethod
    def serialization(block_of_garbage: BlockOfGarbage):
        block_header = block_of_garbage.getBlockHeader()
        body = block_of_garbage.body
        return {
            "header": block_header,
            "body": body
        }

    # 反序列化
    @staticmethod
    def deserialization(block_of_garbage_bytes: bytes) -> BlockOfGarbage:
        dict_of_garbage = literal_eval(bytes(block_of_garbage_bytes).decode("utf-8"))
        block_of_garbage = NewBlockOfGarbageByExist(header=dict_of_garbage["header"],
                                                    body=dict_of_garbage["body"]).getBlock()
        return block_of_garbage


# 申请书对象序列化与反序列化
class SerializationApplicationForm:
    # 序列化
    @staticmethod
    def serialization(application_form: ApplicationForm):
        data = {
            "new_node_info": application_form.newNodeInfo,
            "new_node_signature": application_form.newNodeSignature,
            "application": application_form.application,
            "application_signature_by_new_node": application_form.applicationSignatureByNewNode,
            "main_node": application_form.mainNode
        }
        return data

    # 反序列化
    @staticmethod
    def deserialization(application_form_byte: bytes) -> ApplicationForm:
        application_form_dict = literal_eval(bytes(application_form_byte).decode("utf-8"))
        new_node_info = application_form_dict["new_node_info"]
        content = application_form_dict["application"]["content"]
        start_time = application_form_dict["application"]["start_time"]
        application_signature_by_new_node = application_form_dict["application_signature_by_new_node"]
        application_signature_by_main_node = application_form_dict["main_node"]["application_signature"]
        main_node_user_pk = application_form_dict["main_node"]["user_pk"]
        node_info = NodeInfo(node_id=new_node_info["node_id"], node_ip=new_node_info["node_ip"],
                             user_pk=new_node_info["user_pk"], create_time=new_node_info["create_time"],
                             server_url=new_node_info["server_url"])
        node_info.setNodeSignature(application_form_dict["new_node_signature"])
        application_form = ApplicationForm(node_info=node_info, start_time=start_time, content=content,
                                           application_signature_by_new_node=application_signature_by_new_node)
        application_form.setMainNodeSignature(application_signature_by_main_node)
        application_form.setMainNodeUserPk(main_node_user_pk)
        return application_form


# 申请书回复序列化与反序列化
class SerializationReplyApplicationForm:
    # 序列化
    @staticmethod
    def serialization(reply_application_form: ReplyApplicationForm):
        info = reply_application_form.getInfo()
        signature = reply_application_form.signature
        user_pk = reply_application_form.userPk
        data = {
            "info": info,
            "signature": signature,
            "user_pk": user_pk
        }
        return data

    # 反序列化
    @staticmethod
    def deserialization(reply_application_form_byte: bytes) -> ReplyApplicationForm:
        reply_application_form_dict = literal_eval(bytes(reply_application_form_byte).decode("utf-8"))
        info = reply_application_form_dict["info"]
        signature = reply_application_form_dict["signature"]
        user_pk = reply_application_form_dict["user_pk"]
        reply_application_form = ReplyApplicationForm(new_node_id=info["new_node_id"],
                                                      new_node_user_pk=info["new_node_user_pk"],
                                                      start_time=info["new_node_create_time"],
                                                      is_agree=info["is_agree"])
        reply_application_form.setSignature(signature)
        reply_application_form.setUserPk(user_pk)
        return reply_application_form


class SerializationNetworkMessage:
    # 序列化
    @staticmethod
    def serialization(network_message: NetworkMessage):
        data = {
            "message_type": network_message.messType,
            "message": network_message.message,
            "client_info": network_message.clientInfo,
            "client_signature": network_message.signature
        }
        return data

    # 反序列化
    @staticmethod
    def deserialization(network_message_byte) -> NetworkMessage:
        network_message_dict = literal_eval(bytes(network_message_byte).decode("utf-8"))
        network_message = NetworkMessage(mess_type=network_message_dict["message_type"],
                                         message=network_message_dict["message"])
        client_info = network_message_dict["client_info"]
        network_message.setClientInfo(user_pk=client_info["user_pk"], send_time=client_info["send_time"])
        network_message.setSignature(network_message_dict["client_signature"])
        return network_message


# 序列化区块列表
class SerializationAssetOfBeings:
    @staticmethod
    def serialization(blockListOfBeings: BlockListOfBeings):
        if len(blockListOfBeings.list) == 0:
            return b"{}"
        epoch = blockListOfBeings.list[0].getEpoch()
        block_list = []
        for block_of_beings in blockListOfBeings.list:
            header = block_of_beings.getBlockHeader()
            body = block_of_beings.body
            block_id = block_of_beings.getBlockID()
            block_list.append({
                "block_id": block_id,
                "header": header,
                "body": body
            })
        data = str({
            "epoch": epoch,
            "block_list": block_list
        }).encode("utf-8")
        return base64.b64encode(data)

    @staticmethod
    def deserialization(block_list_bytes: bytes) -> BlockListOfBeings:
        block_list_dict = literal_eval(bytes(base64.b64decode(block_list_bytes)).decode("utf-8"))
        block_list = block_list_dict["block_list"]
        block_list_of_beings = BlockListOfBeings()
        for block_dict in block_list:
            header = block_dict["header"]
            body = block_dict["body"]
            block_list_of_beings.addBlock(NewBlockOfBeingsByExist(header, body).getBlock())
        return block_list_of_beings


# 序列化短期投票消息
class SerializationVoteMessage:
    @staticmethod
    def serialization(vote_message: VoteMessage):
        data = {
            "to_main_node_user_pk": vote_message.toMainNodeUserPk,
            "block_id": vote_message.blockId,
            "election_period": vote_message.electionPeriod,
            "number_of_vote": vote_message.numberOfVote,
            "main_user_pk": vote_message.mainUserPk,
            "vote_type": vote_message.voteType,
            "signature": vote_message.signature
        }
        return data

    @staticmethod
    def deserialization(vote_message_bytes: bytes) -> VoteMessage:
        vote_message_dict = literal_eval(bytes(vote_message_bytes).decode("utf-8"))
        vote_message = VoteMessage()
        vote_message.setVoteInfo(to_main_node_user_pk=vote_message_dict["to_main_node_user_pk"],
                                 block_id=vote_message_dict["block_id"],
                                 election_period=vote_message_dict["election_period"],
                                 number_of_vote=vote_message_dict["number_of_vote"],
                                 main_user_pk=vote_message_dict["main_user_pk"],
                                 vote_type=vote_message_dict["vote_type"])
        vote_message.setSignature(vote_message_dict["signature"])
        return vote_message


# 序列化长期投票消息
class SerializationLongTermVoteMessage:
    @staticmethod
    def serialization(long_term_vote_message: LongTermVoteMessage):
        data = {
            "to_main_node_user_pk": long_term_vote_message.toMainNodeUserPk,
            "block_id": long_term_vote_message.blockId,
            "election_period": long_term_vote_message.electionPeriod,
            "number_of_vote": long_term_vote_message.numberOfVote,
            "simple_user_pk": long_term_vote_message.simpleUserPk,
            "vote_type": long_term_vote_message.voteType,
            "signature": long_term_vote_message.signature
        }
        return data

    @staticmethod
    def deserialization(long_term_vote_message_bytes: bytes) -> LongTermVoteMessage:
        vote_message_dict = literal_eval(bytes(long_term_vote_message_bytes).decode("utf-8"))
        long_term_vote_message = LongTermVoteMessage()
        long_term_vote_message.setVoteInfo(to_main_node_user_pk=vote_message_dict["to_main_node_user_pk"],
                                           block_id=vote_message_dict["block_id"],
                                           election_period=vote_message_dict["election_period"],
                                           number_of_vote=vote_message_dict["number_of_vote"],
                                           simple_user_pk=vote_message_dict["simple_user_pk"],
                                           vote_type=vote_message_dict["vote_type"])
        long_term_vote_message.setSignature(vote_message_dict["signature"])
        return long_term_vote_message
