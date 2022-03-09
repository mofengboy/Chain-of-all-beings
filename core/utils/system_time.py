import time
import ntplib


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
        response = c.request('pool.ntp.org')
        return int(str(response.tx_time * 1000)[0:13])


if __name__ == "__main__":
    print(STime.getSecond())
