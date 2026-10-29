import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    issues = common.validate_headers()
    print(f"校验：{len(issues)} 个问题")
    for x in issues:
        print(f"- {x}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
