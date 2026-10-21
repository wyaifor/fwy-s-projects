from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph


ROOT = Path(__file__).parent
OUT = ROOT / "output" / "pdf"
OUT.mkdir(parents=True, exist_ok=True)
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
MONO = r"C:\Windows\Fonts\consola.ttf"
pdfmetrics.registerFont(TTFont("YaHei", FONT))
pdfmetrics.registerFont(TTFont("YaHeiBold", FONT_BOLD))
pdfmetrics.registerFont(TTFont("Consolas", MONO))

PAGE = landscape(A4)
BLUE = colors.HexColor("#2359A8")
INK = colors.HexColor("#17222B")
MUTED = colors.HexColor("#45525A")
PALE = colors.HexColor("#EEF4FF")
ORANGE = colors.HexColor("#D65F26")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def section(title, bullets, code=None, alert=None):
    return dict(title=title, bullets=bullets, code=code, alert=alert)


QUIZ2 = [
    [
        [section("W7 时间三概念", ["Instant=时刻；Interval=时长；Period=[start,end) 有边界时间段。", "半开区间：start <= t AND t < end；连续窗口不重复边界。", "Valid time=现实何时为真；Transaction time=数据库何时知道；二者都有=Bitemporal。", "Current 查当前；Sequenced 按时间语义；Nonsequenced 把时间列当普通列。"], alert="timestamp 列本身不等于 temporal DBMS。"),
         section("W7 Temporal SQL / Range", ["期间重叠：a.start < b.end AND b.start < a.end。", "PostgreSQL tsrange/tstzrange：&& overlap；@> contains；GiST 加速 range 查询。", "当前版本常用 end='infinity'；更新历史=关闭旧 period + 插入新版本。"], code="WHERE ts >= :s AND ts < :e\nvalid_period && tstzrange(:s,:e,'[)')"),
         section("W7 SQL 做题顺序", ["逻辑顺序：FROM/JOIN -> WHERE筛行 -> GROUP BY分组 -> aggregate -> HAVING筛组 -> SELECT -> ORDER BY。", "非聚合 SELECT 列必须在 GROUP BY；WHERE 不能筛 AVG/COUNT，HAVING 可以。", "CTE(WITH)给中间结果命名，便于检查；不保证缓存或更快。"], code="WITH c AS (...)\nSELECT k,AVG(v) FROM c\nWHERE ts>=:s AND ts<:e\nGROUP BY k HAVING COUNT(*)>=2;"),
         section("题干词 -> 秒选", ["real world -> VALID；recorded/knew -> TRANSACTION。", "aggregate condition -> HAVING；row condition -> WHERE。", "rare term -> TF-IDF；contextual -> BERT；generation -> GPT。", "topic/broker -> MQTT；micro-batch -> Spark；pipeline -> Flink。", "same-key order/replay -> Kafka；lightweight IoT -> MQTT。", "partition+latest -> CP；partition+must respond -> AP。"], alert="多选逐项判断；ONLY/ALWAYS/AUTOMATICALLY 常为陷阱。")],
        [section("W7 时序存储与数组", ["Point-based=每时刻一行：易筛选/join/update。Sequence-based=一行含有序序列：易整段读取。", "array_agg(value ORDER BY ts) 保证顺序；unnest 展开。PostgreSQL 数组常从1开始。", "Spark collect_list 不保证顺序：先收集 (ts,value) struct，再 sort_array；explode 展开。", "多个平行数组会错位；把整条记录作为 struct 一起排序。"], code="array_agg(v ORDER BY ts)\nsort_array(collect_list(named_struct('ts',ts,'v',v)))", alert="Spark [] 从0开始；element_at(arr,1) 从1开始。"),
         section("W7 输入与检查", ["10位 Unix 常为秒，13位常为毫秒；先看数量级与日期范围。", "显式列名 INSERT 更安全；append 增加，overwrite/UPDATE 可能破坏历史。", "端到端：读入 -> schema/NULL/重复 -> 时间转换 -> 排序 -> 半开过滤 -> 聚合 -> 核对 count/min/max -> 画图。"]),
         section("W8 数据与 ML 决策", ["Structured=固定表；Semi-structured=JSON/XML 键存在但结构可变；Unstructured=文本/图像/音频。", "有 label=Supervised：离散=classification，连续=regression；无 label=clustering/topic modelling。", "正确顺序：split -> 只在 train fit 预处理/模型 -> validation 调参 -> test 一次最终评估。"], alert="先用全数据标准化、选特征、建词表 = data leakage。")],
        [section("W8 文本特征", ["Tokenise分词；normalise统一形式；stemming粗截；lemmatisation按语言规则还原。清洗必须看任务，not 可能不能删。", "BoW/Count=词频，忽略词序；n-gram保留局部顺序但维度更高。", "TF-IDF=tf(t,d)*log(N/df(t))：降低到处出现的词，提高区分词；矩阵通常 sparse。"], code="cos(A,B)=A·B/(||A|| ||B||)\nJaccard=|A∩B|/|A∪B|"),
         section("W8 向量与模型", ["文本稀疏向量常用 cosine：越大越相似；集合用 Jaccard；同尺度连续值才常用 Euclidean。", "Word2Vec=静态词向量；BERT=双向上下文表示，适合理解/分类；GPT=自回归 next-token，擅长生成。", "Embedding 把对象映射成稠密向量，向量近邻用于语义检索。"]),
         section("W8 图像 / Metadata / Feature", ["图像常为 HxWxC；RGB=3 channel，grayscale=1；检查 RGB/BGR、0-255/0-1、尺寸与 dtype。", "CNN 学局部特征；ViT 将图像切 patch 用 attention；语义检索比较 embedding，不是逐像素。", "EXIF 可含时间/GPS/设备；文件修改时间不等于拍摄时间。", "Feature：interaction、polynomial、lag/rolling、encoding；时间特征绝不能看未来。"]),
         section("W8 ExifTool 直接识别", ["-TAG=读取指定标签；\"-GPS*\"匹配GPS标签；*.jpg匹配输入文件。", "-csv/-json决定输出格式；>是shell重定向，不是ExifTool参数。", "CreateDate不一定等于DateTimeOriginal/真实拍摄时间；metadata可缺失、错误或被改。"], code="exiftool -common -csv *.jpg > metadata.csv\nexiftool \"-GPS*\" photo.jpg")]
    ],
    [
        [section("W9 Stream / DSMS / Pub-Sub", ["Stream=持续到达、理论无界；需增量处理、窗口、状态、乱序/重复处理。", "DBMS：data persistent/query transient；DSMS：query persistent/data transient。", "Publisher -> topic -> broker -> subscriber；broker 解耦双方，但不自动保证 exactly-once。", "Broker(Kafka/MQTT)负责传输/缓冲；engine(Spark/Flink)负责窗口、状态、计算。"]),
         section("W9 MQTT", ["轻量 Pub/Sub。订阅 sensor/+/temp：+匹配一层；sensor/#：#匹配后续任意层且只能在末尾。", "消息到达触发 callback；retained message 与历史日志不是同一概念。", "QoS0=at most once；QoS1=at least once(可重复)；QoS2=协议单跳 exactly once(成本最高)。"], code="client.subscribe('sensor/+/temp')\ndef on_message(client, userdata, msg): ...", alert="QoS2 不等于端到端业务恰好一次；sink 仍需事务/幂等/去重。"),
         section("W9 Kafka", ["Topic 分 partitions；只保证 partition 内顺序，无跨 partition 全局顺序。", "offset=partition 内位置；同 consumer group 中一个 partition 同时给一个 consumer。", "key 决定分区可保同 key 顺序；consumer 数>partition 数时有人空闲。", "Kafka 是持久化可重放日志，复制提高容错。"])] ,
        [section("W9 状态与窗口", ["Stateless：map/filter 只看当前事件。Stateful：count/dedup/window/running total/join 需历史状态。", "Tumbling=固定不重叠；Sliding=固定可重叠；Session=活动间隔；Count=按条数。", "size=统计范围；slide=输出频率；state 需 checkpoint、TTL/清理。"]),
         section("W9 三种时间 + Watermark", ["Event time=源头发生；Ingestion time=进入平台；Processing time=算子处理。业务乱序分析优先 event time。", "Watermark≈max observed event time - tolerated out-of-orderness，用于关闭窗口与清状态。", "新事件 event_time <= watermark 通常为 late；可丢弃、更新结果或 side output，取决于配置。", "等更久：结果更完整但延迟/状态更大。"], alert="watermark 是进度估计，不保证之前绝不会再来数据。"),
         section("W9 Join / 框架", ["Stream-table：用维表 enrichment；表版本决定用最新值还是历史一致值。", "Stream-stream：按 key + 时间范围，否则两边状态可能无限增长。", "Spark Structured Streaming：micro-batch为主、批流统一；Flink：原生逐事件、event-time/state强。"], code="ON a.key=b.key\nAND b.ts BETWEEN a.ts-INTERVAL '5 min' AND a.ts+INTERVAL '5 min'"),
         section("W9 Tutorial 一条主线", ["CSV row(dict) -> json.dumps(string) -> publish(topic) -> broker -> subscriber。", "msg.payload(bytes) -> decode(string) -> json.loads(dict) -> float -> deque(maxlen=N)/plot。", "先开receiver并订阅，再开publisher；QoS0+retain=False可能错过早期消息。", "Local CSV replay只验证callback/plot，不证明真实MQTT连接。"], code="client.on_message=on_message\nclient.connect(broker,1883)\nclient.loop_forever()")],
        [section("W10 扩展与存储", ["Vertical=加强单机；Horizontal=加节点；Elasticity=自动伸缩。Speedup=同一工作更快；Scaleup=数据/资源同比增长而时间近似不变。", "Row store：整行写/点查；Column store：少数列扫描/聚合；Parquet=列式文件；Wide-column=数据库模型，不是同一概念。", "数据本地性减少网络；shuffle、串行协调、倾斜常是瓶颈。"]),
         section("W10 Partition / Replication / CAP", ["Range partition利范围查但易热点；Hash较均匀但范围散开；好 key 均匀且匹配查询。", "Replication提高可用/读扩展：sync一致但慢；async快但故障可丢未复制写。复制不是备份。", "CAP：发生 network partition(P) 时在 Consistency(C) 与 Availability(A)间取舍；不是平时永久‘三选二’。"]),
         section("W10 Mongo / HDFS / MapReduce", ["Mongo：mongos路由；config servers存元数据；shards存数据且常为replica sets；无 shard key 易 scatter-gather。", "HDFS：NameNode管文件/block位置元数据；DataNode存实际 blocks；适合大文件顺序吞吐，不适合大量小文件。", "Map -> (k,v)；shuffle/sort 按 key 重分布；reduce 聚合。shuffle 常最贵。"]),
         section("W10 Spark 必写", ["Driver 建 DAG/调度；executors 处理 partitions；transformation 惰性，action 才执行。", "map/filter/select=transformation；count/collect/write=action；宽依赖常触发 shuffle/stage。", "优先内建 DataFrame 函数；大数据不要 collect()/toPandas() 到 driver。"], code="df.filter(F.col('x')>0)\\\n  .groupBy('k').agg(F.avg('v'))\ndf.createOrReplaceTempView('t')\nspark.sql('SELECT ... FROM t')")]
    ]
]


FINAL = [
    [
        [section("W1 Data Engineering / Pipeline", ["Data engineering：把 raw data 变成高质量、一致、可供 analytics/ML 使用的信息。", "生命周期：generation/source -> acquisition/ingestion -> storage -> transformation -> serving；横切 security、DataOps、architecture、orchestration。", "Source=数据起点；sink=输出目的地；pipeline=按依赖连接的处理步骤。Batch处理有界批次；stream持续处理无界事件。"]),
         section("W1 Unix 高频", ["pipe | 把左命令 stdout 交给右命令；>覆盖，>>追加；grep筛行；wc -l计行；head/tail查看；cut选列；sort排序；uniq只去除相邻重复。"], code="sort names.txt | uniq\ngrep -i 'error' log.txt | wc -l\ncut -d',' -f1 file.csv | sort | uniq -c"),
         section("W2 Acquisition / Ingestion", ["优先官方 API：结构化、稳定、面向程序；无 API 才 scraping。Pull=消费者主动定期取；Push=事件发生即发送，适合低延迟。", "Batch适合周期历史数据；stream适合连续实时。CDC 捕捉 insert/update/delete 变化。", "工程判断：volume、velocity、variety、刷新频率、权限、rate limit、失败重试、幂等。"]),
         section("W2 Cleaning / Quality", ["Profiling先看 schema、count、NULL、distinct、range、format、duplicates、outliers。", "Validation=检查约束，不等于修复：类型/日期格式/范围/唯一性/引用完整性。", "Cleaning：统一单位/日期/类别、处理缺失、去重、标准化；保留 raw 与审计记录。", "Missing：删、填补或标记取决于机制/任务；异常值先验证，不可盲删。"])] ,
        [section("W3 Relational DB", ["表=rows+columns；schema定义类型/约束。PK唯一非空标识行；FK引用另一表 PK，保证 referential integrity。", "1NF原子值；2NF消除对复合键部分依赖；3NF消除非键对非键传递依赖。规范化减少冗余，反规范化换取读性能。", "INNER只匹配；LEFT保留左表；NULL 用 IS NULL；COUNT(*)含所有行，COUNT(col)忽略NULL。"]),
         section("SQL 模板", ["WHERE筛行；GROUP BY分组；HAVING筛聚合组；ORDER BY排序。非聚合 SELECT 列必须在 GROUP BY。", "JOIN 先明确 grain 和 key，避免 many-to-many 行数爆炸；先查每边 key 是否唯一。"], code="SELECT a.k, COUNT(*) n, AVG(b.v) av\nFROM a LEFT JOIN b ON a.id=b.a_id\nWHERE a.ts>=:s AND a.ts<:e\nGROUP BY a.k HAVING COUNT(*)>1\nORDER BY av DESC;"),
         section("Warehouse / Lake / ETL", ["OLTP：频繁小事务、当前细节、规范化；OLAP：扫描聚合、历史分析、星型模型。", "Fact表=度量+维度FK，grain必须先定义；Dimension=描述属性；star简单，snowflake更规范。", "ETL先转换再入仓；ELT先加载 raw 再在目标中转换。Data warehouse=schema-on-write curated；Data lake=schema-on-read保存raw/多类型；lakehouse试图兼具。", "Data mart服务部门；staging是临时加工区。"])] ,
        [section("W4 Web API / HTTP", ["API优于 scraping：结构稳定、机器接口、常有文档。GET读取，POST提交；参数可在 URL/query/body；响应常 JSON/XML。", "检查 status code：2xx成功，4xx客户端/认证/限流，5xx服务端；处理 timeout、retry+backoff、pagination、rate limit。", "先检查 content-type 与 schema，再解析；认证密钥不写入代码仓库。"], code="r=requests.get(url,params=p,timeout=30)\nr.raise_for_status(); data=r.json()"),
         section("W4 Scraping", ["HTML由 DOM tree 组成；CSS selector/XPath定位元素。先遵守 robots/条款/频率。", "BeautifulSoup：select/select_one、get_text(strip=True)、get('href')；动态JS页面可能需浏览器或找底层API。", "选择稳定语义属性，避免脆弱绝对路径；记录抓取时间和来源URL。"], code="soup=BeautifulSoup(html,'html.parser')\nfor x in soup.select('table tbody tr'): ..."),
         section("W5 Semi-structured / JSON", ["JSON object={}键值；array=[]有序列表；值可嵌套。灵活 schema 允许缺失/额外字段与异构类型。", "解析嵌套时逐层访问并处理缺失；normalize/flatten 要避免数组导致行爆炸。", "字段名表达 schema，日期/时间应作为值：{'values':[{'date':'2026-01-01','sales':100}]}，便于范围查询和索引。"]),
         section("W5 NoSQL / MongoDB", ["Key-value：按key超快；Document(MongoDB)：BSON文档+嵌套；Wide-column：row key/column family；Graph：node/edge关系遍历。", "MongoDB 存 documents，支持 nested structure、灵活schema，不是SQL主语言也不是graph DB。", "Embed适合一起读取且有界的一对少；Reference适合共享、增长、独立更新。索引提速读但增加写/空间。"], code="db.col.find({status:'A',score:{$gte:80}})\ndb.col.createIndex({status:1})")]
    ],
    [
        [section("W6 Spatial 基础", ["Geometry：Point/LineString/Polygon/MultiPolygon。Spatial join 如 point-in-polygon；predicate：intersects/within/contains；distance/nearest。", "CRS定义坐标含义；EPSG:4326是经纬度。经纬顺序常 lon,lat。不同 CRS 必须先 transform，不能只改标签。", "Geometry常平面单位；Geography/投影可用于地球距离。经纬度直接用欧氏距离会失真。"], code="ST_Point(lon,lat)\nST_Within(point, polygon)\nST_Intersects(a,b)\nST_Distance(a,b)"),
         section("W6 Index / 格式", ["Spatial index(R-tree等)用 bounding boxes 先过滤候选，减少精确几何计算；加速查询但不转换 CRS，也不限 point。", "Shapefile 是多文件集合(.shp/.shx/.dbf/.prj)；GeoJSON易交换；WKT是文本几何表示。", "空间连接前验证 geometry有效性、CRS、范围、空值与边界语义。"], alert="正确选项：空间索引可加速查询、减少需精算的 geometry；不会自动坐标转换。"),
         section("W7 Temporal 超压缩", ["Valid=现实有效；Transaction=数据库知道；Bitemporal=两者。Period用[start,end)；overlap：a.s<b.e AND b.s<a.e。", "WHERE筛行 -> GROUP BY -> aggregate -> HAVING筛组。array_agg 内 ORDER BY；Spark collect_list 不保序。", "PostgreSQL range：&& overlap，@> contains，GiST索引。"]),
         section("W8 Unstructured 超压缩", ["有label监督：分类/回归；无label无监督：聚类/topic。split后只在train fit，防 leakage。", "BoW词频；TF-IDF=tf*log(N/df)；文本向量常cosine。Word2Vec静态，BERT上下文理解，GPT next-token生成。", "图像HxWxC；检查尺寸/通道/范围；metadata(EXIF)可结构化但可能缺失/错误。"])] ,
        [section("W9 Broker / Semantics", ["Pub/Sub：producer->topic->broker->consumer。MQTT +一层/#多层；QoS0最多一次、1至少一次、2单跳恰好一次。", "Kafka=分区持久日志；partition内有序；offset为位置；同group一个partition同一时刻给一个consumer；key保同key顺序。", "端到端 exactly-once 需要source+checkpoint+transactional/idempotent sink。"]),
         section("W9 Time / Window / State", ["Event=发生，Ingestion=入平台，Processing=执行；乱序业务用event time。", "Tumbling不重叠；Sliding可重叠；Session按空闲间隔。Watermark≈max event time-容忍乱序，用于关窗/清state，不是绝对保证。", "map/filter无状态；count/dedup/window/join有状态。stream-stream join必须key+时间界。"]),
         section("W10 Storage / Distribution", ["行存适合整行写/点查；列存/Parquet适合列扫描聚合；wide-column不是分析型列存。", "Range partition利范围但易热点；hash均匀；skew使全作业等最慢分区。Replication提可用，不是backup。", "CAP：网络分区时C与A取舍。Mongo：mongos路由/config元数据/shards数据。", "HDFS：NameNode元数据，DataNode blocks。MapReduce：map->shuffle/sort->reduce。"]),
         section("W10 Spark", ["Driver建DAG，executors跑partitions；transformation惰性，action触发。宽依赖常shuffle。", "select/filter/groupBy/agg/join；temp view 后 spark.sql。避免collect/toPandas大数据，优先内建函数。", "Flink原生逐事件/event-time/state强；Spark micro-batch、统一批流与SQL生态强。"], code="df.filter(F.col('x')>0)\\\n  .groupBy('k').agg(F.avg('v'))")],
        [section("选择题触发词 -> 直接选", ["real-time/as soon as occurs -> push/stream；structured programmatic access -> Web API。", "raw now, unknown future use, transform later -> data lake/ELT。", "DOM + CSS selectors -> scraping；documents + nested -> MongoDB。", "current row overwritten -> need temporal history；late/out-of-order -> event time + watermark。", "scan few columns/aggregate -> columnar/Parquet；hotspot -> bad partition key/skew。", "same key ordering/replay -> Kafka partition；IoT轻量 -> MQTT。"]),
         section("代码题自检", ["1 写清输入 grain/key/time unit。2 用半开时间范围。3 JOIN前检查唯一性。4 WHERE与HAVING分清。5 聚合后核对count/min/max。", "JSON先看 object/array nesting；SQL处理NULL用IS NULL/COALESCE；空间先CRS；流式写window/time/watermark。"]),
         section("常见绝对化陷阱", ["‘always/only/automatically/exclusively’多为错：NoSQL不代表无schema；index不改CRS；QoS2不保证整管道恰好一次；更多partition/机器不必然更快。", "相似度越大越近，距离越小越近；BETWEEN含两端；COUNT(col)不计NULL；LEFT JOIN后在WHERE筛右表可能变INNER效果。"]),
         section("10分钟读题法", ["圈动词：define/compare/design/calculate/write SQL；圈约束：real-time、late、range、latest、all rows。", "选择题先排除类别错误和绝对化陈述；多选逐项判真，不凭‘看起来像两个’。", "简答用四句：定义 -> 机制 -> 为什么适合本题 -> 一个限制/陷阱。SQL先写FROM/JOIN和WHERE，再GROUP/HAVING/SELECT。"])]
    ]
]


def make_styles(font_size):
    return {
        "body": ParagraphStyle("body", fontName="YaHei", fontSize=font_size, leading=font_size * 1.34, textColor=INK, spaceAfter=1),
        "title": ParagraphStyle("title", fontName="YaHeiBold", fontSize=font_size + 1.65, leading=(font_size + 1.65) * 1.18, textColor=colors.white, leftIndent=4),
        "code": ParagraphStyle("code", fontName="Consolas", fontSize=font_size - .35, leading=(font_size - .35) * 1.22, textColor=colors.HexColor("#F4F7F8"), leftIndent=5, rightIndent=4),
        "alert": ParagraphStyle("alert", fontName="YaHei", fontSize=font_size - .15, leading=font_size * 1.25, textColor=colors.HexColor("#7C2D12"), leftIndent=4),
    }


def block_height(sec, width, styles):
    h = 18
    for b in sec["bullets"]:
        _, x = Paragraph("• " + esc(b), styles["body"]).wrap(width - 10, 1000); h += x + 1
    if sec.get("code"):
        _, x = Paragraph(esc(sec["code"]).replace("\n", "<br/>"), styles["code"]).wrap(width - 10, 1000); h += x + 8
    if sec.get("alert"):
        _, x = Paragraph("⚠ " + esc(sec["alert"]), styles["alert"]).wrap(width - 10, 1000); h += x + 7
    return h + 6


def draw_block(c, sec, x, top, width, styles):
    h = block_height(sec, width, styles)
    c.setFillColor(colors.white); c.roundRect(x, top - h, width, h, 5, fill=1, stroke=0)
    c.setFillColor(BLUE); c.roundRect(x, top - 18, width, 18, 5, fill=1, stroke=0)
    title_p = Paragraph(esc(sec["title"]), styles["title"])
    title_p.wrap(width - 8, 17)
    title_p.drawOn(c, x + 3, top - 15)
    y = top - 23
    for b in sec["bullets"]:
        p = Paragraph("• " + esc(b), styles["body"]); _, ph = p.wrap(width - 10, 1000); p.drawOn(c, x + 5, y - ph); y -= ph + 1
    if sec.get("code"):
        code = Paragraph(esc(sec["code"]).replace("\n", "<br/>"), styles["code"]); _, ch = code.wrap(width - 10, 1000)
        c.setFillColor(INK); c.roundRect(x + 4, y - ch - 5, width - 8, ch + 6, 3, fill=1, stroke=0); code.drawOn(c, x + 5, y - ch - 2); y -= ch + 8
    if sec.get("alert"):
        p = Paragraph("⚠ " + esc(sec["alert"]), styles["alert"]); _, ah = p.wrap(width - 10, 1000)
        c.setFillColor(colors.HexColor("#FFF1E8")); c.roundRect(x + 4, y - ah - 4, width - 8, ah + 6, 3, fill=1, stroke=0); p.drawOn(c, x + 5, y - ah - 1)
    return h


def build_pdf(path, pages, title, subtitle, font_size):
    c = Canvas(str(path), pagesize=PAGE)
    W, H = PAGE; margin = 16; gap = 7; header = 33; footer = 12
    colw = (W - margin * 2 - gap * 2) / 3
    styles = make_styles(font_size)
    for page_no, columns in enumerate(pages, 1):
        c.setFillColor(colors.HexColor("#F5F2EA")); c.rect(0, 0, W, H, fill=1, stroke=0)
        c.setFillColor(INK); c.setFont("YaHeiBold", 15); c.drawString(margin, H - 20, title)
        c.setFont("YaHei", 7); c.setFillColor(MUTED); c.drawRightString(W - margin, H - 19, subtitle)
        max_bottom = footer + 5
        for ci, sections in enumerate(columns):
            x = margin + ci * (colw + gap); y = H - header
            for sec in sections:
                h = block_height(sec, colw, styles)
                if y - h < max_bottom:
                    raise RuntimeError(f"Overflow {path.name} page {page_no} col {ci+1}: {sec['title']} bottom={y-h:.1f}")
                draw_block(c, sec, x, y, colw, styles); y -= h + 5
        c.setFont("YaHei", 6.5); c.setFillColor(MUTED)
        c.drawString(margin, 5, f"{title} · Side {'A' if page_no == 1 else 'B'} · 2026-10-21")
        c.drawRightString(W - margin, 5, f"第 {page_no}/2 页｜打印：A4 横向、实际大小、双面短边翻转")
        c.showPage()
    c.save()


quiz = OUT / "COMP5339_Quiz2_W7-W10_A4_Double_Sided_Cheatsheet.pdf"
final = OUT / "COMP5339_Final_W1-W10_A4_Double_Sided_Cheatsheet.pdf"
build_pdf(quiz, QUIZ2, "COMP5339 Quiz 2 考场速查", "W7-W10 · 题干触发词 + 判断规则 + SQL/公式 + 陷阱", 8.25)
build_pdf(final, FINAL, "COMP5339 期末考场速查", "W1-W10 · 一张 A4 双面 · 中英术语与答题模板", 7.35)
print(quiz)
print(final)
