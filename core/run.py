import sys
import logging.config
import time
import yaml

sys.path.append("../")

from core.app import APP
from core.utils.system_time import STime
from server.api import WebServer


def run():
    # 日志
    with open('./config/log_config.yaml', 'r') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)

    logger = logging.getLogger("main")

    # 校对系统时间，系统时间与NTP服务器时间不得超过1秒
    if not STime.proofreadingTime():
        # 抛出错误
        logger.info("系统时间与NTP服务器时间不得超过1秒")
        exit()

    # 启动后端服务（若已经定制化后端，此处可修改）
    WebServer().start()

    # 初始化核心 core
    app = APP()
    logger.info("全体初始化完成")

    # 获取主节点列表（读取配置文件）
    # app.loadMainNodeListBySeed()
    # 同步数据
    # app.getCurrentEpochByOtherMainNode()
    # app.synchronizedBlockOfBeings()

    # 订阅
    app.reSubscribe()

    # 循环获取主节点列表，检查自己是否在主节点列表内
    # 只有当自己成为主节点列表时，才继续执行，否则在此处等待，即此时只有读取权限，没有写入权限
    # 不再主节点列表时，可接受订阅数据
    while not app.mainNode.mainNodeList.userPKisExit(user_pk=app.user.getUserPKString()):
        logger.info("当前节点不是主节点")
        time.sleep(1)

    # # DEBUG模式 将自己添加到主节点列表
    # 仅限DEBUG模式，线上模式需要申请加入主节点
    # app.mainNode.mainNodeList.addMainNode(node_info=app.mainNode.nodeInfo)
    # #

    # 成为主节点后周期开始
    phase1 = False
    phase2 = False
    phase3 = False
    phase4 = False

    while True:
        if 0 <= STime.getSecond() < 30 and phase1 is False:
            app.startNewEpoch()
            phase1 = True
            logger.info("第一阶段完成：此时时间：" + str(STime.getSecond()))

        if 30 <= STime.getSecond() < 40 and phase1 is True and phase2 is False:
            app.startCheckAndApplyDeleteNode()
            phase2 = True
            logger.info("第二阶段完成：此时时间：" + str(STime.getSecond()))

        if 40 <= STime.getSecond() < 50 and phase1 is True and phase2 is True and phase3 is False:
            app.startCheckAndGetBlock()
            phase3 = True
            logger.info("第三阶段完成：此时时间：" + str(STime.getSecond()))

        if 50 <= STime.getSecond() < 60 and phase1 is True and phase2 is True and phase3 is True and phase4 is False:
            i = 0
            is_finish = True
            while not app.startCheckAndSave():
                i += 1
                logger.info("第" + str(i) + "次尝试")
                time.sleep(1)
                if STime.getSecond() < 50:
                    logger.warning("当前周期未能成功收集所有区块")
                    is_finish = False
                    break

            phase4 = True
            if is_finish:
                app.addEpoch()
                logger.info("第四阶段完成：此时时间：" + str(STime.getSecond()))
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
                phase4 = False
            else:
                logger.warning("第四阶段任务失败：此时时间：" + str(STime.getSecond()))
                # 主节点进入数据恢复阶段
                app.startDataRecovery()
                app.addEpoch()
                # 此处可能还有未考虑到的情况，例如进行数据恢复时，错过了下一个或下下一个..众生区块生存周期，如何再次进行数据恢复。

        time.sleep(1)


if __name__ == "__main__":
    run()
