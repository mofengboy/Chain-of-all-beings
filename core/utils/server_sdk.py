import logging
import os
import sqlite3

# web server数据库
from core.data.block_of_beings import BlockListOfBeings
from core.utils.serialization import SerializationAssetOfBeings

logger = logging.getLogger("main")


class DB:
    def __init__(self):
        self.__DB = sqlite3.connect('../server/db/database.db', check_same_thread=False)
        self.__initDB()

    def __initDB(self):
        cursor = self.__DB.cursor()
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'beings_block'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table beings_block(
            id INTEGER PRIMARY KEY,
            user_pk TEXT NOT NULL,
            body BLOB NOT NULL,
            signature TEXT NOT NULL,
            is_review INTEGER NOT NULL,
            review_username TEXT,
            create_time TEXT NOT NULL
            )
            """)
            self.__DB.commit()

        # 用户为了成为主节点提交的申请书
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'application_form'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table application_form(
            id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,
            user_pk TEXT NOT NULL,
            node_ip  TEXT NOT NULL,
            server_url TEXT NOT NULL,
            node_create_time TEXT NOT NULL,
            node_signature TEXT NOT NULL,
            application TEXT NOT NULL,
            application_signature TEXT NOT NULL,
            is_review INTEGER NOT NULL,
            remarks TEXT NOT NULL,
            create_time TEXT NOT NULL
            )
            """)
            self.__DB.commit()

    def getWaitingBlockListOfBeingsToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,user_pk,body,signature,is_review,create_time 
        from beings_block where is_review = 1 limit 10
        """)
        data_list = cursor.fetchall()
        block_list = []
        for data in data_list:
            block_list.append({
                "db_id": data[0],
                "user_pk": data[1],
                "body": data[2],
                "signature": data[3],
                "is_review": data[4],
                "create_time": data[5]
            })
            cursor.execute("""
            update beings_block set is_review = 3
            where id = ?
            """, (data[0],))

        self.__DB.commit()
        return block_list

    def getWaitingBlockCountOfBeingsToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id)
        from beings_block where is_review = 1
        """)
        data = cursor.fetchone()
        return data[0]

    def getWaitingApplicationFormToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id, node_id, user_pk, node_ip, server_url, node_create_time, node_signature, 
        application, application_signature, is_review, create_time
        from application_form where is_review = 1 limit 2
        """)
        data_list = cursor.fetchall()
        application_form_list = []
        for data in data_list:
            application_form_list.append({
                "db_id": data[0],
                "node_id": data[1],
                "user_pk": data[2],
                "node_ip": data[3],
                "server_url": data[4],
                "node_create_time": data[5],
                "node_signature": data[6],
                "application": data[7],
                "application_signature": data[8],
                "is_review": data[9],
                "create_time": data[10]
            })
            cursor.execute("""
            update application_form set is_review = 3
            where id = ?
            """, (data[0],))
        self.__DB.commit()
        return application_form_list

    def getWaitingApplicationFormCountToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id)
        from application_form where is_review = 1
        """)
        data = cursor.fetchone()
        return data[0]


# core部分读取server部分的数据库
class SDK:
    def __init__(self):
        self.db = DB()

    def getBeings(self):
        data_list = self.db.getWaitingBlockListOfBeingsToSDK()
        beings_list = []
        for data in data_list:
            beings_list.append({
                "user_pk": data["user_pk"],
                "body_signature": data["signature"],
                "body": data["body"]
            })
        return beings_list

    def getBeingsCount(self):
        return self.db.getWaitingBlockCountOfBeingsToSDK()

    def getApplicationForm(self):
        data_list = self.db.getWaitingApplicationFormToSDK()
        application_form_list = []
        for data in data_list:
            application_form_list.append({
                "node_id": data["node_id"],
                "user_pk": data["user_pk"],
                "node_ip": data["node_ip"],
                "server_url": data["server_url"],
                "node_create_time": int(data["node_create_time"]),
                "node_signature": data["node_signature"],
                "application": data["application"],
                "application_signature": data["application_signature"]
            })
        return application_form_list

    def getApplicationFormCount(self):
        return self.db.getWaitingApplicationFormCountToSDK()


# server部分的区块资源
# 提供下载
class ChainAsset:
    def __init__(self):
        self.file_path = "../server/static/"
        os.makedirs(self.file_path, mode=666, exist_ok=True)

    # 通过Epoch检测众生区块是否存在
    def beingsIsExitByEpoch(self, epoch) -> bool:
        file = self.file_path + "beings_" + str(epoch) + ".chain"
        return os.path.exists(file)

    # 保存区块
    def saveBlockOfBeings(self, block_list_of_beings: BlockListOfBeings) -> bool:
        if len(block_list_of_beings.list) == 0:
            return True
        epoch = block_list_of_beings.list[0].getEpoch()
        block_list_of_beings.sortByBlockId()
        file_name = "beings_" + str(epoch) + ".chain"
        if not self.beingsIsExitByEpoch(epoch):
            with open(self.file_path + file_name, "wb+") as fp:
                content = SerializationAssetOfBeings.serialization(block_list_of_beings)
                fp.write(content)
        else:
            return False

    # 批量期次保存区块
    def saveBatchBlockOfBeings(self, block_list_of_beings: BlockListOfBeings) -> bool:
        epoch_block_list_of_beings = {}
        for block in block_list_of_beings.list:
            epoch = block.getEpoch()
            if str(epoch) not in epoch_block_list_of_beings:
                epoch_block_list_of_beings[str(epoch)] = BlockListOfBeings()
                epoch_block_list_of_beings[str(epoch)].addBlock(block)
            else:
                epoch_block_list_of_beings[str(epoch)].addBlock(block)
        is_success = True
        for block_list in epoch_block_list_of_beings.values():
            is_success = self.saveBlockOfBeings(block_list) and is_success
        return is_success
