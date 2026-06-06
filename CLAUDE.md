# CLAUDE.md — trading-browser-agent-lab

이 repo에서 작업하는 모든 에이전트(Claude Code 등)가 반드시 지키는 규칙.

## 1. 범위: research-only

- 이 repo는 **연구 전용(research-only)** 입니다.
- **금지**: 매매 실행, 주문 생성, 증권사 연동, 실거래 API 호출.
- 백테스트 / 분석 / 프레임워크 검증만 허용됩니다.

## 2. 정본 spec 위치 (vault) — 읽기 전용

- 정본 spec은 vault에 있습니다:
  `C:\Users\Daniek\OneDrive\문서\Claude\Projects\Trading\Trading\AI_STOCK_Agent\Reports\special-reports\p1-framework-backtest-lab-spec.md`
- **vault는 읽기 전용**입니다. 어떤 에이전트도 vault에 쓰기 금지.
- vault에 쓰는 행위자가 늘어나면 STATUS.md 세션 프로토콜 밖의 충돌원이 됩니다.

## 3. 쓰기 경계

- Claude Code는 **이 repo 폴더만 쓰기** 가능합니다
  (`%USERPROFILE%\trading-browser-agent-lab`).
- vault, 기타 로컬 경로는 읽기 전용으로만 접근하세요.

## 4. 보호 파일 — 수정 절대 금지

- `special-reports/yin-yun-breakthrough-framework-v2-2026-05-07.md`
- 무결성 기준:
  - sha256 prefix: `7fc94586eb4b3a0c`
  - lines: `310`
  - bytes: `16,395`
- 이 파일은 어떤 이유로도 수정/재포맷/줄바꿈 변경 금지.

## 5. 산출물 규칙

- 모든 산출물에 **한자 사용 금지**. 영어 / 한글만 사용.
