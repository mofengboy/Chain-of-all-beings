import sqlite3


# web server数据库
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
            create_time TEXT NOT NULL
            )
            """)
            self.__DB.commit()

    def getWaitingBlockListOfBeingsToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select id,user_pk,body,signature,is_review,review_username,create_time 
        from beings_block where is_review = 1 limit 10
        """)
        data_list = cursor.fetchall()
        id_list = []
        for data in data_list:
            id_list.append({
                "db_id": data[0],
                "user_pk": data[1],
                "body": bytes(data[2]).decode("utf-8"),
                "signature": data[3],
                "is_review": data[4],
                "review_username": data[5],
                "create_time": data[6]
            })
            cursor.execute("""
            update beings_block set is_review = 3
            where id = ?
            """, (data[0],))

        self.__DB.commit()
        return id_list

    def getWaitingBlockCountOfBeingsToSDK(self):
        cursor = self.__DB.cursor()
        cursor.execute("""
        select count(id)
        from beings_block where is_review = 1
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
