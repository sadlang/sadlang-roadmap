# 📊 الحالة (Status)

- [kanban.md](kanban.md) — اللوحة المركزيّة (To Do → In Progress → Review → Done).
- [roadmap-status.yaml](roadmap-status.yaml) — الحالة القابلة للقراءة آليًّا (المصدر للتجميع والتحقّق).
- [weekly-sync.md](weekly-sync.md) — قالب محضر المزامنة الأسبوعيّة.

## التحديث
- البطاقات تتحرّك يدويًّا في `kanban.md` ومرآتها في `roadmap-status.yaml`.
- `scripts/validate_roadmap.py` يفشل CI إذا تعارضت البطاقات مع المراحل/المعالم/الفِرَق.
- لا تُعلَّم مهمّة `done` بلا دليل بناء/اختبار (GR-01).
