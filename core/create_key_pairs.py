import os
import sys

sys.path.append("../")
sys.path.append(os.path.abspath("."))
from core.user.user import User


def createKeyPairs():
    user = User()
    user.register()
    print("请务必谨慎保存，一旦丢失或被盗将无法找回！")


if __name__ == "__main__":
    createKeyPairs()
