import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    common.rebuild_board()
    common.rebuild_indexes()
    print("已重建：02-推进管理/任务看板.md、索引/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
