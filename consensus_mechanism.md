## 共识机制

### 节点

#### 概念

1. 主节点：拥有区块的读写权限、投票权限和监督审核其他主节点权限。
2. 简单节点：拥有区块的读权限。


#### 合约
1. 主节点加入

   在一台具有公网IP的服务器上，下载程序并且同步完成数据之后，即可成为简单节点。在此基础上，提交申请书并且有超过50%（含50%）的主节点同意之后，即可成为主节点。

2. 主节点退出

   方式一：在众生区块生成的过程中，若某主节点A未能按照预期产生区块或广播不产生区块的消息，则认为该主节点已经违规离线，其他主节点将在短期内自动达成共识，将某主节点A删除。
   
   方式二：任何阶段，若有任意主节点认为某主节点A违反了社区条约，即可向全网广播删除A的申请书，当在规定时间内，有超过50%（含50%）的主节点同意之后，即可删除主节点A。

### 生命记录区块

1. 众生区块

   众生区块的生成周期为一分钟，每周期N个主节点各生成一个众生区块，共N个区块。每个周期分为三个阶段，第一个阶段目的是生成区块，第二个阶段目的是检测是否收集到当前周期产生的所有区块，第三个节点是，若未收集完全，则进行数据恢复。

   产生区块的主节点选取规则为：

   1. 将所有主节点按照节点ID的字典顺序升序排列。
   2. 将上一众生区块生成周期生成的众生区块按照区块ID的字典顺序升序排列。
   3. 计算上一周期的最后一个区块的哈希值，并将该哈希值作为随机种子。
   4. 随机挑选N个主节点，并去重。

   N的计算方式为：当主节点数量小于等于20时，N等于2；当主节点数量大于20时，N的等于主节点数量除以10并向下取整。

2. 时代区块

   时代区块用来推荐众生区块，其区块主体记录推荐的众生区块的ID和生成众生区块的公钥列表。

   在一个选举周期之内，主节点推荐某众生区块A，并维护A的投票数据。所有用户都可以参与投票，当投票数量达到T的时候,即可生成时代区块。

   每个选举周期会清零所有投票数据并重新计算每个用户的票数信息。

   T = 1024

3. 垃圾区块

   垃圾区块用来标记众生区块，其区块主体记录推荐的众生区块的ID和生成众生区块的公钥列表。

   在一个选举周期之内，主节点标记某众生区块A，并维护A的投票数据。所有用户都可以参与投票，当投票数量达到G的时候,即可生成垃圾区块。

   每个选举周期会清零所有投票数据并重新计算每个用户的票数信息。

   G = 1024



### 投票机制

票的最小分隔值为0.1票。

1. 短期票

   主节点每产生一个众生区块，则主节点所在的用户获得1个短期票，主节点可将票的一部分的投票权授予做出一定贡献的普通用户。

   默认方式为：每产生一个众生区块，主节点授予记录该众生区块的普通用户0.5短期票。

   短期票有效期为8个选举周期。

2. 长期票

   每产生一个时代区块或垃圾区块，生成它的主节点即可获得一个长期票。另外，时代区块推荐的众生区块中主节点和普通用户都将获得1个长期票。

   长期票有效期为128个选举周期。

3. 惩罚票

   1. 主节点。主节点产生的众生区块每被标记为一个垃圾区块，则被扣除一定的票数。假设被标记了G个区块，则扣除：8*（2^G-1）个票。
   2. 普通用户。普通用户的众生区块每被标记为一个垃圾区块，则普通用户的长期票数会被扣除50%并向下取整。

   惩罚票永久有效。



   
