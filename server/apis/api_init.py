from server.database import DB
from server.models import Auth, BlockOfBeings, MainNodeManager, ChainOfBeings, BackStageInfo, BlockOfTimes, Vote, \
    ChainOfTimes, BlockOfGarbage, ChainOfGarbage

db = DB()
auth = Auth(db=db)
backstageInfo = BackStageInfo(db)
blockOfBeings = BlockOfBeings(db)
blockOfTimes = BlockOfTimes(db)
blockOfGarbage = BlockOfGarbage(db)
mainNodeManager = MainNodeManager(db)
chainOfBlock = ChainOfBeings()
chainOfTimes = ChainOfTimes()
chainOfGarbage = ChainOfGarbage()
vote = Vote(db)
