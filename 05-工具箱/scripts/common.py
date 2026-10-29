from pathlib import Path
from datetime import date
import html
import re
import subprocess

SCRIPTS = Path(__file__).resolve().parent
PUBLIC = SCRIPTS.parents[1]
SPACE = PUBLIC.parent
PERSONAL = SPACE / "个人仓"
TEMPLATE = PERSONAL / "模板"
EXCHANGE = PUBLIC / "03-交换区"
OUTBOX = EXCHANGE / "出件箱"
INBOX = EXCHANGE / "收件箱"
LEDGER = EXCHANGE / "交换台账.md"
WORKTABLES = PUBLIC / "02-推进管理" / "工作台"
INDEXES = PUBLIC / "02-推进管理" / "索引"
BOARD = PUBLIC / "02-推进管理" / "任务看板.md"
NOTICE = PUBLIC / "02-推进管理" / "通知台账.md"
KNOW = PUBLIC / "04-知识区"
CURRENT = KNOW / "current"
HISTORY = KNOW / "history"
ROSTER = PUBLIC / "01-成员与规则" / "成员名册.md"
OUTER = PUBLIC / "07-外圈只读"
INDEX_FILES = [
    INDEXES / "文件索引.md",
    INDEXES / "关键词索引.md",
    INDEXES / "人物索引.md",
    INDEXES / "被引用表.md",
    INDEXES / "孤儿文件.md",
]
OUTER_FILES = [OUTER / "任务看板.html", OUTER / "README.md"]


def today():
    return date.today().isoformat()


def read(p):
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


def write(p, s):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def roster_members():
    names = []
    for line in read(ROSTER).splitlines():
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 1 and cells[0] not in ("姓名",) and not cells[0].startswith("外圈"):
                names.append(cells[0])
    return names


def members():
    return roster_members()


def personal_members():
    return sorted(d.name for d in PERSONAL.iterdir() if d.is_dir() and d.name != "模板") if PERSONAL.is_dir() else []


def personal_repo(member, root=None):
    if root:
        return Path(root)
    p = PERSONAL / member
    return p if p.is_dir() else None


def sanitize(s):
    s = re.sub(r"[^\w\u4e00-\u9fff-]+", "-", (s or "").strip())
    return s.strip("-") or "未命名"


def doc_id(frm, to, topic, typ):
    return f"{date.today().strftime('%Y%m%d')}-{sanitize(frm)}-{sanitize(to)}-{sanitize(topic)}-{sanitize(typ)}"


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


def pointer(target, doc_path, action):
    stem = Path(doc_path).stem
    p = INBOX / target / f"{stem}.pointer.md"
    write(p, f"# 指向消息\n\n正件路径：{doc_path}\n动作类型：{action}\n日期：{today()}\n")
    return p


def copy_to_personal(member, filename, content, root=None):
    repo = personal_repo(member, root)
    if not repo:
        return None
    p = repo / "05-单据" / filename
    write(p, content)
    return p


def notice(target, event, doc):
    lines = read(NOTICE).rstrip().splitlines()
    lines.append(f"| {today()} | {target} | {event} | {doc} |")
    write(NOTICE, "\n".join(lines) + "\n")


def task_status_files(member, root=None):
    repo = personal_repo(member, root)
    if not repo:
        return []
    base = repo / "00-任务包"
    if not base.is_dir():
        return []
    return [f for f in sorted(base.glob("*/任务状态.yaml")) if "模板" not in f.parent.name]


def parse_status(path):
    data = {}
    for line in read(path).splitlines():
        if ":" in line and not line.strip().startswith("#"):
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def worktable(member, root=None):
    rows = []
    for f in task_status_files(member, root):
        d = parse_status(f)
        pkg = f.parent.name
        task_pkg = f"外部个人仓/{member}/00-任务包/{pkg}" if root else f"个人仓/{member}/00-任务包/{pkg}"
        rows.append((
            d.get("任务", pkg),
            d.get("状态", "未开始"),
            d.get("阻塞原因", ""),
            task_pkg,
            d.get("产出", ""),
            d.get("更新", today()),
        ))
    lines = [
        f"# {member} 的工作台",
        "",
        "> 由个人仓任务状态生成；不要手写。",
        "",
        "| 任务 | 状态 | 阻塞/在等 | 任务包 | 产出 | 更新 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    if not rows:
        lines.append("| 暂无任务 | — | — | — | — | — |")
    write(WORKTABLES / f"{member}.md", "\n".join(lines) + "\n")


def worktable_rows(member):
    rows = []
    for line in read(WORKTABLES / f"{member}.md").splitlines():
        if line.startswith("|") and "---" not in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 6 and cells[0] not in ("任务", "暂无任务"):
                rows.append(cells)
    return rows


def stale(update):
    try:
        d = date.fromisoformat(update)
    except ValueError:
        return False
    return (date.today() - d).days > 3


def rebuild_board():
    lines = [
        "# 任务看板",
        "",
        "> 由工作台与交换台账重建；自报与证据对不上时标红，工作台过期标注。",
        "",
        "## 工作台",
        "",
        "| 成员 | 任务 | 状态 | 阻塞/在等 | 任务包 | 更新 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for m in members():
        for r in worktable_rows(m):
            status = r[1] + ("（过期）" if stale(r[5]) else "")
            lines.append(f"| {m} | {r[0]} | {status} | {r[2]} | {r[3]} | {r[5]} |")
    lines += ["", "## 交换台账", "", "| 单号 | 类型 | 发起人 | 接收人 | 状态 | 日期 |", "| --- | --- | --- | --- | --- | --- |"]
    for r in ledger_rows():
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[5]} | {r[6]} |")
    lines += ["", "## 对账", "", "| 任务 | 自报 | 台账 | 结论 |", "| --- | --- | --- | --- |"]
    found = False
    for m in personal_members():
        for f in task_status_files(m):
            d = parse_status(f)
            upstream = d.get("上游单据", "")
            if upstream and upstream not in ("无", "待甲投递", "待甲改投", "待投递"):
                row = find_ledger(upstream)
                state = row[5] if row else "台账无记录"
                if d.get("状态") == "已完成" and state != "已归集":
                    conclusion = "**对不上**"
                elif row:
                    conclusion = "一致"
                else:
                    conclusion = "**对不上**"
                lines.append(f"| {m} / {d.get('任务', f.parent.name)} | {d.get('状态','')} | {state} | {conclusion} |")
                found = True
    for m in members():
        if m in personal_members():
            continue
        for r in worktable_rows(m):
            lines.append(f"| {m} / {r[0]} | {r[1]} | — | 外部成员未接入对账 |")
            found = True
    if not found:
        lines.append("| — | — | — | 暂无可对账的单据 |")
    write(BOARD, "\n".join(lines) + "\n")


def effectiveness(rel):
    if rel.startswith("04-知识区/current/"):
        return "正本"
    if rel.startswith("03-交换区/出件箱/"):
        return "正本"
    if rel.startswith("03-交换区/收件箱/"):
        return "副本（指向）"
    if rel.startswith("04-知识区/history/") or rel.startswith("06-归档/"):
        return "冻结"
    if rel.startswith("05-工具箱/"):
        return "工具"
    if rel.startswith("01-成员与规则/单据模板/"):
        return "模板"
    return "正本"


def public_files():
    files = []
    for p in sorted(PUBLIC.rglob("*")):
        if not p.is_file() or ".git" in p.parts or "__pycache__" in p.parts:
            continue
        if p.name in (".DS_Store", ".gitkeep") or p.suffix in (".pyc",):
            continue
        files.append(p.relative_to(PUBLIC).as_posix())
    return files


def rebuild_indexes():
    files = public_files()
    file_lines = ["# 文件索引", "", "> 脚本生成；按文件查，标效力级。", "", "| 文件 | 效力级 |", "| --- | --- |"]
    for f in files:
        file_lines.append(f"| {f} | {effectiveness(f)} |")
    write(INDEXES / "文件索引.md", "\n".join(file_lines) + "\n")

    kw = ["# 关键词索引", "", "> 脚本生成；按事查。", "", "| 关键词 | 位置 |", "| --- | --- |"]
    for f in files:
        if f.startswith("04-知识区/静态知识/") or f.startswith("04-知识区/动态知识/"):
            for line in read(PUBLIC / f).splitlines():
                if line.startswith("#"):
                    kw.append(f"| {line.lstrip('#').strip()} | {f} |")
    kw += [
        "| 协同单 | 01-成员与规则/单据模板/协同单.md |",
        "| 回执 | 01-成员与规则/单据模板/回执.md |",
        "| 退回单 | 01-成员与规则/单据模板/退回单.md |",
        "| 任务包 | 01-成员与规则/任务包标准.md |",
        "| 写回权限 | 01-成员与规则/写回权限表.md |",
    ]
    write(INDEXES / "关键词索引.md", "\n".join(kw) + "\n")

    person = ["# 人物索引", "", "> 脚本生成；按人查。", "", "| 人物 | 出现位置 |", "| --- | --- |"]
    for m in members():
        hits = []
        for f in files:
            if f.startswith("05-工具箱/"):
                continue
            if m in read(PUBLIC / f):
                hits.append(f)
        person.append(f"| {m} | {', '.join(hits[:12]) if hits else '—'} |")
    write(INDEXES / "人物索引.md", "\n".join(person) + "\n")

    refs = {}
    for f in files:
        text = read(PUBLIC / f)
        for target in files:
            if target == f:
                continue
            stem = Path(target).stem
            if target in text or (len(stem) >= 8 and stem in text):
                refs.setdefault(target, set()).add(f)
    ref_lines = ["# 被引用表", "", "> 脚本生成；改一个口径前先看会影响谁。", "", "| 文件 | 被哪些文件引用 | 次数 |", "| --- | --- | --- |"]
    for target in sorted(refs):
        sources = sorted(refs[target])
        ref_lines.append(f"| {target} | {', '.join(sources[:8])} | {len(sources)} |")
    write(INDEXES / "被引用表.md", "\n".join(ref_lines) + "\n")

    allow = ("00-入口/", "02-推进管理/索引/", "05-工具箱/", "06-归档/README", "README.md", "AGENTS.md", "04-知识区/README.md", "03-交换区/", "04-知识区/current/.gitkeep")
    orphans = [f for f in files if f not in refs and not f.startswith(allow)]
    orphan_lines = ["# 孤儿文件", "", "> 脚本生成；没有被任何文件引用，巡检提示归档。", "", "| 文件 |", "| --- |"] + [f"| {f} |" for f in orphans]
    write(INDEXES / "孤儿文件.md", "\n".join(orphan_lines) + "\n")
    return len(orphans)


def publish_outer():
    rows = []
    for m in members():
        for r in worktable_rows(m):
            rows.append((m, r[0], r[1], r[2], r[3], r[5]))
    trs = []
    for r in rows:
        trs.append("<tr>" + "".join(f"<td>{html.escape(x)}</td>" for x in r) + "</tr>")
    led = []
    for r in ledger_rows():
        led.append("<tr>" + "".join(f"<td>{html.escape(x)}</td>" for x in [r[0], r[1], r[2], r[3], r[5], r[6]]) + "</tr>")
    doc = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>任务看板 · 外圈只读</title>
<style>body{{font:15px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;margin:32px;color:#1b1b1a;background:#f6f5f2}}h1{{font-size:26px}}table{{border-collapse:collapse;width:100%;margin:12px 0 28px;background:#fff}}th,td{{border:1px solid #e2e0da;padding:8px 10px;text-align:left;vertical-align:top}}th{{background:#f0efeb}}code{{font-size:.9em}}.meta{{color:#7a7974;font-size:13px}}</style></head>
<body>
<h1>任务看板</h1>
<p class="meta">外圈只读快照；以公共仓 Markdown 记录为准。生成：{today()}</p>
<h2>工作台</h2>
<table><thead><tr><th>成员</th><th>任务</th><th>状态</th><th>阻塞/在等</th><th>任务包</th><th>更新</th></tr></thead><tbody>
{''.join(trs)}
</tbody></table>
<h2>交换台账</h2>
<table><thead><tr><th>单号</th><th>类型</th><th>发起人</th><th>接收人</th><th>状态</th><th>日期</th></tr></thead><tbody>
{''.join(led)}
</tbody></table>
<p class="meta">结论看 <code>04-知识区/current/</code>；决策看 <code>04-知识区/动态知识/决策记录.md</code>；人员看 <code>01-成员与规则/成员名册.md</code>。</p>
</body></html>
"""
    write(OUTER / "任务看板.html", doc)
    write(OUTER / "README.md", "# 外圈只读\n\n- 任务看板：`任务看板.html`\n- 结论：`../04-知识区/current/`\n- 决策：`../04-知识区/动态知识/决策记录.md`\n- 人员：`../01-成员与规则/成员名册.md`\n\n外圈只读公共仓，不碰任何个人仓。\n")


def inspect():
    issues = []
    for m in personal_members():
        for f in task_status_files(m):
            pkg = f.parent
            for need in ["任务说明.md", "输入清单.md", "待裁决事项.md", "过程记录.md", "工作产出", "任务状态.yaml"]:
                if not (pkg / need).exists():
                    issues.append(f"{m}/{pkg.name} 缺少 {need}")
            d = parse_status(f)
            for k in ["任务", "状态", "更新"]:
                if not d.get(k):
                    issues.append(f"{m}/{pkg.name}/任务状态.yaml 缺少 {k}")
            up = d.get("上游单据", "")
            if up and up not in ("无", "待甲投递", "待甲改投", "待投递") and not find_ledger(up):
                issues.append(f"{m}/{pkg.name} 上游单据 {up} 不在台账")
    for base in [OUTBOX, INBOX]:
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("*.md")):
            if p.name.endswith(".pointer.md"):
                continue
            if not re.match(r"^\d{8}-[^-]+-[^-]+-[^-]+-(协同单|回执|退回单)(-(回执|退回))?\.md$", p.name):
                issues.append(f"{p.relative_to(PUBLIC).as_posix()} 不符合五段命名")
    for row in ledger_rows():
        doc, typ, frm, to, topic, status, d = row
        out = OUTBOX / frm / f"{doc}.md"
        ptr = INBOX / to / f"{doc}.pointer.md"
        if status in ("已投递", "已回执", "已归集", "已退回"):
            if not out.exists():
                issues.append(f"台账 {doc} 缺正件：{out.relative_to(PUBLIC).as_posix()}")
            if not ptr.exists():
                issues.append(f"台账 {doc} 缺指向消息：{ptr.relative_to(PUBLIC).as_posix()}")
        if status == "已回执":
            if not (OUTBOX / to / f"{doc}-回执.md").exists():
                issues.append(f"台账 {doc} 已回执但缺回执文件")
        if status == "已退回":
            if not (OUTBOX / to / f"{doc}-退回.md").exists():
                issues.append(f"台账 {doc} 已退回但缺退回单")
    pat = re.compile(r"(中签率|配额总量|放量节奏|当期机型)\s*[:：=]?\s*\d")
    for p in PUBLIC.rglob("*.md"):
        if ".git" in p.parts:
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            if pat.search(line):
                issues.append(f"{p.relative_to(PUBLIC).as_posix()}:{i} 疑似保密数值")
    for m in members():
        for r in worktable_rows(m):
            if stale(r[5]):
                issues.append(f"{m}/{r[0]} 工作台过期（{r[5]}）")
    return issues


def snapshot(paths):
    return {p: (p.read_text(encoding="utf-8") if p.exists() else None) for p in paths}


def restore(snap):
    for p, s in snap.items():
        if s is None:
            if p.exists():
                p.unlink()
        else:
            write(p, s)


def rollback(snap):
    restore(snap)
    subprocess.run(["git", "-C", str(PUBLIC), "reset"], check=False, capture_output=True)


def commit_public(message):
    status = subprocess.run(["git", "-C", str(PUBLIC), "status", "--porcelain"], capture_output=True, text=True)
    if not status.stdout.strip():
        return True, "没有变化"
    subprocess.run(["git", "-C", str(PUBLIC), "add", "-A"], check=False, capture_output=True)
    r = subprocess.run(["git", "-C", str(PUBLIC), "commit", "-m", message], capture_output=True, text=True)
    if r.returncode != 0:
        return False, (r.stdout + r.stderr).strip()
    remote = subprocess.run(["git", "-C", str(PUBLIC), "remote"], capture_output=True, text=True)
    if remote.stdout.strip():
        p = subprocess.run(["git", "-C", str(PUBLIC), "push"], capture_output=True, text=True)
        if p.returncode != 0:
            return True, "已提交本地，推送失败：" + (p.stdout + p.stderr).strip()
    return True, ""
