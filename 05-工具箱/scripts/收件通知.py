import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="收件通知：扫描公共仓收件箱的指向消息")
    p.add_argument("--成员", default="")
    a = p.parse_args()
    targets = [a.成员] if a.成员 else common.members()
    found = False
    for m in targets:
        folder = common.INBOX / m
        if not folder.is_dir():
            continue
        for ptr in sorted(folder.glob("*.pointer.md")):
            print(f"收件通知：{m} 收到 {ptr.name.replace('.pointer.md', '')}")
            found = True
    if not found:
        print("收件通知：没有新的指向消息")
    return 0


if __name__ == "__main__":
    sys.exit(main())
