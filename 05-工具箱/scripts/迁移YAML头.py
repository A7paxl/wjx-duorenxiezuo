import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def header(fields):
    lines = ["---"]
    for k, v in fields.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def add(p, fields, dry):
    if not p.exists() or common.front_matter(p):
        return False
    if dry:
        print(f"将补头：{p}")
        return True
    common.write(p, header(fields) + common.read(p))
    return True


def main():
    p = argparse.ArgumentParser(description="给已有 Markdown 补 YAML 头")
    p.add_argument("--成员", default="甲")
    p.add_argument("--个人仓", default="")
    p.add_argument("--演练", action="store_true")
    a = p.parse_args()
    dry = a.演练
    changed = 0

    for f in sorted(common.OUTBOX.rglob("*.md")):
        if f.name.endswith(".pointer.md"):
            continue
        stem = f.stem
        typ = "协同单"
        original = stem
        if stem.endswith("-回执"):
            typ = "回执"
            original = stem[:-3]
        elif stem.endswith("-退回"):
            typ = "退回单"
            original = stem[:-3]
        row = common.find_ledger(original)
        if not row:
            continue
        sender = row[3] if typ != "协同单" else row[2]
        receiver = row[2] if typ != "协同单" else row[3]
        fields = {"类型": typ, "单号": original, "发起人": sender, "接收人": receiver, "状态": row[5], "更新": row[6]}
        if add(f, fields, dry):
            changed += 1

    repo = common.personal_repo(a.成员, a.个人仓 or None)
    if repo:
        for pkg in sorted((repo / "00-任务包").iterdir()):
            if not pkg.is_dir() or "模板" in pkg.name:
                continue
            st = common.parse_status(pkg / "任务状态.yaml")
            task = st.get("任务", pkg.name)
            status = st.get("状态", "未开始")
            update = st.get("更新", common.today())
            mapping = {"任务说明.md": "任务说明", "输入清单.md": "输入清单", "待裁决事项.md": "待裁决", "过程记录.md": "过程记录"}
            for name, typ in mapping.items():
                fields = {"类型": typ, "任务": task, "更新": update}
                if typ == "任务说明":
                    fields["状态"] = status
                if add(pkg / name, fields, dry):
                    changed += 1
        for f in sorted((repo / "05-单据").glob("*.md")):
            out = Path(common.OUTBOX) / a.成员 / f.name
            if out.exists() and common.front_matter(out):
                if add(f, common.front_matter(out), dry):
                    changed += 1

    print(f"补头完成：{changed} 个文件" + ("（演练）" if dry else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
