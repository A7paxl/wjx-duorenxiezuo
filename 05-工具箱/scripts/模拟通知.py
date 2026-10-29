import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    rows = [line for line in common.read(common.NOTICE).splitlines() if line.startswith("|") and "---" not in line and "日期" not in line]
    print("模拟京ME通知：最近 5 条")
    for line in rows[-5:]:
        print(line)
    print("（本试点没有京ME API；真实环境在这里调用通知接口。）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
