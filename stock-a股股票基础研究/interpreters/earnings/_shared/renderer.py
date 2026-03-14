import csv
import io
import json
from pathlib import Path


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_latest_summary(output_dir: Path):
    if not output_dir.exists():
        return None
    candidates = sorted(output_dir.glob("summary_*.json"))
    if not candidates:
        return None
    return candidates[-1]


def load_stock_names(data_path: Path):
    if not data_path.exists():
        return {}
    mapping = {}
    with data_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ts_code = (row.get("ts_code") or "").strip()
            name = (row.get("name") or "").strip()
            if ts_code and name:
                mapping[ts_code] = name
    return mapping


def format_amount(value):
    """金额格式化：统一万元"""
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{v:.2f}万"


def format_delta(delta):
    """超预期幅度格式化：+xx% 或 -xx%"""
    if delta is None:
        return "N/A"
    try:
        d = float(delta)
    except (TypeError, ValueError):
        return str(delta)
    sign = "+" if d >= 0 else ""
    return f"{sign}{d * 100:.2f}%"


def format_alert(alert, name_map):
    ts_code = (alert.get("ts_code") or "").strip()
    name = name_map.get(ts_code, "")
    end_date = alert.get("end_date")
    source_raw = alert.get("source")
    source_map = {
        "forecast": "业绩预告",
        "express": "业绩快报",
        "income": "正式业绩",
    }
    source = source_map.get(source_raw, source_raw)
    actual = alert.get("actual_value")
    expected = alert.get("expected_max")
    delta = alert.get("delta_max")
    ann_date = None
    period = None
    report_min = None
    report_max = None
    reason = None
    alert_type = None
    payload = alert.get("payload_json")
    if payload:
        try:
            payload_obj = json.loads(payload)
            alert_type = payload_obj.get("alert_type")
            reason = payload_obj.get("reason_hint")
            ann_date = payload_obj.get("ann_date")
            period = payload_obj.get("period")
            report_min = payload_obj.get("expected_report_date_min")
            report_max = payload_obj.get("expected_report_date_max")
        except json.JSONDecodeError:
            reason = None
    title = f"{ts_code} {name}".strip()
    actual_text = format_amount(actual)
    expected_text = format_amount(expected)
    delta_text = format_delta(delta)
    # 根据 alert_type 判断标签
    type_label_map = {
        "above": "超预期",
        "below": "低于预期",
        "inline": "符合预期",
    }
    delta_label = type_label_map.get(alert_type, "偏差")
    parts = [
        f"{title} {end_date} [{source}]",
        f"实际:{actual_text} 预期上限:{expected_text} {delta_label}:{delta_text}",
    ]
    if period:
        parts.append(f"报告期:{period}")
    if ann_date:
        parts.append(f"公告日:{ann_date}")
    if report_min or report_max:
        parts.append(f"预期报告期:{report_min}-{report_max}")
    if reason:
        parts.append(f"原因:{reason}")
    return " | ".join(parts)


def get_alert_type_and_ann_date(alert):
    """从 alert 中提取 alert_type 和 ann_date"""
    alert_type = None
    ann_date = None
    payload = alert.get("payload_json")
    if payload:
        try:
            payload_obj = json.loads(payload)
            alert_type = payload_obj.get("alert_type")
            ann_date = payload_obj.get("ann_date")
        except json.JSONDecodeError:
            pass
    return alert_type or "unknown", ann_date or ""


def build_report(summary, max_alerts: int = 5, name_map=None):
    name_map = name_map or {}
    alerts = summary.get("alerts", [])
    changes = summary.get("changes", [])
    lines = []
    lines.append(f"告警数: {len(alerts)}")
    lines.append(f"预期变动数: {len(changes)}")

    if alerts:
        # 按 alert_type 分组
        grouped = {"above": [], "inline": [], "below": []}
        for alert in alerts:
            alert_type, ann_date = get_alert_type_and_ann_date(alert)
            if alert_type in grouped:
                grouped[alert_type].append((ann_date, alert))
            else:
                grouped.setdefault("unknown", []).append((ann_date, alert))

        # 每组按公告日排序
        for key in grouped:
            grouped[key].sort(key=lambda x: x[0], reverse=True)

        type_labels = [
            ("above", "超预期"),
            ("inline", "符合预期"),
            ("below", "低于预期"),
        ]
        for type_key, label in type_labels:
            items = grouped.get(type_key, [])
            if items:
                lines.append(f"\n【{label}】({len(items)}条)")
                for _, alert in items[:max_alerts]:
                    lines.append(f"- {format_alert(alert, name_map)}")
                if len(items) > max_alerts:
                    lines.append(f"  ... 还有 {len(items) - max_alerts} 条")
    else:
        lines.append("无告警")

    if changes:
        lines.append("\n预期变动:")
        for change in changes[:max_alerts]:
            ts_code = (change.get("ts_code") or "").strip()
            name = name_map.get(ts_code, "")
            period = change.get("period")
            org = change.get("org_name")
            direction = change.get("direction")
            direction_map = {
                "up": "上调",
                "down": "下调",
                "same": "不变",
            }
            direction = direction_map.get(direction, direction)
            title = f"{ts_code} {name}".strip()
            lines.append(f"- {title} {period} {org} {direction}")
    return "\n".join(lines)


def build_csv(summary, name_map=None, today_date=None):
    """生成 CSV 格式的告警列表
    
    Args:
        today_date: 今日日期(YYYY-MM-DD)，用于标记新增。默认为当前日期。
    """
    from datetime import datetime
    
    name_map = name_map or {}
    alerts = summary.get("alerts", [])
    
    if today_date is None:
        today_date = datetime.now().strftime("%Y-%m-%d")

    def get_created_date(alert):
        """提取 created_at 的日期部分"""
        created_at = alert.get("created_at") or ""
        if len(created_at) >= 10:
            return created_at[:10]
        return ""

    # 分为今日新增和历史
    today_alerts = []
    history_alerts = []
    for alert in alerts:
        alert_type, ann_date = get_alert_type_and_ann_date(alert)
        created_date = get_created_date(alert)
        is_new = (created_date == today_date)
        if is_new:
            today_alerts.append((alert_type, ann_date, alert))
        else:
            history_alerts.append((alert_type, ann_date, alert))

    # 每组内按 alert_type 排序（above > inline > below），再按公告日倒序
    type_order = {"above": 0, "inline": 1, "below": 2, "unknown": 3}
    today_alerts.sort(key=lambda x: (type_order.get(x[0], 9), x[1]), reverse=False)
    today_alerts.sort(key=lambda x: x[1], reverse=True)
    today_alerts.sort(key=lambda x: type_order.get(x[0], 9))
    
    history_alerts.sort(key=lambda x: (type_order.get(x[0], 9), x[1]), reverse=False)
    history_alerts.sort(key=lambda x: x[1], reverse=True)
    history_alerts.sort(key=lambda x: type_order.get(x[0], 9))

    # 合并：今日新增在前
    sorted_alerts = [(True, a[2]) for a in today_alerts] + [(False, a[2]) for a in history_alerts]

    output = io.StringIO()
    writer = csv.writer(output)

    # 表头
    writer.writerow([
        "新增", "类型", "代码", "名称", "报告期末", "数据来源",
        "实际值(万)", "预期下限(万)", "预期均值(万)", "预期上限(万)", "偏差(%)",
        "报告期", "公告日", "预期报告期", "入库时间"
    ])

    type_label_map = {
        "above": "超预期",
        "below": "低于预期",
        "inline": "符合预期",
    }
    source_map = {
        "forecast": "业绩预告",
        "express": "业绩快报",
        "income": "正式业绩",
    }

    for is_new, alert in sorted_alerts:
        ts_code = (alert.get("ts_code") or "").strip()
        name = name_map.get(ts_code, "")
        end_date = alert.get("end_date")
        source_raw = alert.get("source")
        source = source_map.get(source_raw, source_raw)
        actual = alert.get("actual_value")
        created_at = alert.get("created_at") or ""
        expected_min = None
        expected_mean = None
        expected_max = alert.get("expected_max")
        delta = alert.get("delta_max")
        alert_type = None
        ann_date = None
        period = None
        report_range = ""

        payload = alert.get("payload_json")
        if payload:
            try:
                payload_obj = json.loads(payload)
                alert_type = payload_obj.get("alert_type")
                expected_min = payload_obj.get("expected_min")
                expected_mean = payload_obj.get("expected_mean")
                ann_date = payload_obj.get("ann_date")
                period = payload_obj.get("period")
                report_min = payload_obj.get("expected_report_date_min")
                report_max = payload_obj.get("expected_report_date_max")
                if report_min or report_max:
                    report_range = f"{report_min}-{report_max}"
            except json.JSONDecodeError:
                pass

        type_label = type_label_map.get(alert_type, "未知")
        new_label = "★" if is_new else ""

        # 格式化数值
        actual_fmt = f"{actual:.2f}" if actual is not None else ""
        min_fmt = f"{expected_min:.2f}" if expected_min is not None else ""
        mean_fmt = f"{expected_mean:.2f}" if expected_mean is not None else ""
        max_fmt = f"{expected_max:.2f}" if expected_max is not None else ""
        delta_fmt = f"{delta * 100:.2f}" if delta is not None else ""

        writer.writerow([
            new_label, type_label, ts_code, name, end_date, source,
            actual_fmt, min_fmt, mean_fmt, max_fmt, delta_fmt,
            period, ann_date, report_range, created_at
        ])

    return output.getvalue()


def build_text_report(summary, name_map=None, days: int = 3):
    """生成最近N天更新的文字报告，按类型分组、公告日排序"""
    from datetime import datetime, timedelta
    
    name_map = name_map or {}
    alerts = summary.get("alerts", [])
    
    # 计算日期范围
    today = datetime.now()
    cutoff_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    
    type_label_map = {
        "above": "超预期",
        "below": "低于预期",
        "inline": "符合预期",
    }
    source_map = {
        "forecast": "业绩预告",
        "express": "业绩快报",
        "income": "正式业绩",
    }
    
    def parse_alert(alert):
        """解析 alert 数据"""
        ts_code = (alert.get("ts_code") or "").strip()
        name = name_map.get(ts_code, "")
        title = f"{name}（{ts_code}）" if name else ts_code
        
        source_raw = alert.get("source")
        source = source_map.get(source_raw, source_raw)
        actual = alert.get("actual_value")
        expected_max = alert.get("expected_max")
        delta = alert.get("delta_max")
        ann_date = None
        alert_type = None
        expected_min = None
        
        payload = alert.get("payload_json")
        if payload:
            try:
                payload_obj = json.loads(payload)
                alert_type = payload_obj.get("alert_type")
                expected_min = payload_obj.get("expected_min")
                ann_date = payload_obj.get("ann_date")
            except json.JSONDecodeError:
                pass
        
        return {
            "title": title,
            "source": source,
            "actual": actual,
            "expected_max": expected_max,
            "expected_min": expected_min,
            "delta": delta,
            "alert_type": alert_type,
            "ann_date": ann_date or "",
        }
    
    def format_line(data):
        """格式化单条记录"""
        actual_text = f"{data['actual']:.2f}万" if data['actual'] is not None else "N/A"
        max_text = f"{data['expected_max']:.2f}万" if data['expected_max'] is not None else "N/A"
        min_text = f"{data['expected_min']:.2f}万" if data['expected_min'] is not None else "N/A"
        delta_text = format_delta(data['delta'])
        type_label = type_label_map.get(data['alert_type'], "偏差")
        
        ann_date = data['ann_date']
        if ann_date and len(ann_date) == 8:
            ann_date_fmt = f"{ann_date[:4]}-{ann_date[4:6]}-{ann_date[6:]}"
        else:
            ann_date_fmt = ann_date or "N/A"
        
        return f"{data['title']}：市场预期上限{max_text}、下限{min_text}，{data['source']}披露为{actual_text}，{type_label}{delta_text}，公告日{ann_date_fmt}"
    
    # 筛选最近N天的 alerts
    recent_alerts = []
    for alert in alerts:
        created_at = alert.get("created_at") or ""
        if created_at[:10] >= cutoff_date:
            recent_alerts.append(alert)
    
    if not recent_alerts:
        return f"最近{days}天无新增业绩告警。"
    
    # 按类型分组
    grouped = {"above": [], "inline": [], "below": []}
    for alert in recent_alerts:
        data = parse_alert(alert)
        alert_type = data["alert_type"] or "unknown"
        if alert_type in grouped:
            grouped[alert_type].append(data)
    
    # 每组按公告日倒序
    for key in grouped:
        grouped[key].sort(key=lambda x: x["ann_date"], reverse=True)
    
    lines = [f"【最近{days}天业绩告警更新】共{len(recent_alerts)}条\n"]
    
    type_order = [
        ("above", "超预期"),
        ("inline", "符合预期"),
        ("below", "低于预期"),
    ]
    
    for type_key, type_name in type_order:
        items = grouped.get(type_key, [])
        if items:
            lines.append(f"\n=== {type_name}（{len(items)}条）===")
            for data in items:
                lines.append(format_line(data))
    
    return "\n".join(lines)
