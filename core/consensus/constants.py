# 最初的想法是这里根据总票数进行一个计算，但是似乎平均每1024个众生区块出一个时代区块也很合理，先这样。
VotesOfTimesBlockGenerate = 32.0
VotesOfGarbageBlockGenerate = 32.0
# 长期票有效时间为128个选举周期
LongTermVoteValidityPeriod = 128
# 规定的节点申请或删除审核时间（大约五天时间）
AUDIT_TIME = 432000000  # 13位时间戳