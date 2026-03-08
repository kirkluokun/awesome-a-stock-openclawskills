# Fact Checker 架构设计文档

## 系统概览

```
输入 (Markdown)
    ↓
[文档解析] → 章-节-小节-段落层级结构
    ↓
[Phase 1: Splitter Agent] (并发=5, 模型=2.0-flash, 无搜索)
    拆句（一句一个 T{index}）
    ├→ 句子分类：factual / subjective
    ├→ 事实句提取声明：[claim1, claim2, ...]
    └→ 主观句跳过
    ↓
[Phase 2: Verifier Agent] (并发=3, 模型=2.5-flash, 带搜索)
    逐句核查（仅对 factual 句，其中 claims 非空）
    ├→ 每个 claim 用 Google Search 搜索
    ├→ 判定：verified / incorrect / not_found
    └→ 返回：verdict + details + sources
    ↓
[输出]
├→ _sentences.json     (Phase 1 结果：全句、分类、声明)
├→ _factcheck.json     (Phase 2 结果：完整核查)
└→ _issues.json        (仅问题数据：incorrect + not_found)
```

## 数据结构

### Phase 1 输出：SentenceFact

```python
@dataclass
class SentenceFact:
    id: str              # C2.S1.P3.T2
    chapter: str
    section: str
    paragraph_index: int
    sentence_index: int  # T{n}
    sentence: str        # 原始句子
    type: str            # "factual" / "subjective"
    claims: list[str]    # ["claim1", "claim2", ...] 或 []
```

### Phase 2 输出：ClaimResult

```python
@dataclass
class ClaimResult:
    id: str              # C2.S1.P3.T2.K1
    chapter: str
    section: str
    paragraph_index: int
    sentence_index: int  # T2
    sentence: str        # 原始句子
    claim: str           # 具体声明
    verdict: str         # "verified" / "incorrect" / "not_found"
    details: str         # 核查说明或正确数据
    sources: list[str]   # 搜索结果 URL
```

## 并发管理

使用 `asyncio.Semaphore` 限制并发数：

```python
# Phase 1
split_sem = asyncio.Semaphore(5)   # 默认 5 个并发
split_coros = [
    split_paragraph(..., split_sem, progress)
    for ...
]
results = await asyncio.gather(*split_coros)

# Phase 2
verify_sem = asyncio.Semaphore(3)  # 默认 3 个并发
verify_coros = [
    verify_sentence(..., verify_sem, progress)
    for ...
]
results = await asyncio.gather(*verify_coros)
```

异步安全的进度追踪：

```python
class Progress:
    def __init__(self, total: int, label: str):
        self.total = total
        self.done = 0
        self.label = label
        self._lock = asyncio.Lock()

    async def tick(self, tag: str = ""):
        async with self._lock:
            self.done += 1
            print(f"  [{self.label}] {self.done}/{self.total}...")
```

## 拆句分类规则（Phase 1）

### Factual 判断标准

包含以下内容的句子：
- **具体数字**：金额、百分比、比例、数量
  - 例：`"GDP 的 2.92%"`、`"695.1 万亿印尼盾"`
- **日期/时间**：年月日、季度、时间点
  - 例：`"2025 年 2 月 17 日"`、`"2026 年"`
- **法律法规**：法律名称、条例号、具体条款
  - 例：`"2025 年第 8 号政府条例"`、`"第 3/2020 号法律"`
- **组织/人名 + 具体行为**：公司名 + 数据或行为
  - 例：`"Freeport Indonesia 出口铜精矿"`
- **排名/份额/产量**：市场地位、全球占比、生产规模
  - 例：`"全球镍产量的 60.2%"`、`"44 家冶炼厂"`
- **政策参数**：具体的政策措施和数值
  - 例：`"100% 全额留存"`、`"12 个月锁定期"`

### Subjective 判断标准

以下句子归为 subjective：

**显式标志词**：
- `"说白了"`, `"说穿了"`, `"如果说"`, `"通俗点说"`, `"简单来说"`
- `"我认为"`, `"我们预测"`, `"预计将"`, `"标志着"`（无具体数据时）
- `"意味着"`（无量化后果时）、`"这就好比"`、`"通俗来讲"`

**隐性标志**：
- 纯评论：`"这一决策的背后是赤裸裸的财政诉求"` → subjective
- 比喻：`"这就好比一个走钢丝的人"` → subjective
- 总结性陈述：`"综上所述，..."`（若无具体数据）→ subjective
- 修辞/过渡：`"接下来的故事核心变了"`、`"这标志着..."`（无量化内容）→ subjective

## 核查流程（Phase 2）

### 搜索策略

对每个 claim，Gemini 执行：

1. **中文搜索**：原始 claim 的中文关键词
2. **英文搜索**：翻译成英文重新搜索
3. **印尼语搜索**（如涉及印尼）：关键词用印尼语
4. **多语言交叉验证**：用不同语言的结果对比

### Verdict 逻辑

| 情况 | Verdict | 备注 |
|------|---------|------|
| 搜索结果明确确认数据 | `verified` | 列出来源 URL |
| 搜索结果显示不同数据 | `incorrect` | 给出正确数据 + 来源 |
| 多次搜索都找不到 | `not_found` | 说明尝试的关键词 |
| API 调用失败 | `not_found` | 记录失败原因 |

## 成本优化

### Phase 1 为什么用 2.0-flash？

- 不需要搜索，纯文本分析
- 2.0-flash 便宜 3-5 倍
- 拆句分类是确定性任务，无需复杂推理
- 可以用高并发（5）快速处理

### Phase 2 为什么用 2.5-flash？

- 需要搜索集成和复杂搜索推理
- 2.5-flash 搜索能力更强
- 核查任务需要更好的推理（判断搜索结果的相关性）
- 用低并发（3）保证质量

### 成本计算

假设文档：100 段落 → 200 句子 → 50% factual → 100 句 → 200 claims

```
Phase 1:
  100 个 split_paragraph() 并发调用
  cost ≈ 0.3$ (2.0-flash)

Phase 2:
  100 个 factual 句 → verify_sentence()
  每句平均 2 claims → 200 个搜索
  cost ≈ 3-5$ (2.5-flash + search)

总成本：3-6$ / 100 段落文档
```

## 错误处理

### JSON 解析失败

若 Gemini 返回非法 JSON：

```python
try:
    items = parse_json_response(text)
except json.JSONDecodeError:
    # 返回一个 sentinel 对象标记错误
    return [SentenceFact(
        ...
        type="factual",
        claims=["[提取失败，需人工核查]"]
    )]
```

Phase 2 会将其标记为 `not_found`。

### API 超时/限流

使用指数退避重试：

```python
for attempt in range(max_retries + 1):
    try:
        resp = await client.aio.models.generate_content(...)
        return resp.text
    except Exception as e:
        if attempt < max_retries:
            delay = base_delay * (2 ** attempt)  # 5s, 10s, 20s...
            await asyncio.sleep(delay)
```

## 编号规则

```
C{章}.S{节}.SS{小节}.P{段}.T{句}.K{声明}

例：C2.S1.SS2.P3.T5.K2
└─ C2       第 2 章（C1 是文档标题）
   └─ S1    第 1 节（## 标题）
      └─ SS2 第 2 小节（### 标题）
         └─ P3 第 3 段落（段落计数在节内重置）
            └─ T5 第 5 个句子（句子计数在段落内）
               └─ K2 第 2 个声明（声明计数在句子内）
```

### 计数重置规则

- 章级改变 → 节、小节、段、句、声明计数全重置
- 节级改变 → 小节、段、句、声明计数全重置
- 小节级改变 → 段、句、声明计数全重置
- 段落改变 → 句、声明计数重置
- 句子改变 → 声明计数重置

## 输出格式

### _sentences.json

```json
{
  "document": "article.md",
  "timestamp": "2026-02-13T...",
  "split_model": "gemini-2.0-flash",
  "statistics": {
    "total_sentences": 100,
    "factual": 50,
    "subjective": 50,
    "total_claims": 120
  },
  "sentences": [
    {
      "id": "C2.S1.P1.T1",
      "chapter": "第一章：...",
      "section": "1.1 ...",
      "paragraph_index": 1,
      "sentence_index": 1,
      "sentence": "...",
      "type": "factual",
      "claims": ["claim1", "claim2"]
    }
  ]
}
```

### _factcheck.json

```json
{
  "document": "article.md",
  "timestamp": "2026-02-13T...",
  "models": {
    "split": "gemini-2.0-flash",
    "verify": "gemini-2.5-flash"
  },
  "statistics": {
    "total_sentences": 100,
    "factual_sentences": 50,
    "subjective_sentences": 50,
    "total_claims": 120,
    "verified": 110,
    "incorrect": 5,
    "not_found": 5
  },
  "results": [
    {
      "id": "C2.S1.P1.T1.K1",
      "sentence": "...",
      "claim": "...",
      "verdict": "verified",
      "details": "...",
      "sources": ["https://..."]
    }
  ]
}
```

## 扩展点

### 添加新的模型

在 CLI 参数中支持自定义模型：

```bash
python fact_checker.py doc.md \
  --split-model gemini-2.0-pro \
  --verify-model gemini-1.5-pro
```

### 添加新的搜索工具

当前仅支持 Google Search。可扩展为：
- Bing Search
- DuckDuckGo
- 特定领域的学术搜索（如 PubMed）

### 添加用户反馈循环

当前输出是静态的。可扩展为：
- 接受用户标注：`"这个 not_found 其实是对的，来自 XYZ 报告"`
- 学习主观/客观分类的误判案例
- 逐步改进拆句算法

## 调试技巧

### 查看具体哪句被分错

```bash
python fact_checker.py doc.md --split-only -o output/
# 查看 output/doc_sentences.json
# 找出 type 字段为错误分类的句子
```

### 逐个调试某句的搜索

```python
# 手动调用 Phase 2
from fact_checker import verify_sentence, SentenceFact

fact = SentenceFact(
    id="C2.S1.P1.T1",
    ...
    claims=["要调试的声明"],
)

result = asyncio.run(verify_sentence(
    client, "gemini-2.5-flash", fact,
    asyncio.Semaphore(1), ...
))
```

### 性能监控

运行时观察日志：

```bash
python fact_checker.py doc.md 2>&1 | tee run.log
# 查看进度百分比和时间
```

计算吞吐量：

```python
# Phase 1: 段落/秒
100 paragraphs / 30 seconds = 3.3 para/sec

# Phase 2: 声明/秒
200 claims / 120 seconds = 1.7 claims/sec
```
