import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="从个人仓任务状态生成本人工作台")
    p.add_argument("--成员", required=True)
    a = p.parse_args()
    if a.成员 not in common.members():
        print(f"成员不存在；现有：{common.members()}")
        return 1
    common.worktable(a.成员)
    print(f"已更新：02-推进管理/工作台/{a.成员}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
