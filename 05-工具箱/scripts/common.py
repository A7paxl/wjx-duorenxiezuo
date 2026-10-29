from pathlib import Path
from datetime import date
import re

SCRIPTS = Path(__file__).resolve().parent
PUBLIC = SCRIPTS.parents[1]
SPACE = PUBLIC.parent
PERSONAL = SPACE / "个人仓"
LEDGER = PUBLIC / "03-交换区" / "交换台账.md"
WORKTABLES = PUBLIC / "02-推进管理" / "工作台"
INDEXES = PUBLIC / "02-推进管理" / "索引"
BOARD = PUBLIC / "02-推进管理" / "任务看板.md"
NOTICE = PUBLIC / "02-推进管理" / "通知台账.md"
KNOW = PUBLIC / "04-知识区"
CURRENT = KNOW / "current"
HISTORY = KNOW / "history"


def today():
    return date.today().isoformat()


def read(p):
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def members():
    return sorted(d.name for d in PERSONAL.iterdir() if d.is_dir()) if PERSONAL.is_dir() else []


def sanitize(s):
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", (s or "").strip())
    return s.strip("-") or "未命名"


def doc_id(frm, to, typ, topic):
    return f"{date.today().strftime('%Y%m%d')}-{sanitize(frm)}-{sanitize(to)}-{sanitize(typ)}-{sanitize(topic)}"


def ensure_ledger():
    if not LEDGER.exists():
        write(LEDGER, "# 交换台账\n\n| 单号 | 类型 | 发起人 | 接收人 | 主题 | 状态 | 日期 |\n| --- | --- | --- | --- | --- | --- | --- |\n")


def append_ledger(row):
    ensure_ledger()
    lines = read(LEDGER).rstrip().splitlines()
    lines.append(row)
    write(LEDGER, "\n".join(lines) + "\n")


def update_ledger(doc, status):
    ensure_ledger()
    out = []
    for line in read(LEDGER).splitlines():
        if line.startswith("|") and doc in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 7:
                cells[5] = status
                line = "| " + " | ".join(cells) + " |"
        out.append(line)
    write(LEDGER, "\n".join(out) + "\n")


def ledger_rows():
    rows = []
    for line in read(LEDGER).splitlines():
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 7 and cells[0] != "单号":
                rows.append(cells)
    return rows


def find_ledger(doc):
    for row in ledger_rows():
        if row[0] == doc:
            return row
    return None


def pointer(target, doc_path, action, suffix=""):
    stem = Path(doc_path).stem + suffix
    p = PERSONAL / target / "06-收件箱" / f"{stem}.pointer.md"
    write(p, f"# 指向消息\n\n正件路径：{doc_path}\n动作类型：{action}\n日期：{today()}\n")
    return p


def notice(target, event, doc):
    lines = read(NOTICE).rstrip().splitlines()
    lines.append(f"| {today()} | {target} | {event} | {doc} |")
    write(NOTICE, "\n".join(lines) + "\n")


def task_status_files(member, include_template=False):
    base = PERSONAL / member / "00-任务包"
    if not base.is_dir():
        return []
    files = sorted(base.glob("*/任务状态.yaml"))
    if not include_template:
        files = [f for f in files if "模板" not in f.parent.name]
    return files


def parse_status(path):
    data = {}
    for line in read(path).splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def worktable(member):
    rows = []
    for f in task_status_files(member):
        d = parse_status(f)
        rows.append((
            d.get("任务", f.parent.name),
            d.get("状态", "未开始"),
            d.get("阻塞原因", ""),
            d.get("产出", ""),
            d.get("更新", today()),
        ))
    lines = [
        f"# {member} 的工作台",
        "",
        "> 由个人仓任务状态生成；不要手写。",
        "",
        "| 任务 | 状态 | 阻塞/在等 | 产出 | 更新 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    if not rows:
        lines.append("| 暂无任务 | — | — | — | — |")
    write(WORKTABLES / f"{member}.md", "\n".join(lines) + "\n")


def rebuild_board():
    lines = [
        "# 任务看板",
        "",
        "> 由工作台与交换台账重建；自报与证据对不上时标红。",
        "",
        "## 工作台",
        "",
        "| 成员 | 任务 | 状态 | 阻塞/在等 | 更新 |",
        "| --- | --- | --- | --- | --- |",
    ]
    reconcile = []
    for m in members():
        for f in task_status_files(m):
            d = parse_status(f)
            task = d.get("任务", f.parent.name)
            lines.append(f"| {m} | {task} | {d.get('状态','')} | {d.get('阻塞原因','')} | {d.get('更新','')} |")
            upstream = d.get("上游单据", "")
            if upstream and upstream not in ("无", "待甲投递", "待甲改投"):
                row = find_ledger(upstream)
                ledger_state = row[5] if row else "台账无记录"
                if d.get("状态") == "已完成" and ledger_state != "已归集":
                    reconcile.append(f"| {m} / {task} | 已完成 | {ledger_state} | 对不上 |")
                elif row:
                    reconcile.append(f"| {m} / {task} | {d.get('状态','')} | {ledger_state} | 一致 |")
    lines += ["", "## 交换台账", "", "| 单号 | 类型 | 发起人 | 接收人 | 状态 | 日期 |", "| --- | --- | --- | --- | --- | --- |"]
    for r in ledger_rows():
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[5]} | {r[6]} |")
    lines += ["", "## 对账", "", "| 任务 | 自报 | 台账 | 结论 |", "| --- | --- | --- | --- |"]
    if reconcile:
        lines.extend(reconcile)
    else:
        lines.append("| — | — | — | 暂无可对账的单据 |")
    write(BOARD, "\n".join(lines) + "\n")


def rebuild_indexes():
    files = []
    for p in sorted(PUBLIC.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            files.append(p.relative_to(PUBLIC).as_posix())
    write(INDEXES / "文件索引.md", "# 文件索引\n\n> 脚本生成；按文件查。\n\n| 文件 |\n| --- |\n" + "\n".join(f"| {f} |" for f in files) + "\n")
    write(INDEXES / "关键词索引.md", "# 关键词索引\n\n> 脚本生成；按事查。\n\n| 关键词 | 位置 |\n| --- | --- |\n| 协同单 | 01-成员与规则/单据模板/协同单.md |\n| 回执 | 01-成员与规则/单据模板/回执.md |\n| 退回单 | 01-成员与规则/单据模板/退回单.md |\n| 任务包 | 01-成员与规则/任务包标准.md |\n| 写回权限 | 01-成员与规则/写回权限表.md |\n| 术语与口径 | 04-知识区/静态知识/术语与口径.md |\n")
    write(INDEXES / "人物索引.md", "# 人物索引\n\n> 脚本生成；按人查。\n\n| 人物 | 位置 |\n| --- | --- |\n| 甲 | 01-成员与规则/成员名册.md |\n| 乙 | 01-成员与规则/成员名册.md |\n")


def inspect():
    issues = []
    for m in members():
        for f in task_status_files(m):
            pkg = f.parent
            for need in ["任务说明.md", "输入清单.md", "待裁决事项.md", "过程记录.md", "工作产出", "任务状态.yaml"]:
                if not (pkg / need).exists():
                    issues.append(f"{m}/{pkg.name} 缺少 {need}")
            d = parse_status(f)
            for k in ["任务", "状态", "更新"]:
                if not d.get(k):
                    issues.append(f"{m}/{pkg.name}/任务状态.yaml 缺少 {k}")
        for box in ["05-出件箱", "06-收件箱"]:
            folder = PERSONAL / m / box
            if not folder.is_dir():
                continue
            for p in sorted(folder.glob("*.md")):
                if p.name.endswith(".pointer.md"):
                    continue
                if not re.match(r"^\d{8}-[^-]+-[^-]+-[^-]+-.+?(-回执|-退回)?\.md$", p.name):
                    issues.append(f"{m}/{box}/{p.name} 不符合五段命名")
    pat = re.compile(r"(中签率|配额总量|放量节奏|当期机型)\s*[:：=]?\s*\d")
    for p in PUBLIC.rglob("*.md"):
        if ".git" in p.parts:
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            if pat.search(line):
                issues.append(f"{p.relative_to(PUBLIC).as_posix()}:{i} 疑似保密数值")
    return issues
