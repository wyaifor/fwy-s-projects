"""Generate the complete W7-W10 name-concept-relation-example exam table."""

from pathlib import Path
import json

ROOT = Path(__file__).parent
DIST = ROOT / "dist"

REL_EX = {
    "w7-01": ("这是 W7 的总入口。后续 valid time、transaction time、temporal table 和时间 SQL 都是在回答数据库如何保留并查询变化。", "员工从 Analyst 升为 Manager：普通 UPDATE 会覆盖旧职位；temporal DBMS 保存两个有效区间，因此仍能回答三月份的职位。"),
    "w7-02": ("Instant、interval、period 是描述时间的基础语言，也决定范围过滤、窗口边界和是否重复计数。", "[09:00,10:00) 包含 09:00、不包含 10:00；10:00 进入下一个小时窗口。INTERVAL '30 minutes' 只有长度，没有时间轴位置。"),
    "w7-03": ("把一个事实拆成现实时间和数据库时间；两条时间线同时存在就是 bitemporal，也是追溯修正的基础。", "合同 1 月生效，但数据库 2 月才录入：valid time 从 1 月开始，transaction time 从 2 月开始。"),
    "w7-04": ("时间语义落到表和查询上：current 看现在，sequenced 在对应有效时段运算，nonsequenced 把时间列当普通数据。", "查询‘当前工资’用 current；查询‘2025-06-01 当时有效的工资’是 as-of/sequenced；只按年份统计时间列可视为 nonsequenced。"),
    "w7-05": ("传统 start/end 列依赖人工条件；SQL:2011 PERIOD 与 PostgreSQL range 把区间语义交给数据库，并可由 GiST 加速重叠查询。", "会议室预订冲突可用 range overlap 运算判断；普通 B-tree 不适合二维区间重叠，GiST 更合适。"),
    "w7-06": ("同一时间序列的两种存储粒度：point-based 便于逐点过滤和更新；sequence-based 减少行数但必须维护数组顺序与对齐。", "温度每分钟一行是 point-based；一天一行并保存 timestamps[] 与 values[] 是 sequence-based。"),
    "w7-07": ("把时间数据变成统计答案的标准执行链：WHERE 筛原始行，GROUP BY 建组，聚合压缩每组，HAVING 再筛聚合结果。", "求每年 7 月平均交易量：WHERE 取月份 7，GROUP BY 年份，AVG(volume)，ORDER BY year。"),
    "w7-08": ("CTE 是复杂查询的命名中间步骤，可把清洗、过滤和聚合拆开检查；它连接可读性与查询计划，但不等于自动缓存。", "WITH july AS (...) SELECT year, AVG(volume) FROM july GROUP BY year；可先单独运行 july 检查过滤是否正确。"),
    "w7-09": ("PostgreSQL 数组实现 sequence-based 表示；array_agg 从多行收集，unnest 再展开。顺序必须由 ORDER BY 明确指定。", "array_agg(price ORDER BY ts) 生成按时间排列的价格数组；unnest(prices) 恢复成多行。"),
    "w7-10": ("这是 PostgreSQL 数组在 Spark 中的对应做法。多列不能分别无序 collect_list，应先绑定为 struct 再排序，避免时间和值错位。", "collect_list(named_struct('ts',ts,'open',open)) → sort_array → transform；element_at 在 Spark 中常用 1-based 索引。"),
    "w7-11": ("连接数据写入、更新策略与时间表示。覆盖还是追加取决于业务语义，Unix 时间单位决定日期是否正确。", "把 1710000000 当毫秒会落到 1970 年附近；应先判断它是秒，再乘 1000 或使用正确转换函数。"),
    "w7-12": ("把 W7 全部知识串成可复现管线：读取、检查、时间转换、排序、过滤聚合、点/序列转换和可视化。", "Bitcoin CSV：检查 schema/行数 → 转 timestamp → 按年统计 7 月交易量 → 核对结果 → 绘图；每一步保留可检查输出。"),

    "w8-01": ("W8 从数据结构转向表示学习。非结构化不等于没有结构，而是结构不能直接由固定关系表完整表达，必须先提取特征。", "一张 JPEG 有文件格式和像素排列，但‘猫的耳朵’不是现成列；文本也有字符顺序，却没有可直接用于模型的固定数值列。"),
    "w8-02": ("ML pipeline 把原始数据依次转换为特征、模型和预测；监督学习依赖标签，无监督学习从未标注数据寻找结构。", "垃圾邮件分类有 spam/not-spam 标签，属于监督学习；按文章相似度聚类没有标签，属于无监督学习。"),
    "w8-03": ("图像先成为像素矩阵，再转换为颜色、纹理、边缘或深度特征。手工特征与深度特征都是把内容映射成向量。", "RGB 图片每个像素有三个通道；CNN 前层常学边缘，后层组合成形状与对象。调整尺寸会改变像素数量和计算成本。"),
    "w8-04": ("文本预处理位于原文和向量化之间；目标是减少无关差异，同时保留任务所需语义。", "小写化让 Data/data 合并；tokenization 把句子拆成 token；停用词删除可能有用，但情感任务不能随意删除 not。"),
    "w8-05": ("Count/BoW 只记录词出现次数；TF-IDF 在词频上降低全库常见词权重。二者通常产生高维稀疏矩阵。", "若‘database’只在少数文档出现，它的 IDF 较高；‘the’到处出现，权重较低。CountVectorizer 先学习词表再输出向量。"),
    "w8-06": ("向量表示使文档可比较；cosine 看方向相似度，适合文本稀疏向量，距离或相似度的选择必须与特征尺度匹配。", "[1,1,0] 与 [2,2,0] 方向相同，cosine 接近 1，即使长度不同；最相似文档应取 cosine 最大值。"),
    "w8-07": ("Word2Vec 给一个词相对固定的向量；BERT 根据上下文产生表示；GPT 按序列预测并生成。三者解决的问题和输出粒度不同。", "bank 在 river bank 和 bank loan 中，Word2Vec 通常只有一个向量；BERT 会根据上下文生成不同表示。"),
    "w8-08": ("图像特征也可进入传统 ML 流程：读取图像 → 标准化 → 提取特征向量 → 降维/训练 → 评估。", "可用颜色直方图比较整体色彩，用 CNN embedding 比较语义；不能直接把不同尺寸图片的原始像素拼接后比较。"),
    "w8-09": ("Metadata 描述数据的来源、时间、位置、格式和作者；它可辅助检索和特征工程，但可能缺失、错误或被修改。", "JPEG 的 EXIF 可含拍摄时间、GPS 和相机型号；ExifTool 可批量导出，但没有 GPS 不代表照片内容没有地点信息。"),
    "w8-10": ("高级特征工程连接数据与模型：编码、缩放、交叉、降维和选择都必须只在训练集上拟合，以防 data leakage。", "先在全数据计算标准化均值再划分训练/测试会泄漏测试信息；正确做法是 fit(train)，再 transform(train/test)。"),
    "w8-11": ("这是 W8 文件夹中的可运行练习，用点式与序列式时间数据复习数组、展开、排序和可视化，并强化 W7 的时间序列能力。", "Bitcoin 点记录按时间排序 → 用 array_agg/collect_list 构建序列 → 用 UNNEST/explode 展开 → 核对记录数与顺序 → 绘图。"),

    "w9-01": ("W9 的入口：stream 是潜在无界、持续到达的事件序列；batch 是有界数据集。流处理必须面对乱序、迟到和持续状态。", "传感器每秒持续上报是 stream；昨天完整日志文件是 batch。把流切成窗口后才能得到有限范围的统计。"),
    "w9-02": ("DBMS 通常保存数据后由一次查询读取；DSMS 让连续查询长期运行，事件到来时增量更新结果。", "‘每5分钟平均温度’不是每次手工运行 SQL，而是注册持续查询，由新事件不断更新窗口结果。"),
    "w9-03": ("Publish/Subscribe 用 broker 将 producer 与 consumer 解耦；发布者不知道具体订阅者，订阅者按 topic 接收。", "温度传感器发布到 building/1/temp；告警服务和仪表盘可同时订阅，彼此无需直接连接。"),
    "w9-04": ("MQTT 是轻量消息协议；topic 是分层字符串，callback 在消息到达时执行；+ 匹配一层，# 匹配后续所有层。", "home/+/temp 匹配 home/kitchen/temp；home/# 还能匹配 home/kitchen/humidity。on_message callback 负责 bytes 解码和 JSON 解析。"),
    "w9-05": ("QoS 在传输成本与重复/丢失风险间权衡：0 至多一次，1 至少一次，2 恰好一次的协议交付；retain 与 QoS 是不同概念。", "普通温度遥测可用 QoS0；不能丢但能去重的订单通知可用 QoS1；QoS1 可能重复，所以 consumer 应幂等。"),
    "w9-06": ("Kafka 把 topic 分成持久、有序的 partition log；partition 内有序，offset 标识位置，consumer group 分摊分区。", "同一 order_id 作为 key 可进入同一 partition 保序；不同 partition 之间没有全局顺序。增加 consumer 超过 partition 数不会继续提高并行度。"),
    "w9-07": ("Stateless 只看当前事件；stateful 保存跨事件信息。窗口聚合、去重和 join 都需要状态，也因此需要 checkpoint 和状态清理。", "把摄氏度转换成华氏度是 stateless；计算每个设备最近10分钟平均值是 stateful。"),
    "w9-08": ("窗口把无界流切成有限集合：tumbling 不重叠，sliding 可重叠，session 由活动间隔决定。窗口长度和步长决定重复计入。", "10分钟 tumbling：每条事件只进一个窗口；长度10分钟、每5分钟滑动的 sliding window 中，一条事件可能进入两个窗口。"),
    "w9-09": ("三种时间解释同一事件：event time 是源头发生，ingestion time 是进入平台，processing time 是算子处理。正确性通常优先 event time。", "12:00 产生的事件因断网 12:05 才到达：event time=12:00，ingestion/processing time 约为12:05。"),
    "w9-10": ("Watermark 是系统对 event-time 进度的估计，用来关闭窗口和清理状态；allowed lateness 决定迟到事件还能否修改结果。", "watermark=12:10、允许迟到2分钟时，event time=12:09 通常仍可处理；非常晚的事件可能丢弃或进入 side output。"),
    "w9-11": ("Stream-table join 用流事件查稳定/更新较慢的维表；stream-stream join 双方都无界，必须用 key 与时间范围限制缓存。", "订单流 join 产品表取得类别；点击流 join 购买流需限定同一用户且购买发生在点击后30分钟内。"),
    "w9-12": ("把消息传输与计算框架串联：MQTT/Kafka 负责事件进入和缓冲，Spark/Flink 负责分布式转换、状态和窗口。", "CSV→JSON→publisher→broker/topic→subscriber callback→bytes decode→json.loads→数值转换→窗口/绘图；先启动 receiver 再启动 publisher。"),

    "w10-01": ("W10 的入口：scalability 同时看负载、资源和性能；speedup 固定数据加资源，scale-up goal 让数据与资源同比增长仍保持时间。", "T1=100秒、4节点T4=30秒，则 speedup=3.33 而非理想4；数据和资源都翻倍而响应时间不变，符合课程的 scale-up goal。"),
    "w10-02": ("扩展设计把计算移近数据、消除单点瓶颈，并用重试、复制、checkpoint 和监控处理失败。性能必须同时看 latency、throughput、成本与可靠性。", "增加机器后若所有数据仍要穿过单一 coordinator，瓶颈没有消失；大量 shuffle 也会让网络而非 CPU 成为限制。"),
    "w10-03": ("存储布局决定工作负载：row store 适合整行事务；column store/Parquet 适合扫描少数列和聚合；wide-column 是数据库模型，不等于列式文件。", "查询一名客户完整记录偏 row store；扫描十亿行只求 sales 列平均值偏 Parquet。Parquet 的 row group、列块和统计量支持跳读。"),
    "w10-04": ("Partitioning 把不同数据子集分布到节点，提高容量与并行；range 利于范围查询，hash 更均匀。分区键必须匹配访问模式并避免 skew。", "按 customer_id hash 分区通常均匀；按 state 分区时 NSW 数据过大可能成为热点。跨分区 join 会产生昂贵 shuffle。"),
    "w10-05": ("Replication 保存相同数据副本以提高可用性和读取能力；同步复制更一致但延迟高，异步更快但可能读旧值或丢最后写入。", "leader 写成功后立刻返回、随后复制给 follower 属于异步；leader 故障时尚未复制的最后一次写入可能丢失。"),
    "w10-06": ("MongoDB sharding 将 collection 分片：mongos 路由，config servers 保存集群元数据，每个 shard 通常是 replica set。sharding 与 replication 职责不同。", "查询包含 shard key 时 mongos 可定向到一个 shard；缺少 shard key 可能 scatter-gather 到所有 shards。"),
    "w10-07": ("CAP 讨论网络分区发生时的一致性与可用性取舍；P 不是平时可随意关闭的按钮。最终一致性表示停止更新后副本最终收敛。", "网络分区时银行余额系统可能拒绝部分请求以保一致；社交点赞可暂时返回旧计数以保持可用，之后收敛。"),
    "w10-08": ("HDFS 把大文件切成 block 并复制到 DataNode；NameNode 管理文件系统和 block 元数据。客户端先问 NameNode 位置，再直接读 DataNode。", "读取文件时 NameNode 不传输全部数据；它返回 block locations，客户端优先读取邻近副本。小文件过多会增加 NameNode 元数据压力。"),
    "w10-09": ("MapReduce 把计算拆成 map、shuffle/sort、reduce；map 产生键值对，shuffle 按 key 聚集，reduce 汇总。Combiner 只能用于可安全局部合并的运算。", "WordCount：map 输出(word,1)，shuffle 聚集同词，reduce 求和。平均值不能只平均各分区平均数，应传 sum 和 count。"),
    "w10-10": ("Spark 用 driver 构建 DAG，executors 执行 tasks；transformations 是 lazy，action 才触发 job。窄依赖可流水线，宽依赖通常产生 shuffle。", "filter/select 只构建计划；count/collect/write 触发执行。groupByKey 会 shuffle；collect 把全部结果送回 driver，可能内存溢出。"),
    "w10-11": ("DataFrame 与 Spark SQL 共享 Catalyst 优化和执行引擎；应提供 schema、尽早过滤、使用内建函数并让聚合留在集群端。", "df.filter(...).groupBy('year').avg('volume') 与临时视图 SQL 可表达同一计划；先聚合再 toPandas，避免把原始大表拉到 driver。"),
    "w10-12": ("Spark 与 Flink 都能批流处理；Spark 强在统一 SQL/ML 生态，Flink 强在原生连续流、event time 和大状态低延迟。框架名称本身不保证 exactly-once。", "离线湖仓 SQL 与 ML pipeline 常选 Spark；复杂乱序事件与低延迟 stateful streaming 常选 Flink。端到端语义还取决于 source、checkpoint 和 sink。"),
    "w10-13": ("Tutorial 用 local[*] 验证与集群相同的 DataFrame/DAG 逻辑，但不能证明多节点性能；最终结果必须由代码、输入和核对指标重现。", "本地读取 Bitcoin → printSchema/count → 时间转换 → 聚合 → explain → 小结果 toPandas/绘图；再用分区数、shuffle、skew 判断真实扩展风险。"),
}

raw = (DIST / "study-data.js").read_text(encoding="utf-8").strip()
study = json.loads(raw[len("const STUDY_DATA=") : -1])

rows = []
for week in study["weeks"]:
    for lesson in week["lessons"]:
        relation, example = REL_EX[lesson["id"]]
        rows.append({
            "week": week["id"].upper(),
            "id": lesson["id"],
            "name": lesson["title"],
            "trigger": lesson["trigger"],
            "concept": lesson["decision"],
            "relation": relation,
            "example": example,
            "code": lesson["code"],
            "trap": lesson["trap"],
        })

assert len(rows) == 48
(DIST / "exam-table-data.js").write_text(
    "const EXAM_TABLE_DATA=" + json.dumps(rows, ensure_ascii=False, separators=(",", ":")) + ";\n",
    encoding="utf-8",
)
print(f"Generated {len(rows)} narrative rows")
