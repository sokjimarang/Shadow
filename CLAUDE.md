# Shadow 프로젝트 가이드

## Git 브랜치 전략: GitHub Flow

이 프로젝트는 **GitHub Flow**를 사용합니다. 소규모 프로젝트와 지속적 배포에 적합한 가장 대중적인 전략입니다.

### 브랜치 규칙

1. **main 브랜치는 항상 배포 가능한 상태 유지**
2. **새 작업은 main에서 feature 브랜치 생성**
   - 네이밍: `feature/<기능명>`, `fix/<버그명>`, `refactor/<대상>`
3. **작은 단위로 자주 커밋**
4. **PR을 통해 main에 병합**
5. **병합 후 feature 브랜치 삭제**

### 브랜치 예시

```
main
├── feature/rest-api
├── feature/qwen-backend
├── fix/memory-leak
└── refactor/error-handling
```

### 참고
- [GitHub Flow Guide](https://docs.github.com/en/get-started/quickstart/github-flow)
- [Git Branching Strategies](https://graphite.com/guides/git-branching-strategies)
