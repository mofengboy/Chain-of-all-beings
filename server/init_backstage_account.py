import hashlib
import random
import os
import sys
import string

sys.path.append("../")
sys.path.append(os.path.abspath("."))
from server.database import DB


class BackstageAccount:
    def __init__(self):
        self.db = DB()

    @staticmethod
    def genPassword(length):
        chars = string.ascii_letters + string.digits
        return ''.join([random.choice(chars) for i in range(length)])

    def generateUser(self):
        password = self.genPassword(16)
        password_abstract = hashlib.sha256(str(password).encode("utf-8")).hexdigest()
        if self.db.isUserExist("node_admin"):
            print("已经覆盖原密码")
            self.db.updateUser(username="node_admin", password=password_abstract)
        else:
            self.db.addUser(username="node_admin", password=password_abstract)
        return ["node_admin", password]


if __name__ == "__main__":
    un, pd = BackstageAccount().generateUser()
    print("后台密码已生成")
    print("username:" + un)
    print("password:" + pd)
    print("请牢记以上密码")
