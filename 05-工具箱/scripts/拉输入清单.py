import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="拉输入清单候选")
    p.add_argument("--成员", required=True)
    p.add_argument("--任务包", required=True)
    p.add_argument("--个人仓", default="")
    a = p.parse_args()

    repo = common.personal_repo(a.成员, a.个人仓 or None)
    if not repo:
        print("找不到个人仓；外部成员请用 --个人仓 指定")
        return 1
    pkg = Path(a.任务包)
    if not pkg.is_absolute():
        if (repo / "00-任务包" / a.任务包).is_dir():
            pkg = repo / "00-任务包" / a.任务包
        else:
            pkg = Path.cwd() / a.任务包
    if not pkg.is_dir():
        print(f"任务包不存在：{pkg}")
        return 1

    rows = []
    for f in sorted((common.PUBLIC / "04-知识区" / "静态知识").glob("*.md")):
        rows.append((f.relative_to(common.PUBLIC).as_posix(), "静态知识，默认全读", "是"))
    for f in sorted((common.PUBLIC / "04-知识区" / "动态知识").rglob("*.md")):
        rows.append((f.relative_to(common.PUBLIC).as_posix(), "动态知识，按任务相关性选", ""))
    for f in sorted((repo / "05-单据").glob("*.md")):
        rows.append((f"个人仓/{repo.name}/05-单据/{f.name}", "个人单据副本，按需选", ""))

    lines = [
        "# 输入清单（候选）",
        "",
        "> 由 `拉输入清单.py` 生成；本人确认后，把要读的标“是”，其余删掉或标“否”。清单外的文件不读。",
        "",
        "| 文件 | 用途 | 是否必读 |",
        "| --- | --- | --- |",
    ]
    for r in rows:
        lines.append("| " + " | ".join(r) + " |")
    out = pkg / "输入清单_候选.md"
    common.write(out, "\n".join(lines) + "\n")
    print(f"已生成：{out}")
    print("请本人确认后，把结果写进同目录的 输入清单.md。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
