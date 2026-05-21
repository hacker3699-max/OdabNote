# MistakeGuard MCP

AI 에이전트가 저지르는 실수를 방지하고 자가 교정할 수 있도록 돕는 복합적 오답노트 MCP 서버 및 CLI 도구입니다.

## Features

- **오답 RAG 쿼리 (`query_notes`):** 작업 시작 전 키워드 매칭을 통해 연관 과거 오답 정보 로드.
- **오답 자가 학습 (`record_mistake`):** 에러 상황과 올바른 해결법을 가중치(오류 빈도)와 함께 DB에 영속화.
- **CLI 인터페이스 (`incorrect-notes`):** 개발자가 터미널에서 오답노트를 조회, 수동 등록, 승인(Veto) 가능.

## Installation

```bash
uv pip install -e .
```
