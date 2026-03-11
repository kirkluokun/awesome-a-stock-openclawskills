#!/usr/bin/env python3
"""
事实核查工具 (Fact Checker) v2 — 多 Agent 架构

两阶段流水线：
  Phase 1 (Splitter Agent)  — gemini-2.0-flash, 拆句+分类+提取声明
  Phase 2 (Verifier Agent)  — gemini-2.5-flash + Google Search, 逐句核查

用法:
    python fact_checker.py <markdown_file> [选项]

选项:
    -o, --output DIR         输出目录（默认为文件同目录）
    --split-model MODEL      Phase1 模型（默认 gemini-2.0-flash）
    --verify-model MODEL     Phase2 模型（默认 gemini-2.5-flash）
    --split-concurrency N    Phase1 并发数（默认 5）
    --verify-concurrency N   Phase2 并发数（默认 3）
    --chapters CHAPTERS      指定核查章节（逗号分隔，如 2,3,4）
    --dry-run                仅解析文档结构
    --split-only             仅执行 Phase1（拆句+分类），不核查
    --resume                 断点续接：跳过已完成的任务

环境变量:
    GOOGLE_API_KEY 或 GEMINI_API_KEY

输出:
    {stem}_sentences.json    Phase1 拆句结果（含编号）
    {stem}_factcheck.json    Phase2 完整核查结果
    {stem}_issues.json       仅 incorrect / not_found 条目
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# 自动加载 .env
try:
    from dotenv import load_dotenv
    _script_dir = Path(__file__).resolve().parent
    for _env in [
        _script_dir.parent.parent / ".env",
        _script_dir.parent / ".env",
        _script_dir / ".env",
        Path.cwd() / ".env",
    ]:
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass

from google import genai
from google.genai import types


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Section:
    """文档章节"""
    level: int
    title: str
    id_prefix: str
    chapter_title: str
    section_title: str
    paragraphs: list[str] = field(default_factory=list)


@dataclass
class SentenceFact:
    """Phase 1 输出：句子级事实提取"""
    id: str                     # C2.S1.P3.T2
    chapter: str
    section: str
    paragraph_index: int
    sentence_index: int
    sentence: str
    type: str                   # factual / subjective
    claims: list[str] = field(default_factory=list)


@dataclass
class ClaimResult:
    """Phase 2 输出：声明核查结果"""
    id: str                     # C2.S1.P3.T2.K1
    chapter: str
    section: str
    paragraph_index: int
    sentence_index: int
    sentence: str
    claim: str
    verdict: str                # verified / incorrect / not_found
    details: str
    sources: list[str] = field(default_factory=list)


# ============================================================
# 并发进度追踪
# ============================================================

class Progress:
    """异步安全的进度计数器"""

    def __init__(self, total: int, label: str):
        self.total = total
        self.done = 0
        self.label = label
        self._lock = asyncio.Lock()

    async def tick(self, tag: str = ""):
        async with self._lock:
            self.done += 1
            pct = self.done * 100 // self.total if self.total else 0
            msg = f"  [{self.label}] {self.done}/{self.total} ({pct}%)"
            if tag:
                msg += f"  {tag}"
            print(msg)


# ============================================================
# 增量写入器 — 每完成一个任务就原子更新 JSON
# ============================================================

class IncrementalWriter:
    """
    增量写入器：每完成一个任务，原子更新 JSON 文件。

    原子写入策略：先写 .tmp 再 rename，确保文件始终有效 JSON。
    支持断点续接：load_existing() 加载已有结果，跳过已完成的任务。
    """

    def __init__(self, path: Path, metadata: dict, items_key: str = "results"):
        """
        参数:
            path: 输出 JSON 文件路径
            metadata: 顶层元数据模板（不含结果数组）
            items_key: 结果数组的键名（"sentences" / "results" / "issues"）
        """
        self.path = path
        self.metadata = metadata
        self.items_key = items_key
        self.items: list[dict] = []
        self._lock = asyncio.Lock()

    async def append(self, new_items: list[dict]) -> None:
        """追加结果并立即原子写入文件"""
        async with self._lock:
            self.items.extend(new_items)
            self._flush()

    def _flush(self) -> None:
        """原子写入：写临时文件 → fsync → os.replace，确保数据持久化且文件始终有效"""
        data = {**self.metadata, self.items_key: self.items}
        tmp = self.path.with_suffix('.tmp')
        content = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
        try:
            os.write(fd, content)
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(str(tmp), str(self.path))

    def load_existing(self) -> list[dict]:
        """加载已有结果文件，用于断点续接"""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding='utf-8'))
                self.items = data.get(self.items_key, [])
                return self.items
            except json.JSONDecodeError:
                return []
        return []

    def get_completed_ids(self) -> set[str]:
        """提取已完成条目的 ID 集合"""
        return {item["id"] for item in self.items if "id" in item}

    def get_completed_prefixes(self) -> set[str]:
        """提取已完成的段落级前缀（C2.S1.P1.T1 → C2.S1.P1）"""
        prefixes: set[str] = set()
        for item in self.items:
            sid = item.get("id", "")
            # 要求必须包含 .T 分隔符，且前缀非空
            dot_t_pos = sid.rfind('.T')
            if dot_t_pos > 0:
                prefix = sid[:dot_t_pos]
                # 验证前缀格式（至少包含 C 和 P）
                if 'C' in prefix and 'P' in prefix:
                    prefixes.add(prefix)
        return prefixes


def _format_elapsed(seconds: float) -> str:
    """格式化耗时为人类可读字符串"""
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m}m{s}s"
    h, m = divmod(m, 60)
    return f"{h}h{m}m{s}s"


# ============================================================
# 通用工具函数
# ============================================================

# 不可重试的错误模式（认证/权限类，重试无意义）
_NONRETRIABLE_PATTERNS = (
    "invalid api key", "authentication", "permission denied",
    "403", "401", "api_key", "quota",
)


def _is_retriable(error: Exception) -> bool:
    """判断 API 异常是否值得重试（排除认证/权限错误）"""
    err_str = str(error).lower()
    return not any(p in err_str for p in _NONRETRIABLE_PATTERNS)


def _normalize_verdict(raw: str) -> str:
    """
    将模型返回的 verdict 标准化为三种之一: verified / incorrect / not_found。
    防止非标准 verdict 值绕过重试逻辑。
    """
    raw = raw.strip().lower()
    if raw in ("verified", "true", "correct", "confirmed", "accurate"):
        return "verified"
    if raw in ("incorrect", "false", "wrong", "inaccurate", "error"):
        return "incorrect"
    return "not_found"


def _validate_claim_item(item: dict) -> bool:
    """验证单条核查结果的 schema 是否完整（必须有 claim 和 verdict）"""
    if not isinstance(item, dict):
        return False
    if not item.get("claim"):
        return False
    if "verdict" not in item:
        return False
    return True


def _claim_similarity(a: str, b: str) -> float:
    """
    计算两个声明文本的相似度（0.0 ~ 1.0）。
    优先精确匹配，其次子字符串包含，最后字符重叠。
    """
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if a in b or b in a:
        return 0.9
    chars_a, chars_b = set(a), set(b)
    return len(chars_a & chars_b) / max(len(chars_a | chars_b), 1)


def _assign_results_to_slots(
    model_items: list[dict],
    slots: list[dict],
    round_num: int,
) -> None:
    """
    将模型返回的核查结果匹配到声明槽位（一对一，防止碰撞）。

    关键设计：
    - 用 used_indices 集合确保每个槽位最多被匹配一次
    - 分离 best_* 和 last_* 字段：best 只在变好时更新，last 总是更新
    - 所有 verdict 经过标准化
    """
    VERDICT_RANK = {"verified": 3, "incorrect": 2, "not_found": 1}
    used_indices: set[int] = set()

    for item in model_items:
        if not _validate_claim_item(item):
            continue

        model_claim = item.get("claim", "")
        verdict = _normalize_verdict(item.get("verdict", "not_found"))
        details = item.get("details", "")
        sources = item.get("sources", [])
        if not isinstance(sources, list):
            sources = []

        # 在未使用的槽位中找最佳匹配
        best_idx, best_score = -1, 0.0
        for idx, slot in enumerate(slots):
            if idx in used_indices:
                continue
            score = _claim_similarity(model_claim, slot["claim"])
            if score > best_score:
                best_idx, best_score = idx, score

        # 相似度过低则丢弃（防止错误匹配）
        if best_idx < 0 or best_score < 0.3:
            continue

        used_indices.add(best_idx)
        slot = slots[best_idx]

        # 记录本轮历史
        slot["history"].append({
            "round": round_num,
            "verdict": verdict,
            "details": details,
            "sources": sources,
        })

        # 更新最新一轮结果（无论好坏，用于下一轮 retry context）
        slot["last_verdict"] = verdict
        slot["last_details"] = details
        slot["last_sources"] = sources

        # 更新最佳结果（只在 verdict 更好时）
        if VERDICT_RANK.get(verdict, 0) > VERDICT_RANK.get(slot["best_verdict"], 0):
            slot["best_verdict"] = verdict
            slot["best_details"] = details
            slot["best_sources"] = sources


# ============================================================
# Markdown 解析器
# ============================================================

def parse_document(content: str) -> list[Section]:
    """将 Markdown 解析为章节列表，按 #/##/### 层级"""
    lines = content.split('\n')
    sections: list[Section] = []

    ch_idx = sec_idx = ss_idx = 0
    cur_chapter = cur_section = cur_title = cur_id = ""
    cur_level = 0
    cur_paragraphs: list[str] = []
    paragraph_buffer: list[str] = []

    def flush():
        nonlocal cur_paragraphs
        if not cur_title:
            cur_paragraphs = []
            return
        filtered = [
            p.strip() for p in cur_paragraphs
            if p.strip() and not p.strip().startswith('![') and p.strip() != '---'
        ]
        if filtered:
            sections.append(Section(
                level=cur_level, title=cur_title, id_prefix=cur_id,
                chapter_title=cur_chapter,
                section_title=cur_section if cur_level >= 2 else cur_title,
                paragraphs=filtered,
            ))
        cur_paragraphs = []

    def flush_buf():
        nonlocal paragraph_buffer
        if paragraph_buffer:
            cur_paragraphs.append(' '.join(paragraph_buffer))
            paragraph_buffer = []

    for line in lines:
        s = line.strip()
        if not s:
            flush_buf()
            continue

        heading = re.match(r'^(#{1,3})\s+(.+)$', s)
        if heading:
            flush_buf(); flush()
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 1:
                ch_idx += 1; sec_idx = ss_idx = 0
                cur_chapter = title; cur_section = ""
                cur_id = f"C{ch_idx}"
            elif level == 2:
                sec_idx += 1; ss_idx = 0
                cur_section = title
                cur_id = f"C{ch_idx}.S{sec_idx}"
            elif level == 3:
                ss_idx += 1
                cur_id = f"C{ch_idx}.S{sec_idx}.SS{ss_idx}"
            cur_level = level; cur_title = title
            continue

        if s.startswith('![') or s == '---':
            flush_buf(); continue

        if re.match(r'^[-*]\s+', s) or re.match(r'^\d+\.\s+', s):
            flush_buf()
            cur_paragraphs.append(s)
            continue

        paragraph_buffer.append(s)

    flush_buf(); flush()
    return sections


# ============================================================
# 通用 API 调用（带重试）
# ============================================================

async def call_gemini(
    client: genai.Client,
    model: str,
    prompt: str,
    use_search: bool = False,
    max_retries: int = 3,
    base_delay: float = 5.0,
) -> str:
    """
    调用 Gemini API，支持可选 google_search 工具。
    指数退避重试。
    """
    tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else None
    config = types.GenerateContentConfig(tools=tools, temperature=0.1)

    last_err = None
    for attempt in range(max_retries + 1):
        try:
            resp = await client.aio.models.generate_content(
                model=model, contents=prompt, config=config,
            )
            return resp.text
        except Exception as e:
            last_err = e
            # 不可重试的错误（认证/权限）立即抛出，不浪费重试次数
            if not _is_retriable(e):
                raise RuntimeError(f"API 不可重试错误: {e}") from e
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                print(f"    [重试] {attempt+1}/{max_retries}: {e}, {delay:.0f}s 后重试")
                await asyncio.sleep(delay)

    raise RuntimeError(f"API 失败（重试 {max_retries} 次）: {last_err}")


def parse_json_response(text: str) -> list[dict]:
    """
    从 Gemini 文本响应解析 JSON 数组。

    容错策略（按优先级）：
    1. 直接解析
    2. 去掉 ```json ... ``` 包裹后解析
    3. 用正则提取最外层 [...] 后解析
    4. 修复常见 JSON 错误（尾部逗号、未闭合引号）后解析
    5. 逐行扫描拼接多个 JSON 对象为数组
    """
    text = text.strip()

    # 策略 1: 直接解析
    try:
        result = json.loads(text)
        return result if isinstance(result, list) else [result]
    except json.JSONDecodeError:
        pass

    # 策略 2: 去掉 markdown 代码块（可能有多层或变体）
    cleaned = re.sub(r'```(?:json|JSON)?\s*\n?', '', text)
    cleaned = cleaned.strip()
    try:
        result = json.loads(cleaned)
        return result if isinstance(result, list) else [result]
    except json.JSONDecodeError:
        pass

    # 策略 3: 正则提取最外层 JSON 数组 [...]
    match = re.search(r'\[[\s\S]*\]', cleaned)
    if match:
        try:
            result = json.loads(match.group())
            return result if isinstance(result, list) else [result]
        except json.JSONDecodeError:
            pass

    # 策略 4: 修复常见错误后重试
    fixed = cleaned
    # 去掉尾部逗号 (,] → ])
    fixed = re.sub(r',\s*\]', ']', fixed)
    # 去掉尾部逗号 (,} → })
    fixed = re.sub(r',\s*\}', '}', fixed)
    if match:
        fixed_match = re.search(r'\[[\s\S]*\]', fixed)
        if fixed_match:
            try:
                result = json.loads(fixed_match.group())
                return result if isinstance(result, list) else [result]
            except json.JSONDecodeError:
                pass

    # 策略 5: 逐个提取 {...} 对象拼成数组（处理 Extra data 问题）
    objects = []
    for m in re.finditer(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', cleaned):
        try:
            obj = json.loads(m.group())
            objects.append(obj)
        except json.JSONDecodeError:
            continue
    if objects:
        return objects

    # 全部失败，抛出原始错误让上层处理
    return json.loads(text)


# ============================================================
# Phase 1: Splitter Agent — 拆句 + 分类 + 提取声明
# ============================================================

SPLIT_PROMPT = """\
你是一个精确的文本分析师。请将以下段落拆分为独立句子，并对每个句子分类。

**分类规则：**
- **factual**：包含可核查的具体事实——数字、金额、百分比、日期、法规名称及内容、组织/公司的具体行为、排名、产量/份额数据、具体政策参数
- **subjective**：主观判断、预测、比喻、评论、总结性描述

**典型 subjective 标志：**
"说白了"、"说穿了"、"这就好比"、"如果说"、"通俗点说"、"简单来说"、"我认为"、"我们预测"、"预计将"、"标志着"、"意味着"（无具体数据时）

**段落：**
{paragraph}

**以纯 JSON 数组返回（不要 ```json 标记）：**
[
  {{
    "sentence": "精确引用的原始句子",
    "type": "factual" 或 "subjective",
    "claims": ["可核查声明1", "可核查声明2"]
  }}
]

规则：
- subjective 句子的 claims 为空数组 []
- factual 句子必须列出每个可独立核查的数据点
- 一个句子中有多个数据点时，拆成多个 claim
- 纯修辞/连接/过渡句归为 subjective
只输出 JSON。"""


async def split_paragraph(
    client: genai.Client,
    model: str,
    section: Section,
    paragraph: str,
    p_idx: int,
    semaphore: asyncio.Semaphore,
    progress: Progress,
) -> list[SentenceFact]:
    """
    Phase 1: 对单个段落执行拆句和事实提取。
    使用 gemini-2.0-flash（快速、便宜、不需要搜索）。
    """
    tag = f"{section.id_prefix}.P{p_idx}"

    async with semaphore:
        try:
            prompt = SPLIT_PROMPT.format(paragraph=paragraph)
            text = await call_gemini(client, model, prompt, use_search=False)
            items = parse_json_response(text)
        except (json.JSONDecodeError, RuntimeError) as e:
            await progress.tick(f"{tag} [错误: {e}]")
            return [SentenceFact(
                id=f"{tag}.T1", chapter=section.chapter_title,
                section=section.section_title, paragraph_index=p_idx,
                sentence_index=1, sentence=paragraph[:100] + "...",
                type="factual", claims=["[提取失败，需人工核查]"],
            )]

        results = []
        for t_idx, item in enumerate(items, 1):
            results.append(SentenceFact(
                id=f"{tag}.T{t_idx}",
                chapter=section.chapter_title,
                section=section.section_title,
                paragraph_index=p_idx,
                sentence_index=t_idx,
                sentence=item.get("sentence", ""),
                type=item.get("type", "subjective"),
                claims=item.get("claims", []),
            ))

        factual_count = sum(1 for r in results if r.type == "factual")
        claim_count = sum(len(r.claims) for r in results if r.type == "factual")
        await progress.tick(f"{tag}: {len(results)}句, {factual_count}条事实, {claim_count}个声明")
        return results


# ============================================================
# Phase 2: Verifier Agent — 逐句核查
# ============================================================

# --- 文档摘要生成 prompt ---
CONTEXT_PROMPT = """\
请为以下文档生成一段精炼的核查背景摘要（3-5 句话），包含：
1. 文档讨论的核心国家/地区（如"印度尼西亚"）
2. 涉及的关键主体（政府机构、企业、人物）
3. 核心主题领域（如"矿产出口政策"）
4. 时间范围

这段摘要将用于引导搜索引擎核查文档中的数据，确保搜索结果指向正确的国家和主题。

**文档前 3000 字：**
{text_preview}

直接输出摘要文本，不要加标记。"""


async def generate_doc_context(
    client: genai.Client,
    model: str,
    content: str,
) -> str:
    """
    用 LLM 生成文档核查背景摘要。

    该摘要会作为上下文注入每个核查任务的 prompt，
    确保搜索时指向正确的国家和主题（避免中文搜索误匹配到中国）。
    """
    preview = content[:3000]
    prompt = CONTEXT_PROMPT.format(text_preview=preview)
    try:
        resp = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1),
        )
        return resp.text
    except Exception as e:
        print(f"  [警告] 文档摘要生成失败: {e}，使用空上下文")
        return ""


# --- 核查 prompt（含文档上下文）---
VERIFY_PROMPT = """\
你是一个严格的事实核查员。请对以下句子中的每个声明，使用 Google 搜索逐一核查。

**⚠️ 核查背景（重要）：**
{doc_context}
所有声明都来自上述背景中的国家/地区，搜索时必须锁定该国相关信息，不要混淆其他国家的数据。

**原始句子：**
{sentence}

**待核查声明：**
{claims_list}

**文档位置：** {chapter} > {section}

**核查要求：**
1. 每个声明单独搜索核查
2. **搜索语言优先级**：先用英文搜索，再用文档涉及国家的当地语言（如印尼语）搜索，最后才用中文搜索。中文资料容易混淆到中国的数据，必须交叉验证
3. 搜索关键词必须包含国家名称（如 "Indonesia"、"印尼"），避免歧义
4. verified → 简述确认来源
5. incorrect → 必须给出正确数据和来源
6. not_found → 说明尝试了哪些搜索关键词（含英文和当地语言）

**以纯 JSON 数组返回（不要 ```json 标记）：**
[
  {{
    "claim": "具体声明",
    "verdict": "verified 或 incorrect 或 not_found",
    "details": "核查说明",
    "sources": ["URL"]
  }}
]
只输出 JSON。"""


RETRY_PROMPT = """\
你是一个严格的事实核查员。以下声明在上一轮搜索中未能确认或被判定有误，请用**完全不同的搜索策略**重新核查。

**⚠️ 核查背景（重要）：**
{doc_context}
所有声明都来自上述背景中的国家/地区，搜索时必须锁定该国相关信息。

**原始句子：**
{sentence}

**待重新核查的声明：**
{claims_list}

**上一轮核查记录（第 {round_num} 轮，请避免重复相同搜索！）：**
{previous_attempts}

**重新核查策略（必须与上轮不同）：**
1. 换用完全不同的关键词组合（拆解声明、使用同义词、缩小/扩大范围）
2. 切换搜索语言：若上轮用英文，这轮用印尼语（Bahasa Indonesia）或反之
3. 搜索官方来源：政府公报、央行报告、统计局数据
4. 搜索新闻报道中的直接引用
5. 对 incorrect 声明：验证上轮给出的"正确数据"是否可靠，避免以错纠错
6. 对 not_found 声明：尝试搜索包含该数据的更大主题或相关政策名称

**以纯 JSON 数组返回（不要 ```json 标记）：**
[
  {{
    "claim": "具体声明",
    "verdict": "verified 或 incorrect 或 not_found",
    "details": "核查说明（含本轮使用的搜索关键词和语言）",
    "sources": ["URL"]
  }}
]
只输出 JSON。"""


async def verify_sentence(
    client: genai.Client,
    model: str,
    fact: SentenceFact,
    semaphore: asyncio.Semaphore,
    progress: Progress,
    doc_context: str = "",
    max_retry_rounds: int = 2,
) -> list[ClaimResult]:
    """
    Phase 2: 对单个事实句子的所有声明进行核查。

    核查流程（带上下文记忆的重试循环）：
    1. 以 fact.claims 为锚点初始化声明槽位（确保不丢声明）
    2. 首轮：用 VERIFY_PROMPT 核查全部声明，匹配结果到槽位
    3. 重试（最多 max_retry_rounds 轮）：
       - 用 last_* 字段（最新结果，非最佳结果）构建上下文
       - 用 RETRY_PROMPT 要求换关键词/语言重新搜索
       - best_* 只在 verdict 更好时更新，last_* 每轮都更新
    4. 返回最终结果（每个原始声明必定有一条结果）

    关键修复（来自 Codex review）：
    - 锚定 fact.claims 而非模型输出，防止声明丢失
    - 分离 best_*/last_*，确保 retry context 使用最新数据
    - _assign_results_to_slots 防止多对一碰撞
    - verdict 标准化，防止非标值绕过重试
    - 首轮失败时为每个声明生成独立结果
    """
    tag = fact.id

    async with semaphore:
        # === 初始化声明槽位（锚定到 fact.claims，确保不丢声明）===
        claim_slots: list[dict] = []
        for k_idx, original_claim in enumerate(fact.claims, 1):
            claim_slots.append({
                "id": f"{tag}.K{k_idx}",
                "claim": original_claim,
                "best_verdict": "not_found",
                "best_details": "",
                "best_sources": [],
                "last_verdict": "not_found",
                "last_details": "",
                "last_sources": [],
                "history": [],
            })

        # === 首轮核查 ===
        claims_text = "\n".join(f"  {i}. {c}" for i, c in enumerate(fact.claims, 1))
        prompt = VERIFY_PROMPT.format(
            doc_context=doc_context,
            sentence=fact.sentence,
            claims_list=claims_text,
            chapter=fact.chapter,
            section=fact.section,
        )

        first_round_ok = True
        try:
            text = await call_gemini(client, model, prompt, use_search=True)
            items = parse_json_response(text)
            # 匹配模型输出到声明槽位（一对一，防碰撞）
            _assign_results_to_slots(items, claim_slots, round_num=1)
        except (json.JSONDecodeError, RuntimeError) as e:
            first_round_ok = False
            # 首轮失败：为每个声明标记失败（不合并成单个 [核查失败]）
            for slot in claim_slots:
                slot["history"].append({
                    "round": 1, "verdict": "not_found",
                    "details": f"首轮核查失败: {e}", "sources": [],
                })
                slot["last_details"] = f"首轮核查失败: {e}"

        # === 重试循环：对 not_found / incorrect 的声明重新核查 ===
        for retry_round in range(2, max_retry_rounds + 2):
            # 收集需要重试的槽位
            failed_slots = [
                s for s in claim_slots
                if s["best_verdict"] in ("not_found", "incorrect")
            ]
            if not failed_slots:
                break  # 全部 verified，不需要重试

            # 构建重试 prompt：用 last_*（最新结果）而非 best_*
            retry_claims_text = "\n".join(
                f"  {i}. {s['claim']}"
                for i, s in enumerate(failed_slots, 1)
            )
            previous_text = "\n".join(
                f"  声明: {s['claim']}\n"
                f"    上轮判定: {s['last_verdict']}\n"
                f"    上轮说明: {s['last_details']}\n"
                f"    上轮来源: {', '.join(s['last_sources'][:3]) if s['last_sources'] else '无'}"
                for s in failed_slots
            )

            retry_prompt = RETRY_PROMPT.format(
                doc_context=doc_context,
                sentence=fact.sentence,
                claims_list=retry_claims_text,
                round_num=retry_round,
                previous_attempts=previous_text,
            )

            try:
                retry_text = await call_gemini(client, model, retry_prompt, use_search=True)
                retry_items = parse_json_response(retry_text)
                # 匹配到 failed_slots（不是全部 claim_slots，缩小匹配范围）
                _assign_results_to_slots(retry_items, failed_slots, round_num=retry_round)
            except (json.JSONDecodeError, RuntimeError):
                break  # 重试解析失败，保留已有结果

        # === 构建最终 ClaimResult 列表 ===
        results = []
        for slot in claim_slots:
            details = slot["best_details"]
            total_rounds = len(slot["history"])
            if total_rounds > 1:
                details = f"[经 {total_rounds} 轮核查] {details}"

            results.append(ClaimResult(
                id=slot["id"],
                chapter=fact.chapter,
                section=fact.section,
                paragraph_index=fact.paragraph_index,
                sentence_index=fact.sentence_index,
                sentence=fact.sentence,
                claim=slot["claim"],
                verdict=slot["best_verdict"],
                details=details,
                sources=slot["best_sources"],
            ))

        v = sum(1 for r in results if r.verdict == "verified")
        e = sum(1 for r in results if r.verdict != "verified")
        max_rounds = max((len(s["history"]) for s in claim_slots), default=1)
        retry_tag = f" (经{max_rounds}轮)" if max_rounds > 1 else ""
        status = f"✅{v}" + (f" ❌{e}" if e else "")
        await progress.tick(f"{tag}: {len(results)}声明 [{status}]{retry_tag}")
        return results


# ============================================================
# 增量包装器 — 任务完成后立即写入 JSON
# ============================================================

async def _split_and_write(
    client: genai.Client,
    model: str,
    section: Section,
    paragraph: str,
    p_idx: int,
    semaphore: asyncio.Semaphore,
    progress: Progress,
    writer: IncrementalWriter,
) -> list[SentenceFact]:
    """Phase 1 包装器：拆句完成后增量写入"""
    results = await split_paragraph(client, model, section, paragraph, p_idx, semaphore, progress)
    await writer.append([asdict(r) for r in results])
    return results


async def _verify_and_write(
    client: genai.Client,
    model: str,
    fact: SentenceFact,
    semaphore: asyncio.Semaphore,
    progress: Progress,
    claim_writer: IncrementalWriter,
    issues_writer: IncrementalWriter,
    doc_context: str = "",
) -> list[ClaimResult]:
    """Phase 2 包装器：核查完成后增量写入结果 + 问题"""
    results = await verify_sentence(client, model, fact, semaphore, progress, doc_context)
    await claim_writer.append([asdict(r) for r in results])
    # 问题数据也增量写入
    issues = [r for r in results if r.verdict in ("incorrect", "not_found")]
    if issues:
        await issues_writer.append([asdict(r) for r in issues])
    return results


# ============================================================
# 主流程
# ============================================================

async def run_fact_check(
    file_path: str,
    output_dir: Optional[str] = None,
    split_model: str = "gemini-2.0-flash",
    verify_model: str = "gemini-2.5-flash",
    split_concurrency: int = 5,
    verify_concurrency: int = 3,
    chapters: Optional[list[int]] = None,
    dry_run: bool = False,
    split_only: bool = False,
    resume: bool = False,
) -> dict:
    """
    两阶段事实核查主流程。

    Phase 1: Splitter (gemini-2.0-flash) → 拆句+分类+提取
    Phase 2: Verifier (gemini-2.5-flash+search) → 逐句核查

    支持增量写入（每完成一个任务立即更新 JSON）和断点续接（--resume）。
    """
    t0 = time.time()

    path = Path(file_path)
    if not path.exists():
        print(f"错误: 文件不存在 - {file_path}")
        sys.exit(1)

    if output_dir is None:
        output_dir = str(path.parent)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # --- 解析文档 ---
    content = path.read_text(encoding='utf-8')
    print(f"📄 文档: {path.name}")
    sections = parse_document(content)
    print(f"   章节: {len(sections)}")

    if chapters:
        sections = [
            s for s in sections
            if any(s.id_prefix.startswith(f"C{c}") for c in chapters)
        ]
        print(f"   过滤后: {len(sections)} 个章节")

    total_p = sum(len(s.paragraphs) for s in sections)
    print(f"   段落: {total_p}")

    if dry_run:
        print(f"\n📋 文档结构:")
        for s in sections:
            indent = "  " * (s.level - 1)
            print(f"{indent}[{s.id_prefix}] {'#'*s.level} {s.title}  ({len(s.paragraphs)} 段)")
            for i, p in enumerate(s.paragraphs, 1):
                print(f"{indent}  P{i}: {p[:60]}...")
        return {"dry_run": True}

    client = genai.Client()

    sentences_path = out / f"{path.stem}_sentences.json"
    factcheck_path = out / f"{path.stem}_factcheck.json"
    issues_path = out / f"{path.stem}_issues.json"

    # ========================================
    # Phase 1: Splitter Agent
    # ========================================

    # 收集需要处理的段落
    para_tasks = []
    for section in sections:
        for p_idx, paragraph in enumerate(section.paragraphs, 1):
            if len(paragraph.strip()) < 20:
                continue
            para_tasks.append((section, paragraph, p_idx))

    # 初始化增量写入器
    sentences_meta = {
        "document": path.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "split_model": split_model,
        "phase1_completed": False,
        "total_paragraphs": len(para_tasks),
    }
    sentences_writer = IncrementalWriter(sentences_path, sentences_meta, items_key="sentences")

    # 断点续接：检查 Phase 1 是否已完成
    skip_phase1 = False
    completed_prefixes: set[str] = set()
    if resume and sentences_path.exists():
        sentences_writer.load_existing()
        completed_prefixes = sentences_writer.get_completed_prefixes()
        try:
            data = json.loads(sentences_path.read_text(encoding='utf-8'))
            if data.get("phase1_completed"):
                skip_phase1 = True
                print(f"\n⏩ Phase 1 已完成（{len(sentences_writer.items)} 句），跳过")
        except (json.JSONDecodeError, KeyError):
            pass
        if not skip_phase1 and completed_prefixes:
            print(f"\n🔄 Resume: Phase 1 已完成 {len(completed_prefixes)}/{len(para_tasks)} 个段落")

    if not skip_phase1:
        phase1_failures = 0  # 初始化，防止 remaining_tasks 为空时未定义

        # 过滤已完成的段落
        remaining_tasks = [
            (sec, para, pidx)
            for sec, para, pidx in para_tasks
            if f"{sec.id_prefix}.P{pidx}" not in completed_prefixes
        ]

        if remaining_tasks:
            print(f"\n{'='*60}")
            print(f"Phase 1: 拆句+分类 (模型={split_model}, 并发={split_concurrency})")
            if completed_prefixes:
                print(f"  续接: {len(remaining_tasks)} 个段落待处理（已跳过 {len(completed_prefixes)} 个）")
            print(f"{'='*60}")

            split_sem = asyncio.Semaphore(split_concurrency)
            split_progress = Progress(len(remaining_tasks), "拆句")

            split_coros = [
                _split_and_write(
                    client, split_model, sec, para, pidx,
                    split_sem, split_progress, sentences_writer,
                )
                for sec, para, pidx in remaining_tasks
            ]
            split_results = await asyncio.gather(*split_coros, return_exceptions=True)

            phase1_failures = 0
            for res in split_results:
                if isinstance(res, Exception):
                    phase1_failures += 1
                    print(f"  [异常] {res}")

        # 标记 Phase 1 完成（仅在零失败时才标记，否则 resume 时会重试失败的段落）
        all_s = sentences_writer.items
        factual_n = sum(1 for s in all_s if s.get("type") == "factual" and s.get("claims"))
        subjective_n = sum(1 for s in all_s if s.get("type") == "subjective")
        claims_n = sum(len(s.get("claims", [])) for s in all_s if s.get("type") == "factual")

        sentences_writer.metadata.update({
            "phase1_completed": phase1_failures == 0,
            "statistics": {
                "total_sentences": len(all_s),
                "factual": factual_n,
                "subjective": subjective_n,
                "total_claims": claims_n,
            },
        })
        sentences_writer._flush()

        t1 = time.time()
        print(f"\n📊 Phase 1 结果 ({_format_elapsed(t1 - t0)}):")
        print(f"  总句子: {len(all_s)}")
        print(f"  事实句: {factual_n} ({claims_n} 个声明)")
        print(f"  主观句: {subjective_n} (跳过)")
        print(f"  保存: {sentences_path}")

    if split_only:
        elapsed = time.time() - t0
        print(f"\n(--split-only 模式，Phase 2 跳过)")
        print(f"⏱️  总耗时: {_format_elapsed(elapsed)}")
        return {"split_only": True}

    # ========================================
    # Phase 2: Verifier Agent
    # ========================================

    # 生成文档核查背景摘要（避免搜索时混淆国家/主题）
    print(f"\n🔍 生成文档核查背景摘要...")
    doc_context = await generate_doc_context(client, verify_model, content)
    if doc_context:
        print(f"  摘要: {doc_context[:120]}...")

    # 从 writer 中重建事实句对象（兼容 resume 加载的数据）
    _fields = {f for f in SentenceFact.__dataclass_fields__}
    factual_sentences = [
        SentenceFact(**{k: v for k, v in s.items() if k in _fields})
        for s in sentences_writer.items
        if s.get("type") == "factual" and s.get("claims")
    ]
    total_claims = sum(len(f.claims) for f in factual_sentences)

    # 初始化核查增量写入器
    factcheck_meta = {
        "document": path.name,
        "file_path": str(path.resolve()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models": {"split": split_model, "verify": verify_model},
        "phase2_completed": False,
        "total_factual_sentences": len(factual_sentences),
    }
    claim_writer = IncrementalWriter(factcheck_path, factcheck_meta, items_key="results")

    issues_meta = {
        "document": path.name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    issues_writer = IncrementalWriter(issues_path, issues_meta, items_key="issues")

    # 断点续接：加载已核查的句子
    completed_sentence_ids: set[str] = set()
    if resume and factcheck_path.exists():
        claim_writer.load_existing()
        # 提取已完成的句子级 ID（C2.S1.P1.T1.K1 → C2.S1.P1.T1）
        for item in claim_writer.items:
            sid = item.get("id", "")
            dot_k_pos = sid.rfind('.K')
            if dot_k_pos > 0:
                sentence_id = sid[:dot_k_pos]
                # 验证格式（至少包含 C 和 T）
                if 'C' in sentence_id and '.T' in sentence_id:
                    completed_sentence_ids.add(sentence_id)
        if completed_sentence_ids:
            print(f"\n🔄 Resume: Phase 2 已核查 {len(completed_sentence_ids)}/{len(factual_sentences)} 句")
        # 同时加载已有 issues
        if issues_path.exists():
            issues_writer.load_existing()

    remaining_facts = [f for f in factual_sentences if f.id not in completed_sentence_ids]
    remaining_claims = sum(len(f.claims) for f in remaining_facts)

    if remaining_facts:
        print(f"\n{'='*60}")
        print(f"Phase 2: 逐句核查 (模型={verify_model}, 并发={verify_concurrency})")
        if completed_sentence_ids:
            print(f"  续接: {len(remaining_facts)} 句待核查（已跳过 {len(completed_sentence_ids)} 句）")
        else:
            print(f"  待核查: {len(remaining_facts)} 句, {remaining_claims} 个声明")
        print(f"{'='*60}")

        verify_sem = asyncio.Semaphore(verify_concurrency)
        verify_progress = Progress(len(remaining_facts), "核查")

        verify_coros = [
            _verify_and_write(
                client, verify_model, fact, verify_sem, verify_progress,
                claim_writer, issues_writer, doc_context,
            )
            for fact in remaining_facts
        ]
        verify_results = await asyncio.gather(*verify_coros, return_exceptions=True)

        phase2_failures = 0
        for res in verify_results:
            if isinstance(res, Exception):
                phase2_failures += 1
                print(f"  [异常] {res}")
    else:
        phase2_failures = 0
        print(f"\n⏩ Phase 2 已全部完成，无需核查")

    # 最终统计 + 标记完成
    all_c = claim_writer.items
    verified_n = sum(1 for c in all_c if c.get("verdict") == "verified")
    incorrect_n = sum(1 for c in all_c if c.get("verdict") == "incorrect")
    not_found_n = sum(1 for c in all_c if c.get("verdict") == "not_found")

    all_s = sentences_writer.items
    claim_writer.metadata.update({
        "phase2_completed": phase2_failures == 0,
        "statistics": {
            "total_sentences": len(all_s),
            "factual_sentences": len(factual_sentences),
            "subjective_sentences": len(all_s) - len(factual_sentences),
            "total_claims": len(all_c),
            "verified": verified_n,
            "incorrect": incorrect_n,
            "not_found": not_found_n,
        },
    })
    claim_writer._flush()

    # 更新 issues 写入器的统计（始终写入，清除可能残留的旧文件）
    issues_writer.metadata.update({
        "total_issues": len(issues_writer.items),
        "incorrect_count": sum(1 for i in issues_writer.items if i.get("verdict") == "incorrect"),
        "not_found_count": sum(1 for i in issues_writer.items if i.get("verdict") == "not_found"),
    })
    issues_writer._flush()

    elapsed = time.time() - t0

    # 打印最终摘要
    print(f"\n{'='*60}")
    print(f"  📋 最终摘要")
    print(f"  {'─'*40}")
    print(f"  总句子:      {len(all_s)}")
    print(f"  事实句:      {len(factual_sentences)}")
    print(f"  主观句(跳过): {len(all_s) - len(factual_sentences)}")
    print(f"  {'─'*40}")
    print(f"  核查声明:    {len(all_c)}")
    print(f"  ✅ 数据无误: {verified_n}")
    print(f"  ❌ 数据有误: {incorrect_n}")
    print(f"  ❓ 无法核实: {not_found_n}")
    print(f"  {'─'*40}")
    print(f"  ⏱️  总耗时: {_format_elapsed(elapsed)}")
    print(f"  📄 结果: {factcheck_path}")
    if issues_writer.items:
        print(f"  ⚠️  问题: {issues_path}")
    print(f"{'='*60}")

    return claim_writer.metadata


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="两阶段事实核查: 拆句(2.0-flash) → 核查(2.5-flash+search)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python fact_checker.py article.md\n"
            "  python fact_checker.py article.md --chapters 2,3 --verify-concurrency 5\n"
            "  python fact_checker.py article.md --split-only\n"
            "  python fact_checker.py article.md --dry-run\n"
            "  python fact_checker.py article.md --resume    # 断点续接\n"
        ),
    )
    parser.add_argument("file", help="Markdown 文件路径")
    parser.add_argument("-o", "--output", help="输出目录")
    parser.add_argument("--split-model", default="gemini-2.0-flash",
                        help="Phase1 拆句模型（默认 gemini-2.0-flash）")
    parser.add_argument("--verify-model", default="gemini-2.5-flash",
                        help="Phase2 核查模型（默认 gemini-2.5-flash）")
    parser.add_argument("--split-concurrency", type=int, default=5,
                        help="Phase1 并发数（默认 5）")
    parser.add_argument("--verify-concurrency", type=int, default=3,
                        help="Phase2 并发数（默认 3）")
    parser.add_argument("--chapters", help="指定章节（逗号分隔，如 2,3,4）")
    parser.add_argument("--dry-run", action="store_true", help="仅解析文档结构")
    parser.add_argument("--split-only", action="store_true",
                        help="仅执行 Phase1（拆句分类），不核查")
    parser.add_argument("--resume", action="store_true",
                        help="断点续接：跳过已完成的任务，继续处理剩余部分")

    args = parser.parse_args()

    chapters = None
    if args.chapters:
        chapters = [int(c.strip()) for c in args.chapters.split(',')]

    asyncio.run(run_fact_check(
        file_path=args.file,
        output_dir=args.output,
        split_model=args.split_model,
        verify_model=args.verify_model,
        split_concurrency=args.split_concurrency,
        verify_concurrency=args.verify_concurrency,
        chapters=chapters,
        dry_run=args.dry_run,
        split_only=args.split_only,
        resume=args.resume,
    ))


if __name__ == "__main__":
    main()
