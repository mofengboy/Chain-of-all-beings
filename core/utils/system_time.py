import logging
import time
import ntplib

logger = logging.getLogger("main")


class STime:
    # 获取毫秒级时间戳
    @staticmethod
    def getTimestamp():
        return int(round(time.time() * 1000))

    # 获取秒级时间戳
    @staticmethod
    def getSecondTimestamp() -> str:
        return str(round(time.time() * 1000))[0:10]

    # 获取秒
    @staticmethod
    def getSecond():
        return int(time.strftime("%S"))

    # 校对系统时间
    @staticmethod
    def proofreadingTime() -> bool:
        system_time = STime.getTimestamp()
        NTP_time = STime.getNTPTime()
        if abs(system_time - NTP_time) > 1000:
            return False
        else:
            return True

    # 获取NTP时间
    @staticmethod
    def getNTPTime():
        c = ntplib.NTPClient()
        for i in range(5):
            try:
                response = c.request('cn.pool.ntp.org')
                return int(str(response.tx_time * 1000)[0:13])
            except Exception as err:
                logger.warning(err)
                logger.info("第" + str(i + 1) + "次尝试重连ntp服务器")
        logger.warning("时间校对失败！")
        return STime.getTimestamp()


if __name__ == "__main__":
    print(STime.getSecond())
