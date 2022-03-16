import hashlib
from ast import literal_eval

from core.data.block_of_beings import BlockOfBeings
from core.consensus.block_generate import NewBlockOfBeingsByExist
from core.consensus.data import ApplicationForm, ReplyApplicationForm

# 众生区块对象序列化与反序列化
from core.data.network_message import NetworkMessage


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
        application_form = ApplicationForm(node_info=new_node_info, start_time=start_time, content=content,
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
