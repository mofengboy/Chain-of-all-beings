import getopt
import sys
import os
import logging.config
import time
import yaml

sys.path.append("../")
sys.path.append(os.path.abspath("."))

from core.app import APP
from core.utils.ciphersuites import CipherSuites
from core.utils.system_time import STime


def run(sk_string, pk_string, server_url):
    # 日志
    with open('./config/log_config.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    logger = logging.getLogger("main")

    # 校对系统时间，系统时间与NTP服务器时间不得超过1秒
    if not STime.proofreadingTime():
        # 抛出错误
        logger.error("系统时间与NTP服务器时间不得超过1秒,请核对系统时间")
        exit()

    # 初始化核心 core
    app = APP(sk_string, pk_string, server_url)
    logger.info("全体初始化完成")

    # # DEBUG模式 将自己添加到主节点列表
    # # 仅限DEBUG模式，线上模式需要申请加入主节点
    # app.mainNode.mainNodeList.addMainNode(node_info=app.mainNode.nodeInfo)
    # app.storageGenesisBlock()
    # #

    # 获取主节点列表（读取配置文件）
    if not app.loadMainNodeListBySeed():
        logger.error("无法获得任何主节点IP的地址，请检测网络或者配置文件")
        # 关闭所有线程并退出
        app.stopAllSub(app.subList)
        app.server.stop()
        exit()
    # 同步数据
    app.getCurrentEpochByOtherMainNode()
    app.synchronizedBlockOfBeings()

    # 订阅
    app.reSubscribe()

    # 检查主节点列表，即此时只有读取权限，没有写入权限
    # 不再主节点列表时，可接受订阅数据

    phase1 = False
    phase2 = False
    phase3 = False

    # 保证再前30秒进入
    while STime.getSecond() >= 30:
        logger.info("请稍等")
        time.sleep(1)

    while True:
        if app.mainNode.mainNodeList.userPKisExit(user_pk=app.user.getUserPKString()):
            if 0 <= STime.getSecond() < 30 and phase1 is False:
                app.startNewEpoch()
                phase1 = True
                logger.info("第一阶段完成：此时时间：" + str(STime.getSecond()))

            if 30 <= STime.getSecond() < 40 and phase1 is True and phase2 is False:
                app.startCheckAndApplyDeleteNode()
                phase2 = True
                logger.info("第二阶段完成：此时时间：" + str(STime.getSecond()))

            if 40 <= STime.getSecond() < 60 and phase1 is True and phase2 is True and phase3 is False:
                i = 0
                while not app.startCheckAndSave():
                    i += 1
                    logger.info("第" + str(i) + "次尝试")
                    time.sleep(0.1)
                    if STime.getSecond() >= 50:
                        logger.warning("当前周期未能成功收集所有区块")
                        app.blockRecoveryOfBeings()
                        break
                logger.info("第三阶段完成：此时时间：" + str(STime.getSecond()))

                app.addEpoch()
                if app.getEpoch() % 20160 == 0:
                    # 进入下一个选举周期
                    app.addElectionPeriod()
                    logger.info("进入下一个选举周期")

                if app.getEpoch() % 1440 == 0:
                    # 校对时间
                    if not STime.proofreadingTime():
                        logger.warning("请校对系统时间，当前时间与NTP时间误差超过一秒")
                phase1 = False
                phase2 = False
                phase3 = False
            time.sleep(0.1)
        else:
            try:
                if 0 <= STime.getSecond() < 30 and phase1 is False:
                    logger.info("当前节点不是主节点,请在其他主节点处进行申请")
                    logger.info("节点信息如下：")
                    logger.info(app.mainNode.getNodeInfo())
                    logger.info("节点签名如下：")
                    logger.info(app.mainNode.getNodeSignature())

                    app.startNewEpoch()
                    phase1 = True
                    logger.info("第一阶段完成：此时时间：" + str(STime.getSecond()))
                if STime.getSecond() >= 40 and phase1 is True:
                    if not app.startCheckAndSave():
                        logger.warning("当前周期未能成功收集所有区块")
                        app.blockRecoveryOfBeings()
                    app.addEpoch()
                    if app.getEpoch() % 20160 == 0:
                        # 进入下一个选举周期
                        app.addElectionPeriod()
                        logger.info("进入下一个选举周期")
                    if app.getEpoch() % 1440 == 0:
                        # 校对时间
                        if not STime.proofreadingTime():
                            logger.warning("请校对系统时间，当前时间与NTP时间误差超过一秒")
                    phase1 = False
            except Exception as error:
                logger.exception(error)
            time.sleep(1)


if __name__ == "__main__":
    argv = sys.argv[1:]
    # 私钥
    private_key_string = ""
    # 公钥
    public_key_string = ""
    # 平台服务网址
    url = ""
    try:
        opts, args = getopt.getopt(argv, "s:p:u:")  # 短选项模式
    except Exception as err:
        print(err)
        exit()

    for opt, arg in opts:
        if opt == "-s":
            private_key_string = arg
        if opt == "-p":
            public_key_string = arg
        if opt == "-u":
            url = arg

    if not CipherSuites.verifyPublicAndPrivateKeys(private_key_string, public_key_string):
        print("公钥与私钥不匹配")
        exit()
    if url == "":
        print("server_url不能为空")
        exit()
    run(private_key_string, public_key_string, url)
