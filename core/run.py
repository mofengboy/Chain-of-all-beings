from core.user.user import User


def console():
    print("众生之链控制终端")
    user = User()

    print("您是否已经拥有私钥？输入y表示已经拥有，n表示现在去生成。")
    flag = input(":")
    while flag != "y" and flag != "n":
        print("请输入y或n")
        flag = input(":")
    if flag == "y":
        print("请确认安全后输入您的私钥")
        key = input(":")
        user.login(key)
        print("登录成功")
    if flag == "n":
        print("私钥已生成")
        user.register()
        key = user.getUserSK()
        print("请确保将以下私钥保存到安全的地方，私钥是您后续操作的唯一凭证，并且丢失后无法找回。")
        print(key)

#     节点鉴权 是否为主节点








if __name__ == "__main__":
    console()
