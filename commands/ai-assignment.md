---
description: AI(ChatGPT 등)로 쉽게 대체될 수 있는 보고서·활동지·수행평가를 H→AI→H 구조로 재설계하는 workflow.
---

# AI-resilient assignment redesign

K-Teacher Skills "ai-resilient-assignment-redesign" workflow를 시작한다.

**Chain:** `ai-resilient-assignment-redesign` → `assessment-first-design` → `to-lesson-brief`
**Default profile:** Deep (threshold 0.15, max 12 rounds)

사용자 요청:
```
$ARGUMENTS
```

## 진행 절차

1. **Round 0:** `skills/ai-era/ai-resilient-assignment-redesign/SKILL.md` 로딩 → Gate v2 banner → topology 잠금.
2. **취약점 진단:** 현재 과제가 AI로 어떻게 대체되는지 시연. AI 탐지 도구 단독 권장 금지.
3. **H→AI→H 재설계:**
   - H (Human first): 학생 본인 생각·경험·맥락 우선 산출물
   - AI (intermediate): 학생이 AI를 도구로 사용하되 프롬프트 로그 첨부
   - H (Human last): SHIFT 성찰지로 AI 산출물의 한계 비판·재구성
4. **과정 평가 비중:** 50% 이상.
5. **평가 증거 설계:** `assessment-first-design`으로 H→AI→H 단계별 학습 증거 정의.
6. **Brief 정리:** `to-lesson-brief` + 학생 안내문 초안.

학생 개인정보 입력 금지 안내 필수. `references/ai-assignment-templates.md` 참조.
