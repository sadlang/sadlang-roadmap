#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""مدقّق اتّساق خارطة الطريق الفيدراليّة (sadlang-roadmap).

يفرض قواعد منع التشتّت آليًّا (GOVERNANCE.md + schema/README.md). يفشل (خروج != 0)
عند أيّ مخالفة، فيوقف CI. لا يعتمد إلا على المكتبة القياسيّة (تحليل frontmatter يدويّ).

الاستعمال:  python scripts/validate_roadmap.py
"""
from __future__ import annotations
import os
import re
import sys

# فرض UTF-8 على المخرجات (كونسول ويندوز قد يكون cp125x فيفشل مع العربيّة/الإيموجي).
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASK_STATES = {"todo", "in-progress", "review", "done", "blocked"}
MILESTONE_STATES = {"planned", "in-progress", "done", "blocked"}
ACTIVE_STATES = {"in-progress", "review", "done"}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def read_frontmatter(path: str) -> dict | None:
    """يقرأ كتلة YAML البسيطة بين --- و--- (مفتاح: قيمة لكل سطر)."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return None
    data: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.split("#", 1)[0].rstrip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        data[key.strip()] = val.strip().strip("'\"")
    data["__body__"] = text[m.end():]
    return data


def yaml_scalar(path: str, key: str) -> str | None:
    """استخراج بسيط لقيمة مفتاح عُلويّ من ملفّ YAML (يكفي لـcurrent_phase)."""
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.split("#", 1)[0].rstrip()
            if s.startswith(key + ":"):
                return s.partition(":")[2].strip().strip("'\"")
    return None


def collect_repos() -> set[str]:
    repos: set[str] = set()
    p = os.path.join(ROOT, "teams", "teams.yaml")
    if not os.path.exists(p):
        err("teams/teams.yaml مفقود")
        return repos
    with open(p, encoding="utf-8") as f:
        for line in f:
            m = re.search(r"repos:\s*\[(.*?)\]", line)
            if m:
                for r in m.group(1).split(","):
                    r = r.strip()
                    if r:
                        repos.add(r)
    return repos


def collect_milestones() -> set[str]:
    ids: set[str] = set()
    mdir = os.path.join(ROOT, "milestones")
    for name in os.listdir(mdir):
        if not name.startswith("M-") or not name.endswith(".md"):
            continue
        fm = read_frontmatter(os.path.join(mdir, name))
        if fm is None:
            err(f"milestones/{name}: لا frontmatter")
            continue
        mid = fm.get("id", "")
        if not mid.startswith("M-"):
            err(f"milestones/{name}: id غير صالح ({mid!r})")
        for field in ("phase", "status", "owner", "target"):
            if not fm.get(field):
                err(f"milestones/{name}: الحقل '{field}' إلزاميّ")
        if fm.get("status") and fm["status"] not in MILESTONE_STATES:
            err(f"milestones/{name}: حالة غير مسموحة ({fm['status']})")
        if "معيار الإنجاز" not in fm.get("__body__", ""):
            warn(f"milestones/{name}: لا قسم «معيار الإنجاز (DoD)»")
        ids.add(mid)
    return ids


def validate_tasks(repos: set[str], milestones: set[str], current_phase: int) -> None:
    tdir = os.path.join(ROOT, "tasks")
    for name in os.listdir(tdir):
        if not (name.startswith("TASK-") and name.endswith(".md")):
            continue
        fm = read_frontmatter(os.path.join(tdir, name))
        if fm is None:
            err(f"tasks/{name}: لا frontmatter")
            continue
        ctx = f"tasks/{name}"
        if not re.match(r"^TASK-\d{4}$", fm.get("id", "")):
            err(f"{ctx}: id يجب أن يكون TASK-NNNN")
        # المرحلة
        try:
            phase = int(fm.get("phase", ""))
            if phase < 0 or phase > 5:
                err(f"{ctx}: phase خارج 0..5")
            elif phase > current_phase:
                err(f"{ctx}: phase={phase} > المرحلة المفتوحة {current_phase} (قاعدة 4: لا ميزات مستقبليّة)")
        except ValueError:
            err(f"{ctx}: phase ليس عددًا")
        # المعلم
        if fm.get("milestone") not in milestones:
            err(f"{ctx}: milestone {fm.get('milestone')!r} غير موجود")
        # المستودع
        if fm.get("repo") not in repos:
            err(f"{ctx}: repo {fm.get('repo')!r} غير معرّف في teams.yaml")
        if "," in fm.get("repo", "") or " " in fm.get("repo", "").strip():
            err(f"{ctx}: مستودع واحد فقط مسموح (قاعدة 2)")
        # الحالة
        status = fm.get("status", "")
        if status not in TASK_STATES:
            err(f"{ctx}: status غير مسموح ({status})")
        # التقدير
        try:
            est = int(fm.get("estimate_days", ""))
            if est < 2 or est > 5:
                err(f"{ctx}: estimate_days={est} خارج [2,5] (قاعدة 5)")
        except ValueError:
            err(f"{ctx}: estimate_days مفقود/غير عددّي")
        # القفل والمسؤول عند التفعيل
        if status in ACTIVE_STATES:
            assignee = fm.get("assignee", "")
            if not assignee or assignee == "غير مُعيَّن":
                err(f"{ctx}: مهمّة '{status}' تحتاج assignee")
            rfc = fm.get("rfc", "")
            if not rfc or rfc.startswith("<"):
                err(f"{ctx}: مهمّة '{status}' تحتاج rfc (قفل)")


def main() -> int:
    status_path = os.path.join(ROOT, "status", "roadmap-status.yaml")
    cp_raw = yaml_scalar(status_path, "current_phase") if os.path.exists(status_path) else None
    if cp_raw is None:
        err("status/roadmap-status.yaml: current_phase مفقود")
        current_phase = 5
    else:
        current_phase = int(cp_raw)

    repos = collect_repos()
    milestones = collect_milestones()
    validate_tasks(repos, milestones, current_phase)

    for w in warnings:
        print(f"⚠️  {w}")
    if errors:
        for e in errors:
            print(f"❌ {e}")
        print(f"\nفشل التحقّق: {len(errors)} مخالفة، {len(warnings)} تحذير.")
        return 1
    print(f"✅ خارطة الطريق متّسقة (المرحلة المفتوحة={current_phase}، "
          f"{len(milestones)} معلم، {len(repos)} مستودع). تحذيرات: {len(warnings)}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
