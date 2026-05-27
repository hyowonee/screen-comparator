# 화면 코드 비교 분석 도구 (Git 기반)


 

두 개의 독립된 화면(A, B)의 프론트엔드(.js, .clx) 코드를 **Git 저장소의 실시간 상태**에서 분석하여, 업무 기능 차이를 비교하고 결과를 Excel 파일로 출력하는 도구입니다.


 

## 🆕 주요 기능 (Git 연동)


 

- **Git 객체 직접 접근**: 로컬 작업 디렉토리가 아닌 `.git/objects`에서 파일을 읽어 정확한 버전 분석

- **인터랙티브 브랜치 선택**: 저장소의 모든 브랜치(로컬/원격) 목록에서 선택 가능

- **실시간 파일 검색**: 선택된 브랜치의 커밋된 상태에서 프로그램 파일 자동 검색

- **Fallback 모드**: Git 접근 실패 시 로컬 파일 시스템으로 자동 전환


 

## 📋 요구사항


 

- Python 3.8+

- `openpyxl` (Excel 생성)

- `GitPython` (Git 접근)


 

## 📦 설치 방법


 

```bash

# 의존성 설치

pip install -r requirements.txt

```


 

## 🚀 사용 방법


 

### 1. 설정 파일 준비


 

`config.json` 파일을 프로젝트 구조에 맞게 수정합니다:


 

**새로운 Pods 기반 형식 (권장)**:

```json

{

  "pods": {

    "CCT": {

      "git": {

        "remote_url": "https://github.com/yourorg/cbh_cct_frt.git",

        "token": "${GIT_TOKEN}"

      },

      "local_fallback": "C:/develop/repository/git/cbh_cct_frt",

      "base_path": "clx-src/cbhcct/policy",

      "screen_name": "CCT 화면"

    },

    "PAY": {

      "git": {

        "remote_url": "https://github.com/yourorg/cbh_pay_frt.git",

        "token": "${GIT_TOKEN}"

      },

      "local_fallback": "C:/develop/repository/git/cbh_pay_frt",

      "base_path": "clx-src/cbhpay/annuity",

      "screen_name": "PAY 화면"

    }

  },

  "backend": {

    "search_paths": [

      "C:/develop/repository/git/cbh_cct_bnd/src/main/java/kr/co/kblife",

      "C:/develop/repository/git/cbh_pay_bnd/src/main/java/kr/co/kblife"

    ]

  }

}

```


 

**기존 screens 형식 (호환)**:

```json

{

  "screens": [

    {

      "name": "CCT 화면",

      "frontend": {

        "base_path": "C:/develop/repository/git/cbh_cct_frt/clx-src/cbhcct/policy",

        "files": ["CCTMDeathBenefitScrtz"]

      }

    }

  ],

  "backend": {...}

}

```


 

**주의**: `base_path`는 **Git 저장소 내부 경로**여야 합니다. 저장소 루트를 기준으로 한 상대 경로를 지정하세요.


 

### 2. 실행


 

```bash

# 대화형 모드 (Git 브랜치 선택, 프로그램 입력)

python main.py


 

# 다른 설정파일 사용

python main.py config_cct.json


 

# 단일 화면 상세 분석 (요건 분석)

# 이 모드는 config.json 없이 프로그램명만 입력받음

python git_analyzer.py

```


 

### 3. 인터랙티브 단계


 

도구는 다음 단계를 안내합니다:


 

1. **Pod 선택**: 설정파일에 정의된 Pod 목록에서 선택

2. **브랜치 선택**: 해당 저장소의 모든 브랜치(로컬/원격) 목록에서 선택

3. **프로그램명 입력**: 분석할 프로그램명 입력 (예: `CCTMElectronicFundsTransferStore`)

4. **파일 검색**: Git 저장소에서 `.js`, `.clx` 파일 자동 검색 및 미리보기

5. **요건 분석**: 두 파일을 함께 분석하여 상세 Excel 리포트 생성


 

## 📊 출력 결과


 

요건 분석 시 `프로그램NAME_요건_브랜치명.xlsx` 파일이 생성되며, 다음 6개 시트로 구성됩니다:


 

### 시트 1: 요약

- 총 규칙 수, 함수 수, UI 요소 수

- 카테고리별 분포


 

### 시트 2: 규칙상세

- 모든 추출된 조건/규칙 상세 목록

- 사용자 요건, 기술적 조건, 액션, UI 요소 연결, API 호출 정보


 

### 시트 3: UI요소

- 화면의 모든 UI 필드(input, grid, combobox 등)

- 사용된 규칙, 참조 함수


 

### 시트 4: 함수목록

- 모든 함수 목록과 API 호출 정보


 

### 시트 5: 요건매트릭스

- UI 요소 × 요건 카테고리 매트릭스


 

### 시트 6: 작업흐름

- 카테고리별 그룹된 사용자 요건


 

## 🔍 분석 항목


 

### 조건문 추출

- `if/else if` 조건문

- `switch-case` 문

- 3항 연산자


 

### 검증 규칙

- `util.validateXXX()` 호출

- 커스텀 검증 함수


 

### 상태 관리

- `rdbProcOption.value` 설정/조회

- `dsTempSaveYn` 상태 관리

- 탭 인덱스 변경


 

### 탭 전환

- `onTabXSelectionChange` 핸들러

- 탭 초기화 함수


 

### API 호출

- `util.Submit.send()` URL 추출

- `$http`, `axios` 호출


 

### 초기화 로직

- `onTabXInit`

- `onPageInit`

- 데이터 로드 함수


 

## 📁 파일 구조


 

```

screen-comparator/

├── main.py                      # Git 기반 비교 분석 진입점 (deprecated, git_analyzer.py 권장)

├── git_analyzer.py              # 인터랙티브 Git 기반 분석기 (주력)

├── git_compare_analyzer.py      # 두 화면 비교 (Git 연동)

├── frontend_analyzer.py         # 프론트엔드 정적 분석 (JS/CLX)

├── screen_requirements_analyzer_v2.py  # 상세 요건 추출

├── requirements_excel_generator_v2.py  # 요건 Excel 생성

├── matcher.py                   # 프론트-백엔드 매칭

├── excel_generator.py           # 비교 결과 Excel 생성

├── config_parser.py             # 설정 파일 파싱

├── backend_analyzer.py          # 백엔드 Java 분석

├── requirements.txt             # Python 의존성

├── config.json                  # 설정 파일 (사용자 작성)

└── README.md                    # 본 문서

```


 

## ⚙️ Git 접근 방식 (하이브리드)


 

도구는 **원격-first, 로컬-fallback** 전략을 사용합니다:


 

### 1. 원격 저장소 직접 접근 (우선 시도)


 

```text

config.json →

  "git": {

    "remote_url": "https://github.com/company/repo.git",

    "token": "${GIT_TOKEN}"

  }

```


 

작동 방식:

- `git clone --depth=1`로 임시 디렉토리에클론

- Git Python 또는 CLI로 파일 읽기 (`.git/objects` 직접 접근)

- **장점**: 최신 코드 실시간 분석

- **필요**: 환경변수 `GIT_TOKEN` 설정 (비공개 저장소인 경우)


 

### 2. 로컬 저장소 Fallback (원격 실패 시)


 

```text

config.json →

  "local_fallback": "C:/develop/repository/git/cbh_cct_frt"

```


 

작동 방식:

- 원격 접근 실패 시 자동으로 전환

- 로컬 clone된 저장소에서 직접 파일 읽기

- **장점**: 네트워크/인증 문제 없음, 빠름

- **필요**: 로컬에 이미 clone된 저장소 경로


 

### 환경변수 설정 (Git 토큰)


 

```bash

# Windows (PowerShell)

$env:GIT_TOKEN="ghp_your_token_here"


 

# Windows (CMD)

set GIT_TOKEN=ghp_your_token_here


 

# Linux/Mac

export GIT_TOKEN=ghp_your_token_here

```


 

**참고**: `${GIT_TOKEN}`은 환경변수로 자동 치환됩니다.


 

## 🛠️ Fallback 기능


 

Git 접근에 실패한 경우(권한 문제, 손상된 저장소 등) 자동으로 로컬 파일 시스템으로 대체됩니다:

- 설정파일의 `local_fallback` 경로 사용

- 또는 `base_path`에서 직접 파일 읽기

- 사용자에게Fallback 상태가 명시적으로 알림


 

## 🔧 문제 해결


 

### "Git 접근 실패" 메시지

- 로컬 `.git` 디렉토리에 읽기 권한이 있는지 확인

- 저장소가 정상적인지 `git log` 실행으로 테스트


 

### 파일을 찾을 수 없음

- `base_path`가 Git 저장소 루트를 기준으로 한 올바른 상대 경로인지 확인

- 프로그램명이 파일명에 정확히 포함되는지 확인 (대소문자 무시)


 

### 브랜치가 보이지 않음

- `git branch -a` 명령어로 브랜치 목록 확인

- 원격 브랜치를 로컬에 fetching 필요성


 

## 📝 사용 팁


 

1. **프로그램명**: 파일명과 확장자를 제외한 이름 (예: `CCTMElectronicFundsTransferStore.js` → `CCTMElectronicFundsTransferStore`)

2. **대소문자**: 파일명 검색은 대소문자를 구분하지 않습니다.

3. **브랜치 선택**: 기본값은 현재 체크아웃된 브랜치입니다.

4. **Excel 파일**: 자동으로 프로그램명과 브랜치명이 포함된 이름으로 생성됩니다.


 

## 📄 라이선스


 

이 프로젝트는 내부 분석 도구로 제작되었습니다.
