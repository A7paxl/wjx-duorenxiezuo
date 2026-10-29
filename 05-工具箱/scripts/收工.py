import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="收工：同步工作台、重建看板/索引、巡检、提交个人仓")
    p.add_argument("--成员", required=True)
    p.add_argument("--个人仓", default="")
    p.add_argument("--message", default="")
    a = p.parse_args()
    if a.成员 not in common.members():
        print(f"成员不在名册；现有：{common.members()}")
        return 1
    repo = common.personal_repo(a.成员, a.个人仓 or None)
    if not repo:
        print("找不到个人仓；外部成员请用 --个人仓 指定")
        return 1

    paths = [common.WORKTABLES / f"{a.成员}.md", common.BOARD,
             common.INDEXES / "文件索引.md", common.INDEXES / "关键词索引.md", common.INDEXES / "人物索引.md"]
    snap = common.snapshot(paths)
    try:
        common.worktable(a.成员, a.个人仓 or None)
        common.rebuild_board()
        common.rebuild_indexes()
    except Exception as e:
        common.rollback(snap)
        print(f"收工失败，已回滚：{e}")
        return 1

    issues = common.inspect()
    print(f"巡检：{len(issues)} 个问题")
    for x in issues:
        print(f"- {x}")
    if issues:
        common.rollback(snap)
        return 1

    ok, msg = common.commit_public(f"同步工作台 {a.成员}")
    if not ok:
        common.rollback(snap)
        print(f"公共仓提交失败，已回滚：{msg}")
        return 1

    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=False)
    diff = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--quiet"], check=False)
    if diff.returncode != 0:
        m = a.message or f"{a.成员} 收工"
        subprocess.run(["git", "-C", str(repo), "commit", "-m", m], check=False)
        print("个人仓已提交")
    else:
        print("个人仓没有变化")
    if msg:
        print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
