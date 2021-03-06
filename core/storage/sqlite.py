import sqlite3
from abc import ABC

from core.utils.system_time import STime


class Sqlite(ABC):
    def __init__(self):
        self.blockConn = sqlite3.connect('./db/block.db', check_same_thread=False)
        self.initBlockDB()

        self.tempConn = sqlite3.connect('./db/temp.db', check_same_thread=False)
        self.initTempDB()

    def initBlockDB(self):
        cursor = self.blockConn.cursor()
        # 众生链
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'beings'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table beings(
            id INTEGER PRIMARY KEY,
            epoch INTEGER NOT NULL,
            block_id TEXT NOT NULL UNIQUE,
            main_node_user_pk TEXT NOT NULL,
            simple_user_pk TEXT NOT NULL,
            header BLOB NOT NULL,
            body BLOB NOT NULL
            )
            """)
            self.blockConn.commit()

        # 时代链
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'galaxy'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table galaxy(
            id INTEGER PRIMARY KEY,
            election_period INTEGER NOT NULL,
            block_id TEXT NOT NULL UNIQUE,
            user_pk TEXT NOT NULL,
            header BLOB NOT NULL,
            body BLOB NOT NULL,
            beings_block_id TEXT NOT NULL,
            beings_simple_user_pk TEXT NOT NULL,
            beings_main_node_user_pk TEXT NOT NULL
            )
            """)
            self.blockConn.commit()

        # 垃圾标注链
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'garbage'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table garbage(
            id INTEGER PRIMARY KEY,
            election_period INTEGER NOT NULL,
            block_id TEXT NOT NULL UNIQUE,
            user_pk TEXT NOT NULL,
            header BLOB NOT NULL,
            body BLOB NOT NULL,
            beings_block_id TEXT NOT NULL,
            beings_simple_user_pk TEXT NOT NULL,
            beings_main_node_user_pk TEXT NOT NULL
            )
            """)
            self.blockConn.commit()

    def initTempDB(self):
        cursor = self.tempConn.cursor()
        # 存储待发布的区块内容
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'block'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table block(
            id INTEGER PRIMARY KEY,
            user_pk TEXT NOT NULL,
            body_signature TEXT NOT NULL,
            body TEXT NOT NULL,
            is_release INTEGER NOT NULL, 
            create_time INTEGER NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 新主节点申请信息（当前主节点已经审核通过）
        # is_audit 0代表未审核 1代表审核通过 2代表拒绝 3表示以及申请完成，4超过规定时间未达到要求
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'node_join'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table node_join(
            id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,
            user_pk TEXT NOT NULL,
            node_ip  TEXT NOT NULL,
            server_url TEXT NOT NULL,
            node_create_time TEXT NOT NULL,
            node_signature TEXT NOT NULL,
            application TEXT NOT NULL,
            application_time TEXT NOT NULL,
            application_signature TEXT NOT NULL,
            agree_count INTEGER NOT NULL,
            is_audit INTEGER NOT NULL,
            main_node_signature TEXT NOT NULL,
            main_node_user_pk TEXT NOT NULL,
            create_time INTEGER NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储接受到的新节点加入同意信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'node_join_agree'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table node_join_agree(
            id INTEGER PRIMARY KEY,
            new_node_id TEXT NOT NULL,
            start_time INTEGER NOT NULL,
            reply_application_form_info BLOB NOT NULL,
            main_node_user_pk TEXT NOT NULL,
            main_node_signature TEXT NOT NULL,
            create_time INTEGER NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储待审核的新节点加入信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'node_join_other'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table node_join_other(
            id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,
            user_pk TEXT NOT NULL,
            node_ip  TEXT NOT NULL,
            server_url TEXT NOT NULL,
            node_create_time TEXT NOT NULL,
            node_signature TEXT NOT NULL,
            application TEXT NOT NULL,
            application_time TEXT NOT NULL,
            application_signature TEXT NOT NULL,
            main_node_user_pk TEXT NOT NULL,
            main_node_signature TEXT NOT NULL,
            is_audit INTEGER NOT NULL,
            create_time INTEGER NOT NULL
            )
            """)
            self.tempConn.commit()

        # 主节点主动申请删除信息（当前主节点申请）
        # is_audit 0代表待广播 1代表已经广播 3表示以及申请完成，4超过规定时间未达到要求
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'node_active_delete'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table node_active_delete(
            id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,
            application_content TEXT NOT NULL,
            application_time TEXT NOT NULL,
            agree_count INTEGER NOT NULL,
            is_audit INTEGER NOT NULL,
            main_node_signature TEXT NOT NULL,
            main_node_user_pk TEXT NOT NULL,
            create_time INTEGER NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储接受到的回复同意消息（主动申请删除的）
        # status 0 表示待广播 1表示广播 2 表示取消广播
        cursor.execute("""select count(*) from sqlite_master 
        where type = 'table' and name = 'node_active_delete_reply_agree'""")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table node_active_delete_reply_agree(
            id INTEGER PRIMARY KEY,
            del_node_id TEXT NOT NULL,
            start_time INTEGER NOT NULL,
            reply_application_form BLOB NOT NULL,
            reply_node_user_pk TEXT NOT NULL,
            reply_node_signature TEXT NOT NULL,
            status INTEGER NOT NULL,
            create_time INTEGER NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储待审核的主节点删除信息（其他主节点发送的）
        # is_audit 0代表待回复 1代表已经回复同意 2代表已回复拒绝 3代表已经广播同意 4代表已经广播拒绝
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'node_delete_other_active'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table node_delete_other_active(
            id INTEGER PRIMARY KEY,
            node_id TEXT NOT NULL,
            application_content TEXT NOT NULL,
            application_time TEXT NOT NULL,
            is_audit INTEGER NOT NULL,
            main_node_signature TEXT NOT NULL,
            main_node_user_pk TEXT NOT NULL,
            create_time INTEGER NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储待审核的节点删除信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'node_delete'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table node_delete(
            id INTEGER PRIMARY KEY,
            node_info BLOB NOT NULL,
            node_signature TEXT NOT NULL,
            application BLOB NOT NULL,
            is_audit INTEGER NOT NULL,
            create_time INTEGER NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储待广播的短期投票信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'wait_votes'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table wait_votes(
            id INTEGER PRIMARY KEY,
            to_node_id TEXT NOT NULL,
            election_period INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            user_pk TEXT NOT NULL,
            vote_info BLOB NOT NULL,
            signature TEXT NOT NULL,
            status INTEGER NOT NULL,
            create_time TEXT NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储待广播的长期投票信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'wait_votes_of_long'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table wait_votes_of_long(
            id INTEGER PRIMARY KEY,
            to_node_id TEXT NOT NULL,
            election_period INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            user_pk TEXT NOT NULL,
            vote_info BLOB NOT NULL,
            signature TEXT NOT NULL,
            status INTEGER NOT NULL,
            create_time TEXT NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储收集到的投票信息摘要 防止重复广播
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'vote_digest'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table vote_digest(
            id INTEGER PRIMARY KEY,
            election_period INTEGER NOT NULL,
            block_id TEXT NOT NULL,
            vote_message_digest TEXT NOT NULL,
            create_time TEXT NOT NULL 
            )
            """)
            self.tempConn.commit()

        # 存储core的一些信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'core_info'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table core_info(
            id INTEGER PRIMARY KEY,
            info_id INTEGER NOT NULL,
            info_name TEXT NOT NULL,
            content BLOB NOT NULL,
            update_time INTEGER NOT NULL, 
            create_time INTEGER NOT NULL
            ) 
            """)
            self.tempConn.commit()

        # 存储当前Epoch消息
        cursor.execute("""
        select count(*) from core_info
        where info_name = ?
        """, ("current_epoch",))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            insert into core_info(info_id,info_name,content,update_time,create_time)
            values (?,?,?,?,?)
            """, (1, "current_epoch", 0, STime.getTimestamp(), STime.getTimestamp()))
            self.tempConn.commit()

        # 主节点的票数信息
        cursor.execute("select count(*) from sqlite_master where type = 'table' and name = 'main_node_vote'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table main_node_vote(
            id INTEGER PRIMARY KEY,
            main_node_id TEXT NOT NULL,
            main_node_user_pk TEXT NOT NULL,
            total_vote float NOT NULL,
            used_vote float NOT NULL,
            update_time INTEGER NOT NULL, 
            create_time INTEGER NOT NULL
            ) 
            """)
            self.tempConn.commit()

        # 普通用户的票数信息
        cursor.execute(
            "select count(*) from sqlite_master where type = 'table' and name = 'simple_user_permanent_vote'")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            create table simple_user_permanent_vote(
            id INTEGER PRIMARY KEY,
            simple_user_pk TEXT NOT NULL,
            total_vote float NOT NULL,
            used_vote float NOT NULL,
            update_time INTEGER NOT NULL, 
            create_time INTEGER NOT NULL
            ) 
            """)
            self.tempConn.commit()


if __name__ == "__main__":
    Sqlite()
