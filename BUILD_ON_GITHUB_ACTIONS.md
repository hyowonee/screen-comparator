# Windows EXE 자동 빌드 방법

반입하려는 PC에 Python 설치가 불가능한 경우, 이 프로젝트를 GitHub 저장소에 올린 뒤 GitHub Actions에서 Windows용 EXE를 만들 수 있습니다.

## 1. GitHub 저장소에 업로드

이 폴더의 전체 내용을 GitHub 저장소에 올립니다.

## 2. Actions 실행

GitHub 저장소 화면에서:

1. `Actions` 탭 클릭
2. `Build Windows EXE` 선택
3. `Run workflow` 클릭
4. 완료될 때까지 대기

## 3. 결과물 다운로드

Workflow가 완료되면 하단의 `Artifacts`에서 `screen-comparator-windows-exe`를 다운로드합니다.

압축 안에는 다음 파일이 들어 있습니다.

```text
screen-comparator.exe
config.json
README_EXE.md
```

## 4. 반입 PC에서 실행

반입 PC에서는 Python 설치가 필요 없습니다.

```text
screen-comparator.exe
config.json
```

두 파일을 같은 폴더에 두고 `screen-comparator.exe`를 실행하세요.

## 주의

- 원격 Git 저장소를 분석하려면 반입 PC에 Git이 설치되어 있어야 할 수 있습니다.
- Git 설치가 불가능한 PC라면 `config.json`의 `local_fallback`에 이미 복사된 로컬 저장소 경로를 지정하거나, 코드에서 Git CLI 의존성을 제거해야 합니다.
- 사내망/폐쇄망 PC에서는 원격 clone이 막힐 수 있으므로 로컬 저장소 방식이 더 안정적입니다.
