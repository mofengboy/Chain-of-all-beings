import time


class STime:

    # 获取毫秒级时间戳
    @staticmethod
    def getTimestamp():
        return int(round(time.time() * 1000))


if __name__ == "__main__":
    STime.getTimestamp()
