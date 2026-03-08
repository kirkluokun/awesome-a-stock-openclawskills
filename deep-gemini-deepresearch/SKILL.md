---
name: gemini-deepresearch
description: |
  统一深度研究工具。双模式：Deep(Gemini Deep Research API，带规划和验证) / Lite(Gemini CLI 快速草稿)。
  支持用户输入思路、素材、讨论框架，多轮对话确认提纲后执行。
  触发场景：深度研究/调研/文献综述/竞争分析/行业报告/快速调研
input-variables:
  mode:
    description: "研究模式: deep(深度) / lite(快速草稿)"
    default: "deep"
  output_dir:
    description: "输出目录"
    default: "当前目录"
  data_dir:
    description: "用户素材文件夹路径（可选，自动上传到 FileSearchStore）"
    default: ""
  attachments:
    description: "附件文件路径（可选，CLI 使用多次 --attach，每次一个文件）"
    default: ""
  gemini_model:
    description: "Gemini CLI 使用的模型（仅 Lite 模式）"
    default: "gemini-3-pro-preview"
  timeout:
    description: "Deep Research API 超时时间（分钟）"
    default: "30"
metadata: {"clawdbot":{"emoji":"🔬","requires":{"bins":["gemini"],"pip":["google-genai>=1.56.0"]}}}
---

# 🔬 Deep Research — 统一深度研究工具

双模式研究流水线：Claude 规划 → Gemini 执行 → Claude 验证。

## 依赖

| 依赖             | 用途      | 安装                                                                    |
| ---------------- | --------- | ----------------------------------------------------------------------- |
| `gemini` CLI     | Lite 模式 | 见 [github.com/google/gemini-cli](https://github.com/google/gemini-cli) |
| `google-genai`   | Deep 模式 | `pip install -r requirements.txt`                                       |
| `python-dotenv`  | .env 加载 | 可选，但推荐安装                                                        |
| `GEMINI_API_KEY` | API 认证  | 设置环境变量或写入 `.env`                                               |

## 模式选择

| 用户意图                       | 模式         | 执行方式                 | 耗时     | 输出质量          |
| ------------------------------ | ------------ | ------------------------ | -------- | ----------------- |
| "深度研究/全面分析/深度调研"   | **Deep**     | Gemini Deep Research API | 10-30min | 完整研究报告+引用 |
| "快速调研/初步看看/先出个草稿" | **Lite**     | Gemini CLI               | 3-8min   | 研究草稿          |
| "研究" (模糊)                  | 询问用户选择 | —                        | —        | —                 |

---

## Stage 1: 规划（Claude，两种模式共用）

### 触发后的第一步：理解需求

阅读 `references/research_methodology.md` 后，与用户进行多轮对话：

**1. 理解目标（1-2个问题）**
> "你的研究目标是什么？学习、投资决策、写报告、还是做方案？"

根据回答调整后续问题：
- 学习/好奇 → 问深度偏好和关注焦点
- 投资决策 → 问决策标准和约束条件
- 写报告 → 问受众和格式要求

**2. 消化用户素材**

用户可能提供：思路文档、讨论框架、参考资料、数据文件夹。
- 阅读所有素材
- 提取关键信息和约束
- 在提纲中体现用户的思路

**3. 讨论并确认研究提纲（核心步骤）**

生成结构化提纲并与用户讨论确认：

```markdown
# 研究主题：{topic}

## 研究目标
{由讨论确定}

## 核心研究问题
1. {问题1}
2. {问题2}
3. {问题3}

## 报告结构要求
### 1. {章节1}
- 重点关注：...
- 数据来源要求：...
### 2. {章节2}
...

## 质量标准
- 必须交叉验证的事实：...
- 信息时效要求：...

## 用户素材/约束
- {摘要}
```

用户确认后保存为 `{output_dir}/{slug}/outline.md`，进入 Stage 2。

---

## Stage 2: 执行

### Deep Mode → Gemini Deep Research API

```bash
python {SKILL_DIR}/scripts/deep_research.py \
  "{topic}" \
  --outline {outline_path} \
  --data-dir {data_dir} \
  --attach {file1} --attach {file2} \
  --output {output_dir}/{slug}/
```

- 耗时 10-30 分钟
- 支持 file_search（自有数据）、多模态输入、流式输出
- 参数/用法详见 `docs/guide.md`

### Lite Mode → Gemini CLI

使用 `scripts/lite_research.sh`：

```bash
bash {SKILL_DIR}/scripts/lite_research.sh \
  --topic "{topic}" \
  --outline "{outline_path}" \
  --output "{output_dir}/{slug}/" \
  --model "{gemini_model}"
```

- 耗时 3-8 分钟，草稿质量
- 使用模型：`gemini-3-pro-preview`（可配置）

### 异步通知（两种模式共用）

执行完成后，通过 cron(wake) 通知主 agent：

```
cron(
  action: 'wake',
  text: '🔬 研究完成: {topic}
  模式: {deep|lite}
  关键发现: {2-3 bullet points}
  报告路径: {output_path}',
  mode: 'now'
)
```

> **注意**：Stage 2 耗时较长（最多30分钟），必须使用 sessions_spawn 后台执行。

---

## Stage 3: 验证（仅 Deep Mode）

收到 wake 通知后：

1. 读取完整报告
2. 按 `references/research_methodology.md` 的质量标准审查：
   - 源多样性和权威性
   - 关键事实交叉验证
   - 偏见和利益冲突评估
   - 信息时效性
   - 与用户提纲的覆盖度
3. 如有遗漏/问题 → 用 `--followup` 在原会话上追问：
   ```bash
   python {SKILL_DIR}/scripts/deep_research.py \
     --followup {session_json} "请展开第二点的论据"
   ```
4. 整合为最终报告

---

## 输出结构

```
{output_dir}/{slug}/
├── outline.md                    # Stage 1 生成的研究提纲
├── {topic}_{ts}_report.md        # 研究报告（Deep/Lite）
├── {topic}_{ts}_report.session.json  # 会话文件（Deep，用于追问）
└── verification_notes.md         # 验证记录（Deep 可选）
```

## 约束

### MUST
- Stage 1 必须经过用户确认提纲后才能开始 Stage 2
- 标注数据来源和获取时间
- Deep Mode 必须进行 Stage 3 验证

### MUST NOT
- ❌ 跳过 Stage 1 直接执行研究
- ❌ 在报告中编造引用或数据
- ❌ Lite 模式冒充深度研究输出
