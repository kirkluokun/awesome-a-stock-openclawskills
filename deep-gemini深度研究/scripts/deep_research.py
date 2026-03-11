#!/usr/bin/env python3
"""
Gemini Deep Research Agent — 深度研究工具

封装 Gemini Interactions API 的深度研究代理，支持：
  - 输入题目 + 可选提纲 markdown 控制报告结构
  - 指定本地目录让 Agent 访问自有数据（file_search）
  - 多模态输入（图片、PDF 等）
  - 流式输出 + 断线自动重连
  - 研究完成后追问
  - 独立 CLI + Claude Code Skill 双模式

用法:
    python deep_research.py "研究主题"
    python deep_research.py "研究主题" --outline outline.md
    python deep_research.py "研究主题" --data-dir ./参考资料/
    python deep_research.py "分析图表" --attach chart.png --attach report.pdf
    python deep_research.py --followup session.json "请展开第二点"
    python deep_research.py "研究主题" -o ./output/

环境变量:
    GEMINI_API_KEY 或 GOOGLE_API_KEY
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ============================================================
# .env 自动加载
# ============================================================
try:
    from dotenv import load_dotenv

    _script_dir = Path(__file__).resolve().parent
    for _env in [
        _script_dir.parent.parent / ".env",   # AItool 根目录
        _script_dir.parent / ".env",           # skill 根目录
        _script_dir / ".env",                  # scripts 目录
        Path.cwd() / ".env",                   # 工作目录
    ]:
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass

from google import genai

# ============================================================
# 常量 & 配置
# ============================================================

# 深度研究专用 Agent 名称
AGENT_NAME = "deep-research-pro-preview-12-2025"
# 追问使用的模型（非 Agent，走普通 interactions）
FOLLOWUP_MODEL = "gemini-3-pro-preview"

# file_search 支持的文件类型（MIME → 扩展名映射）
SUPPORTED_STORE_EXTENSIONS: set[str] = {
    ".pdf", ".md", ".txt", ".csv", ".json",
    ".html", ".htm", ".xml", ".docx", ".xlsx",
    ".pptx", ".rtf", ".tsv",
}

# 多模态附件支持的类型
SUPPORTED_ATTACH_EXTENSIONS: dict[str, str] = {
    # 图片
    ".png": "image", ".jpg": "image", ".jpeg": "image",
    ".gif": "image", ".webp": "image", ".heic": "image",
    # 文档
    ".pdf": "document",
    # 视频
    ".mp4": "video", ".mov": "video", ".avi": "video",
    ".mkv": "video", ".webm": "video",
}

# 断线重连最大次数
MAX_RECONNECT_ATTEMPTS = 5
# 重连退避基础秒数
RECONNECT_BASE_DELAY = 3
# 轮询间隔秒数
POLL_INTERVAL = 10
# 附件上传等待超时（秒）
ATTACH_UPLOAD_TIMEOUT = 120
# 单文件大小限制（50MB）
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024


# ============================================================
# FileSearchStore 管理
# ============================================================

def create_store(client: genai.Client, display_name: str) -> str:
    """
    创建 FileSearchStore，返回 store 的全限定名称。

    参数:
        client: genai.Client 实例
        display_name: store 的显示名称

    返回:
        store_name: 如 "fileSearchStores/xxx"
    """
    store = client.file_search_stores.create(
        config={"display_name": display_name}
    )
    print(f"[Store] 已创建: {store.name}")
    return store.name


def upload_directory(client: genai.Client, store_name: str, dir_path: Path) -> int:
    """
    递归扫描目录，上传所有支持的文件到 FileSearchStore。

    参数:
        client: genai.Client 实例
        store_name: FileSearchStore 全限定名
        dir_path: 本地数据目录

    返回:
        上传成功的文件数量
    """
    uploaded = 0
    # 收集所有待上传文件（跳过隐藏文件、超大文件）
    files_to_upload: list[Path] = []
    for f in sorted(dir_path.rglob("*")):
        # 跳过隐藏文件和隐藏目录下的文件
        if any(part.startswith(".") for part in f.relative_to(dir_path).parts):
            continue
        if not f.is_file():
            continue
        if f.suffix.lower() not in SUPPORTED_STORE_EXTENSIONS:
            continue
        # 文件大小限制
        if f.stat().st_size > MAX_FILE_SIZE_BYTES:
            print(f"  跳过（超过 {MAX_FILE_SIZE_BYTES // 1024 // 1024}MB 限制）: {f.name}")
            continue
        files_to_upload.append(f)

    if not files_to_upload:
        print(f"[Store] 警告: 目录 {dir_path} 中没有找到支持的文件")
        return 0

    print(f"[Store] 找到 {len(files_to_upload)} 个文件，开始上传...")

    # 逐个上传并等待处理完成
    pending_ops: list[tuple[str, Any]] = []
    for f in files_to_upload:
        try:
            op = client.file_search_stores.upload_to_file_search_store(
                file=str(f),
                file_search_store_name=store_name,
                config={"display_name": f.name},
            )
            pending_ops.append((f.name, op))
            print(f"  上传中: {f.name}")
        except Exception as e:
            print(f"  上传失败: {f.name} — {e}")

    # 等待所有上传操作完成，检查是否真正成功
    for fname, op in pending_ops:
        try:
            while not op.done:
                time.sleep(2)
                op = client.operations.get(op)
            # 检查 LRO 是否有错误
            if hasattr(op, "error") and op.error:
                print(f"  处理失败: {fname} — {op.error}")
            else:
                uploaded += 1
        except Exception as e:
            print(f"  处理失败: {fname} — {e}")

    print(f"[Store] 上传完成: {uploaded}/{len(files_to_upload)} 个文件")
    return uploaded


def cleanup_store(client: genai.Client, store_name: str) -> None:
    """
    删除 FileSearchStore，清理资源。

    参数:
        client: genai.Client 实例
        store_name: FileSearchStore 全限定名
    """
    try:
        # force=True 确保即使 store 中有文件也能删除
        client.file_search_stores.delete(name=store_name, force=True)
        print(f"[Store] 已清理: {store_name}")
    except Exception as e:
        print(f"[Store] 清理失败（可手动删除）: {e}")


# ============================================================
# Prompt 构建
# ============================================================

def build_research_prompt(
    topic: str,
    outline_path: Path | None = None,
) -> str:
    """
    构建研究 prompt，可选注入提纲作为结构化指令。

    参数:
        topic: 研究主题
        outline_path: 提纲 markdown 文件路径

    返回:
        完整的 prompt 字符串
    """
    prompt = f"Research topic: {topic}\n\n"

    if outline_path:
        outline_text = outline_path.read_text(encoding="utf-8").strip()
        prompt += (
            "Format the output following this outline structure exactly:\n\n"
            f"{outline_text}\n\n"
            "For each section, provide thorough research with cited sources. "
            "If data is unavailable, explicitly state so.\n"
        )

    return prompt


def build_multimodal_input(
    prompt: str,
    attachments: list[Path],
    client: genai.Client,
) -> tuple[str | list[dict[str, str]], list[str]]:
    """
    构建多模态输入。无附件时返回纯文本，有附件时返回 input 数组。

    参数:
        prompt: 文本提示
        attachments: 附件文件路径列表
        client: genai.Client 实例（用于上传文件）

    返回:
        (prompt_input, uploaded_file_names) 元组
        - prompt_input: 纯字符串或 input parts 列表
        - uploaded_file_names: 已上传到 Files API 的文件名列表（用于清理）
    """
    if not attachments:
        return prompt, []

    parts: list[dict[str, str]] = [{"type": "text", "text": prompt}]
    # 追踪上传的文件名，用于后续清理
    _uploaded_file_names: list[str] = []

    for attach in attachments:
        ext = attach.suffix.lower()
        attach_type = SUPPORTED_ATTACH_EXTENSIONS.get(ext)

        if not attach_type:
            print(f"[附件] 跳过不支持的类型: {attach.name} ({ext})")
            continue

        # 文件大小预检（与 data_dir 上传保持一致）
        file_size = attach.stat().st_size
        if file_size > MAX_FILE_SIZE_BYTES:
            print(f"[附件] 跳过超大文件: {attach.name} ({file_size / 1024 / 1024:.1f}MB > {MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f}MB)")
            continue

        # 上传到 Gemini Files API 获取 URI
        print(f"[附件] 上传: {attach.name}")
        try:
            uploaded_file = client.files.upload(file=str(attach))
            # 等待文件处理完成（带超时和失败检查）
            upload_deadline = time.time() + ATTACH_UPLOAD_TIMEOUT
            while (
                uploaded_file.state
                and uploaded_file.state.name == "PROCESSING"
                and time.time() < upload_deadline
            ):
                time.sleep(2)
                uploaded_file = client.files.get(name=uploaded_file.name)

            # 检查最终状态
            if uploaded_file.state and uploaded_file.state.name == "FAILED":
                print(f"[附件] 处理失败: {attach.name}")
                continue
            if not uploaded_file.uri:
                print(f"[附件] 无法获取 URI: {attach.name}")
                continue

            parts.append({"type": attach_type, "uri": uploaded_file.uri})
            _uploaded_file_names.append(uploaded_file.name)
            print(f"[附件] 就绪: {attach.name}")
        except Exception as e:
            print(f"[附件] 上传失败: {attach.name} — {e}")

    # 只有文本部分则退回纯文本
    if len(parts) == 1:
        return prompt, _uploaded_file_names

    return parts, _uploaded_file_names


# ============================================================
# 研究执行（流式 + 断线重连）
# ============================================================

def _process_stream(event_stream, state: dict) -> str:
    """
    处理事件流，实时显示思考摘要和正文内容。

    参数:
        event_stream: interactions API 返回的流式迭代器
        state: 共享状态字典，包含 interaction_id、last_event_id、is_complete

    返回:
        本次流中收到的正文文本片段拼接
    """
    text_buffer: list[str] = []

    for event in event_stream:
        # 捕获 interaction ID
        if event.event_type == "interaction.start":
            state["interaction_id"] = event.interaction.id
            print(f"\n[研究] 已启动: {state['interaction_id']}")

        # 追踪 event ID（用于断线重连）
        if event.event_id:
            state["last_event_id"] = event.event_id

        # 处理内容增量（防御性访问 delta 属性）
        if event.event_type == "content.delta":
            delta = getattr(event, "delta", None)
            if delta is None:
                continue
            delta_type = getattr(delta, "type", None)

            if delta_type == "text":
                text = getattr(delta, "text", "") or ""
                if text:
                    print(text, end="", flush=True)
                    text_buffer.append(text)
            elif delta_type == "thought_summary":
                content = getattr(delta, "content", None)
                thought_text = getattr(content, "text", "") if content else ""
                if thought_text:
                    print(f"\n[思考] {thought_text}", flush=True)

        # 完成
        elif event.event_type == "interaction.complete":
            state["is_complete"] = True

        # 错误事件：仅记录，不阻止重连（让重连循环决定是否继续）
        elif event.event_type == "error":
            print(f"\n[错误] 研究过程出错", flush=True)

    return "".join(text_buffer)


def run_research(
    client: genai.Client,
    prompt_input: str | list[dict[str, str]],
    tools: list[dict] | None = None,
    timeout_minutes: int = 30,
    use_stream: bool = True,
) -> tuple[str, str]:
    """
    执行深度研究任务，支持流式输出和断线重连。

    参数:
        client: genai.Client 实例
        prompt_input: 纯文本或多模态 input
        tools: 附加工具列表（如 file_search）
        timeout_minutes: 最大等待时间（分钟）
        use_stream: 是否使用流式传输

    返回:
        (interaction_id, report_text) 元组
    """
    deadline = time.time() + timeout_minutes * 60

    if use_stream:
        return _run_stream(client, prompt_input, tools, deadline)
    else:
        return _run_poll(client, prompt_input, tools, deadline)


def _run_stream(
    client: genai.Client,
    prompt_input: str | list[dict[str, str]],
    tools: list[dict] | None,
    deadline: float,
) -> tuple[str, str]:
    """流式执行 + 断线重连"""
    state: dict[str, Any] = {
        "interaction_id": None,
        "last_event_id": None,
        "is_complete": False,
    }
    all_text: list[str] = []

    # 构建请求参数
    create_kwargs: dict[str, Any] = {
        "input": prompt_input,
        "agent": AGENT_NAME,
        "background": True,
        "stream": True,
        "agent_config": {
            "type": "deep-research",
            "thinking_summaries": "auto",
        },
    }
    if tools:
        create_kwargs["tools"] = tools

    # 第一次连接
    print("[研究] 启动深度研究...")
    try:
        stream = client.interactions.create(**create_kwargs)
        text = _process_stream(stream, state)
        all_text.append(text)
    except Exception as e:
        print(f"\n[连接] 初始连接中断: {e}")

    # 断线重连循环
    reconnect_count = 0
    while not state["is_complete"] and state["interaction_id"]:
        if time.time() > deadline:
            print("\n[超时] 已达到最大等待时间")
            break

        reconnect_count += 1
        if reconnect_count > MAX_RECONNECT_ATTEMPTS:
            print(f"\n[连接] 已达到最大重连次数 ({MAX_RECONNECT_ATTEMPTS})")
            break

        delay = RECONNECT_BASE_DELAY * reconnect_count
        print(f"\n[连接] 第 {reconnect_count} 次重连，等待 {delay}s...")
        time.sleep(delay)

        try:
            get_kwargs: dict[str, Any] = {
                "id": state["interaction_id"],
                "stream": True,
            }
            if state["last_event_id"]:
                get_kwargs["last_event_id"] = state["last_event_id"]

            resume_stream = client.interactions.get(**get_kwargs)
            text = _process_stream(resume_stream, state)
            all_text.append(text)
            # 成功恢复，重置计数
            reconnect_count = 0
        except Exception as e:
            print(f"[连接] 重连失败: {e}")

    # 尝试从 API 获取完整报告（流式可能不完整或中断）
    report_text = "".join(all_text)
    if state["interaction_id"]:
        canonical = _fetch_final_report(client, state["interaction_id"])
        # 优先使用 API 返回的完整报告（比流式拼接更可靠）
        if canonical.strip():
            report_text = canonical

    return state["interaction_id"] or "", report_text


def _run_poll(
    client: genai.Client,
    prompt_input: str | list[dict[str, str]],
    tools: list[dict] | None,
    deadline: float,
) -> tuple[str, str]:
    """轮询模式执行"""
    create_kwargs: dict[str, Any] = {
        "input": prompt_input,
        "agent": AGENT_NAME,
        "background": True,
    }
    if tools:
        create_kwargs["tools"] = tools

    print("[研究] 启动深度研究（轮询模式）...")
    interaction = client.interactions.create(**create_kwargs)
    interaction_id = interaction.id
    print(f"[研究] ID: {interaction_id}")

    while time.time() < deadline:
        interaction = client.interactions.get(interaction_id)

        if interaction.status == "completed":
            print("\n[研究] 完成!")
            report_text = _extract_text_from_outputs(interaction.outputs)
            return interaction_id, report_text

        elif interaction.status == "failed":
            error_msg = getattr(interaction, "error", "未知错误")
            print(f"\n[错误] 研究失败: {error_msg}")
            return interaction_id, ""

        # 显示进度
        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL)

    print("\n[超时] 已达到最大等待时间")
    return interaction_id, ""


def _extract_text_from_outputs(outputs: list | None) -> str:
    """从 interaction outputs 中安全提取文本内容"""
    if not outputs:
        return ""
    # 从最后一个 output 开始往前找，取第一个有文本的
    for output in reversed(outputs):
        text = getattr(output, "text", None)
        if text:
            return text
    return ""


def _fetch_final_report(client: genai.Client, interaction_id: str) -> str:
    """从已完成的 interaction 获取最终报告文本"""
    try:
        interaction = client.interactions.get(interaction_id)
        return _extract_text_from_outputs(interaction.outputs)
    except Exception as e:
        print(f"[警告] 获取最终报告失败: {e}")
    return ""


# ============================================================
# 追问处理
# ============================================================

def load_session(session_path: Path) -> dict:
    """
    加载会话文件。

    参数:
        session_path: session.json 文件路径

    返回:
        会话数据字典
    """
    with open(session_path, "r", encoding="utf-8") as f:
        return json.load(f)


def followup_question(
    client: genai.Client,
    interaction_id: str,
    question: str,
) -> str:
    """
    基于已完成的研究进行追问。

    参数:
        client: genai.Client 实例
        interaction_id: 原始研究的 interaction ID
        question: 追问问题

    返回:
        追问回复文本
    """
    print(f"[追问] 基于 {interaction_id}...")
    interaction = client.interactions.create(
        input=question,
        model=FOLLOWUP_MODEL,
        previous_interaction_id=interaction_id,
    )

    return _extract_text_from_outputs(interaction.outputs)


# ============================================================
# 输出 & 会话持久化
# ============================================================

def save_report(text: str, output_dir: Path, topic: str) -> Path:
    """
    保存研究报告为 markdown 文件。

    参数:
        text: 报告正文
        output_dir: 输出目录
        topic: 研究主题（用于文件名）

    返回:
        保存的文件路径
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    # 清理文件名：取前30字符，移除特殊字符
    safe_name = "".join(
        c if c.isalnum() or c in (" ", "-", "_", ".", "（", "）") else "_"
        for c in topic[:30]
    ).strip()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{safe_name}_{timestamp}_report.md"
    filepath = output_dir / filename

    filepath.write_text(text, encoding="utf-8")
    print(f"\n[输出] 报告已保存: {filepath}")
    return filepath


def save_session(
    interaction_id: str,
    topic: str,
    output_dir: Path,
    report_path: Path,
    store_name: str | None = None,
) -> Path:
    """
    保存会话文件，支持后续追问。

    参数:
        interaction_id: 研究 interaction ID
        topic: 研究主题
        output_dir: 输出目录
        report_path: 报告文件路径
        store_name: FileSearchStore 名称（可选）

    返回:
        session.json 文件路径
    """
    session_data = {
        "interaction_id": interaction_id,
        "store_name": store_name,
        "topic": topic,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "report_file": str(report_path),
    }

    session_path = report_path.with_suffix(".session.json")
    with open(session_path, "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)

    print(f"[输出] 会话已保存: {session_path}")
    print(f"       追问命令: python {__file__} --followup {session_path} \"你的问题\"")
    return session_path


# ============================================================
# CLI 入口
# ============================================================

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Gemini Deep Research Agent — 深度研究工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            '  %(prog)s "量子计算的商业应用前景"\n'
            '  %(prog)s "量子计算" --outline outline.md\n'
            '  %(prog)s "对比分析" -l outline.md -d ./参考资料/\n'
            '  %(prog)s "分析图表" --attach chart.png --attach report.pdf\n'
            '  %(prog)s --followup session.json "请展开第二点"\n'
        ),
    )

    parser.add_argument(
        "topic",
        nargs="?",
        help="研究主题（正常模式必填，追问模式为追问问题）",
    )

    parser.add_argument(
        "-l", "--outline",
        type=Path,
        help="提纲 markdown 文件路径，控制报告结构",
    )

    parser.add_argument(
        "-d", "--data-dir",
        type=Path,
        help="本地数据目录路径（自动创建 FileSearchStore）",
    )

    parser.add_argument(
        "-a", "--attach",
        type=Path,
        action="append",
        default=[],
        help="附加文件（图片/PDF/视频），可多次使用",
    )

    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=Path.cwd(),
        help="输出目录（默认当前目录）",
    )

    parser.add_argument(
        "-f", "--followup",
        type=Path,
        help="会话文件路径（追问模式）",
    )

    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=30,
        help="最大等待时间（分钟，默认 30）",
    )

    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="禁用流式传输，改用轮询模式",
    )

    parser.add_argument(
        "-b", "--batch",
        type=Path,
        help="批量任务 JSON 文件路径（串行执行多个研究任务）",
    )

    args = parser.parse_args(argv)

    # 验证参数：batch 模式不需要 topic
    if not args.batch and not args.followup and not args.topic:
        parser.error("必须提供研究主题、--batch 批量文件，或 --followup 进行追问")

    if args.followup and not args.topic:
        parser.error("追问模式需要提供问题内容作为 topic 参数")

    if args.followup and not args.followup.exists():
        parser.error(f"会话文件不存在: {args.followup}")

    if args.batch and not args.batch.exists():
        parser.error(f"批量任务文件不存在: {args.batch}")

    if args.outline and not args.outline.exists():
        parser.error(f"提纲文件不存在: {args.outline}")

    if args.data_dir and not args.data_dir.is_dir():
        parser.error(f"数据目录不存在: {args.data_dir}")

    if args.timeout <= 0:
        parser.error(f"超时时间必须大于 0: {args.timeout}")

    for attach in args.attach:
        if not attach.exists():
            parser.error(f"附件不存在: {attach}")

    return args


def run_single_task(
    client: genai.Client,
    topic: str,
    output_dir: Path,
    outline_path: Path | None = None,
    data_dir: Path | None = None,
    attachments: list[Path] | None = None,
    timeout_minutes: int = 30,
    use_stream: bool = True,
) -> bool:
    """
    执行单个研究任务。从 main() 和 batch 模式共用。

    参数:
        client: genai.Client 实例
        topic: 研究主题
        output_dir: 输出目录
        outline_path: 提纲文件路径
        data_dir: 数据目录路径
        attachments: 附件列表
        timeout_minutes: 超时分钟数
        use_stream: 是否流式传输

    返回:
        是否成功获取到报告
    """
    store_name: str | None = None
    uploaded_file_names: list[str] = []
    try:
        # 1. 构建 prompt
        prompt = build_research_prompt(
            topic=topic,
            outline_path=outline_path,
        )

        # 2. 处理多模态附件
        prompt_input, uploaded_file_names = build_multimodal_input(
            prompt=prompt,
            attachments=attachments or [],
            client=client,
        )

        # 3. 准备工具（file_search）
        tools: list[dict] | None = None
        if data_dir:
            store_display = f"dr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            store_name = create_store(client, store_display)
            file_count = upload_directory(client, store_name, data_dir)

            if file_count > 0:
                tools = [
                    {
                        "type": "file_search",
                        "file_search_store_names": [store_name],
                    }
                ]
            else:
                print("[警告] 没有文件被上传，将不使用 file_search")

        # 4. 执行研究
        interaction_id, report_text = run_research(
            client=client,
            prompt_input=prompt_input,
            tools=tools,
            timeout_minutes=timeout_minutes,
            use_stream=use_stream,
        )

        # 5. 保存结果
        if report_text.strip():
            report_path = save_report(
                text=report_text,
                output_dir=output_dir,
                topic=topic,
            )
            save_session(
                interaction_id=interaction_id,
                topic=topic,
                output_dir=output_dir,
                report_path=report_path,
                store_name=store_name,
            )
            return True
        else:
            print("[警告] 未获取到研究报告内容")
            if interaction_id:
                print(f"       Interaction ID: {interaction_id}")
            return False

    finally:
        # 清理 FileSearchStore
        if store_name:
            cleanup_store(client, store_name)
        # 清理 Files API 上传的附件文件
        for fname in uploaded_file_names:
            try:
                client.files.delete(name=fname)
            except Exception:
                pass


# ============================================================
# 批量执行
# ============================================================

def run_batch(
    client: genai.Client,
    batch_path: Path,
    output_dir: Path,
    timeout_minutes: int = 30,
    use_stream: bool = True,
) -> int:
    """
    串行执行批量研究任务。

    批量文件格式 (JSON):
        [
          {"topic": "研究主题1", "outline": "outline.md", "data_dir": "./data/"},
          {"topic": "研究主题2"},
          {"topic": "研究主题3", "attach": ["img.png", "doc.pdf"]}
        ]

    每个任务必须有 topic 字段，其他字段可选。

    参数:
        client: genai.Client 实例
        batch_path: 批量任务 JSON 文件路径
        output_dir: 输出根目录
        timeout_minutes: 每个任务的超时分钟数
        use_stream: 是否流式传输

    返回:
        失败任务数量
    """
    # 加载批量任务
    with open(batch_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)

    if not isinstance(tasks, list) or not tasks:
        print("[批量] 错误: 文件内容必须是非空 JSON 数组")
        return 1

    total = len(tasks)
    # 路径解析基于批量文件所在目录
    batch_base = batch_path.resolve().parent
    results: list[dict[str, Any]] = []

    print(f"[批量] 共 {total} 个任务，串行执行")
    print(f"{'='*60}")

    for idx, task in enumerate(tasks, 1):
        # 校验条目类型，非 dict 跳过继续
        if not isinstance(task, dict):
            print(f"\n[批量 {idx}/{total}] 跳过: 条目不是字典，实际类型={type(task).__name__}")
            results.append({"index": idx, "topic": f"(非法:{type(task).__name__})", "status": "跳过"})
            continue

        topic = task.get("topic", "").strip()
        if not topic:
            print(f"\n[批量 {idx}/{total}] 跳过: 缺少 topic 字段")
            results.append({"index": idx, "topic": "(空)", "status": "跳过"})
            continue

        print(f"\n[批量 {idx}/{total}] {topic}")
        print(f"{'-'*60}")

        # 解析任务专属参数
        outline_path: Path | None = None
        if task.get("outline"):
            outline_path = batch_base / task["outline"]
            if not outline_path.exists():
                print(f"  警告: 提纲文件不存在 {outline_path}，忽略")
                outline_path = None

        data_dir: Path | None = None
        if task.get("data_dir"):
            data_dir = batch_base / task["data_dir"]
            if not data_dir.is_dir():
                print(f"  警告: 数据目录不存在 {data_dir}，忽略")
                data_dir = None

        attachments: list[Path] = []
        for a in task.get("attach", []):
            p = batch_base / a
            if p.exists():
                attachments.append(p)
            else:
                print(f"  警告: 附件不存在 {p}，忽略")

        # 每个任务输出到独立子目录
        safe_idx = f"{idx:02d}"
        safe_topic = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_"
            for c in topic[:20]
        ).strip()
        task_output = output_dir / f"{safe_idx}_{safe_topic}"

        start_time = time.time()
        try:
            success = run_single_task(
                client=client,
                topic=topic,
                output_dir=task_output,
                outline_path=outline_path,
                data_dir=data_dir,
                attachments=attachments,
                timeout_minutes=timeout_minutes,
                use_stream=use_stream,
            )
            elapsed = time.time() - start_time
            status = "成功" if success else "无结果"
            results.append({
                "index": idx, "topic": topic,
                "status": status, "elapsed": f"{elapsed:.0f}s",
            })
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n[批量 {idx}/{total}] 失败: {e}")
            results.append({
                "index": idx, "topic": topic,
                "status": f"失败: {e}", "elapsed": f"{elapsed:.0f}s",
            })

    # 打印汇总
    print(f"\n{'='*60}")
    print(f"[批量] 执行完成 — 共 {total} 个任务")
    print(f"{'='*60}")
    succeeded = 0
    for r in results:
        mark = "+" if r["status"] == "成功" else "-"
        elapsed = r.get("elapsed", "")
        print(f"  [{mark}] {r['index']:2d}. {r['topic'][:30]}  {r['status']}  {elapsed}")
        if r["status"] == "成功":
            succeeded += 1
    print(f"\n  成功: {succeeded}/{total}")

    return total - succeeded


def main(argv: list[str] | None = None) -> int:
    """主入口"""
    args = parse_args(argv)

    # 初始化客户端
    client = genai.Client()

    # ---- 追问模式 ----
    if args.followup:
        session = load_session(args.followup)
        print(f"[追问] 加载会话: {session['topic']}")

        response = followup_question(
            client=client,
            interaction_id=session["interaction_id"],
            question=args.topic,
        )

        if response:
            print(f"\n{'='*60}\n")
            print(response)
            save_report(
                text=response,
                output_dir=args.output,
                topic=f"followup_{args.topic}",
            )
        else:
            print("[追问] 未获取到回复")
        return 0

    # ---- 批量模式 ----
    if args.batch:
        failed = run_batch(
            client=client,
            batch_path=args.batch,
            output_dir=args.output,
            timeout_minutes=args.timeout,
            use_stream=not args.no_stream,
        )
        return 1 if failed else 0

    # ---- 单任务模式 ----
    success = run_single_task(
        client=client,
        topic=args.topic,
        output_dir=args.output,
        outline_path=args.outline,
        data_dir=args.data_dir,
        attachments=args.attach,
        timeout_minutes=args.timeout,
        use_stream=not args.no_stream,
    )
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[中断] 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n[致命错误] {e}")
        sys.exit(1)
