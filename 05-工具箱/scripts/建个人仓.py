import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import common


def main():
    p = argparse.ArgumentParser(description="建个人仓（每人一个，放在本人机器上）")
    p.add_argument("--成员", required=True)
    p.add_argument("--岗位", default="成员")
    p.add_argument("--类别", default="产品")
    p.add_argument("--职责", default="待补充")
    p.add_argument("--口径", default="—")
    p.add_argument("--路径", default="")
    p.add_argument("--登记", action="store_true", help="同时在公共仓登记名册、出件箱/收件箱、工作台、公告")
    p.add_argument("--演练", action="store_true")
    a = p.parse_args()

    target = Path(a.路径) if a.路径 else (common.PERSONAL / a.成员 if a.成员 == "甲" else Path.home() / "个人仓" / a.成员)
    actions = [
        f"建个人仓：{target}",
        "  - 目录：00-任务包、01-草稿、02-过程记录、03-生效区、04-归档、05-单据、09-日志",
        "  - 复制任务包模板、写 AGENTS.md、git init",
    ]
    if a.登记:
        actions += [
            f"  - 名册新增：{a.成员} / {a.类别} / {a.岗位} / {a.职责} / {a.口径}",
            f"  - 公共仓交换区建出件箱/收件箱：{a.成员}",
            f"  - 工作台建档：02-推进管理/工作台/{a.成员}.md",
            f"  - 公告栏加一条：新成员 {a.成员} 已登记",
        ]
    if a.演练:
        print("【演练】将执行：")
        for x in actions:
            print(x)
        return 0

    if target.exists():
        print(f"个人仓已存在：{target}")
        return 1
    if a.成员 in common.members():
        print(f"名册里已有：{a.成员}")
        return 1

    for d in ["00-任务包", "01-草稿", "02-过程记录", "03-生效区", "04-归档", "05-单据", "09-日志"]:
        (target / d).mkdir(parents=True, exist_ok=True)
    template = common.TEMPLATE / "00-任务包" / "00-任务包模板"
    if template.exists():
        shutil.copytree(template, target / "00-任务包" / "00-任务包模板")
    common.write(target / "AGENTS.md", f"# {a.成员}的个人仓规程（给 AI）\n\n## 我是谁\n\n{a.成员}，{a.岗位}。\n\n## 开工必读\n\n1. 公共仓 `AGENTS.md`。\n2. 公共仓 `01-成员与规则/协作契约.md`。\n3. 本仓 `00-任务包/` 当前任务状态。\n4. 公共仓 `03-交换区/收件箱/{a.成员}/` 的指向消息。\n\n## 可见性\n\n个人仓之间互相不可见；只读自己的个人仓；只通过公共仓交换区收件箱接收内容。\n\n## 写什么\n\n只写本仓；单据正本和收件箱在公共仓交换区；本仓 `05-单据/` 只放副本。公共仓只通过脚本或向统筹提案。\n\n## 收工\n\n更新任务状态、过程记录、当天日志；同步工作台；提交个人仓。\n")
    common.write(target / "09-日志" / f"{common.today()}.md", f"# {common.today()}\n\n## 其他\n\n- 个人仓初始化。\n")
    subprocess.run(["git", "-C", str(target), "init", "-b", "main"], check=False)

    if a.登记:
        roster = common.read(common.ROSTER).splitlines()
        row = f"| {a.成员} | {a.类别} | {a.岗位} | {a.职责} | {a.口径} |"
        out = []
        inserted = False
        for line in roster:
            if line.startswith("| 外圈") and not inserted:
                out.append(row)
                inserted = True
            out.append(line)
        if not inserted:
            out.append(row)
        common.write(common.ROSTER, "\n".join(out) + "\n")
        for box in [common.OUTBOX, common.INBOX]:
            d = box / a.成员
            d.mkdir(parents=True, exist_ok=True)
            (d / ".gitkeep").touch()
        common.write(common.WORKTABLES / f"{a.成员}.md", f"# {a.成员} 的工作台\n\n> 由个人仓任务状态生成；不要手写。\n\n| 任务 | 状态 | 阻塞/在等 | 任务包 | 产出 | 更新 |\n| --- | --- | --- | --- | --- | --- |\n| 暂无任务 | — | — | — | — | — |\n")
        ann = common.PUBLIC / "00-入口" / "公告栏.md"
        s = common.read(ann).rstrip().splitlines()
        s.append(f"| {common.today()} | 新成员 {a.成员} 已登记；建个人仓、出件箱/收件箱、工作台 | 立即 | 全员 |")
        common.write(ann, "\n".join(s) + "\n")
        ok, msg = common.commit_public(f"新成员 {a.成员} 登记")
        if not ok:
            print(f"公共仓提交失败：{msg}")
            return 1

    print(f"已建：{target}")
    print("请设置本仓 git 身份后提交；外部成员请把个人仓放在本人机器上。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
