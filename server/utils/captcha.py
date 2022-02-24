import gvcode
import hashlib
import time

Storage_Time = 300  # 五分钟


class Captcha:
    def __init__(self):
        self.__captchaStorage = {}

    # 生成验证码
    def generate(self):
        pic_base64, word = gvcode.base64()
        uuid = hashlib.md5(str(pic_base64).encode("utf-8")).hexdigest()[0:8]
        self.__captchaStorage[uuid] = [
            word.lower(),  # 转为小写
            time.time()
        ]
        return uuid, pic_base64

    # 验证验证码
    def verify(self, uuid, word) -> bool:
        # 清楚过期验证码
        for uuid_i in self.__captchaStorage:
            data = self.__captchaStorage[uuid_i]
            if time.time() - data[1] > Storage_Time:
                del self.__captchaStorage[uuid_i]

        try:
            if self.__captchaStorage.pop(uuid)[0] == word.lower():
                return True
            else:
                return False
        except Exception as err:
            # print(err)
            return False


if __name__ == "__main__":
    captcha = Captcha()
    for i in range(5):
        captcha.generate()
