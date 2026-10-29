import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="收工：同步工作台、重建看板/索引、巡检、提交个人仓")
    p.add_argument("--成员", required=True)
    p.add_argument("--message", default="")
    a = p.parse_args()
    if a.成员 not in common.members():
        print(f"成员不存在；现有：{common.members()}")
        return 1

    common.worktable(a.成员)
    common.rebuild_board()
    common.rebuild_indexes()
    issues = common.inspect()
    print(f"巡检：{len(issues)} 个问题")
    for x in issues:
        print(f"- {x}")
    if issues:
        return 1

    repo = common.PERSONAL / a.成员
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=False)
    diff = subprocess.run(["git", "-C", str(repo), "diff", "--cached", "--quiet"], check=False)
    if diff.returncode != 0:
        msg = a.message or f"{a.成员} 收工"
        subprocess.run(["git", "-C", str(repo), "commit", "-m", msg], check=False)
        print("个人仓已提交")
    else:
        print("个人仓没有变化")
    print("公共仓的脚本产物已更新；请统筹审阅后提交公共仓。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
