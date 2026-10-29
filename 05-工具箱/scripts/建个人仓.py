import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="建个人仓")
    p.add_argument("--成员", required=True)
    p.add_argument("--岗位", default="成员")
    a = p.parse_args()
    target = common.PERSONAL / a.成员
    if target.exists():
        print(f"个人仓已存在：{target}")
        return 1

    for d in ["00-任务包", "01-草稿", "02-过程记录", "03-生效区", "04-归档", "05-出件箱", "06-收件箱", "09-日志"]:
        (target / d).mkdir(parents=True, exist_ok=True)
    template = common.PERSONAL / "甲" / "00-任务包" / "00-任务包模板"
    if template.exists():
        shutil.copytree(template, target / "00-任务包" / "00-任务包模板")
    common.write(target / "AGENTS.md", f"# {a.成员}的个人仓规程（给 AI）\n\n## 我是谁\n\n{a.成员}，{a.岗位}。\n\n## 开工必读\n\n1. 公共仓 `AGENTS.md`。\n2. 公共仓 `01-成员与规则/协作契约.md`。\n3. 本仓 `00-任务包/` 当前任务状态。\n4. 本仓 `06-收件箱/` 的指向消息。\n\n## 写什么\n\n只写本仓；`06-收件箱/` 只读指向消息；公共仓只通过脚本或向统筹提案。\n\n## 收工\n\n更新任务状态、过程记录、当天日志；同步工作台；提交个人仓。\n")
    common.write(target / "09-日志" / f"{common.today()}.md", f"# {common.today()}\n\n## 其他\n\n- 个人仓初始化。\n")
    subprocess.run(["git", "-C", str(target), "init", "-b", "main"], check=False)
    print(f"已建：{target.relative_to(common.SPACE).as_posix()}")
    print("请设置本仓 git 身份后提交。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
