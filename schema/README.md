# 📐 المخطّطات (Schema)

العقد الذي يفرضه [`scripts/validate_roadmap.py`](../scripts/validate_roadmap.py). يطابق ثقافة لغة ص
(`language-truth/` + مولّدات + linter الـRFC): الحقيقة محدّدة آليًّا، لا أعرافًا شفهيّة.

## بطاقة مهمّة (`tasks/TASK-*.md` — frontmatter)
| الحقل | إلزاميّ | القيد |
|------|---------|------|
| `id` | ✅ | `TASK-` + 4 أرقام |
| `phase` | ✅ | عدد 0..5، **≤ current_phase** |
| `milestone` | ✅ | `M-*` موجود في `milestones/` |
| `repo` | ✅ | مستودع **واحد** مذكور في `teams/teams.yaml` |
| `team` | ✅ | فريق موجود |
| `assignee` | ✅ | (قد يكون «غير مُعيَّن» في `todo` فقط) |
| `status` | ✅ | `todo\|in-progress\|review\|done\|blocked` |
| `rfc` | ✅ | قفل RFC (مطلوب قبل `in-progress`) |
| `estimate_days` | ✅ | عدد 2..5 |

## معلم (`milestones/M-*.md` — frontmatter)
`id` (`M-*`), `phase` (0..5), `status` (`planned\|in-progress\|done\|blocked`),
`owner`, `target` — كلها إلزاميّة. ويجب وجود قسم «معيار الإنجاز (DoD)».

## قواعد متقاطعة (يفرضها المدقّق)
1. لا مهمّة بـ`phase > current_phase` (منع الميزات المستقبليّة — قاعدة 4).
2. كل `milestone` و`repo` و`team` في بطاقة موجود فعلًا.
3. `estimate_days ∈ [2,5]` (قاعدة 5).
4. مهمّة `in-progress`/`review`/`done` لها `assignee` و`rfc` غير فارغين.
5. `current_phase` في `roadmap-status.yaml` يطابق المرحلة المفتوحة في `ROADMAP.md`.
