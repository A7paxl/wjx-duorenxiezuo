import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="从个人仓任务状态生成本人工作台")
    p.add_argument("--成员", required=True)
    p.add_argument("--个人仓", default="")
    a = p.parse_args()
    if a.成员 not in common.members():
        print(f"成员不在名册；现有：{common.members()}")
        return 1
    if not common.personal_repo(a.成员, a.个人仓 or None):
        print("找不到个人仓；外部成员请用 --个人仓 指定")
        return 1

    paths = [common.WORKTABLES / f"{a.成员}.md", common.BOARD,
             *common.INDEX_FILES]
    snap = common.snapshot(paths)
    try:
        common.worktable(a.成员, a.个人仓 or None)
        common.rebuild_board()
        common.rebuild_indexes()
        ok, msg = common.commit_public(f"同步工作台 {a.成员}")
        if not ok:
            common.rollback(snap)
            print(f"同步失败，已回滚：{msg}")
            return 1
        print(f"已更新：02-推进管理/工作台/{a.成员}.md")
        if msg:
            print(msg)
        return 0
    except Exception as e:
        common.rollback(snap)
        print(f"同步异常，已回滚：{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
