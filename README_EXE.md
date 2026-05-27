# Windows EXE 빌드/배포 안내

## 빌드

```bat
build_exe.bat
```

또는 직접 실행:

```bat
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller screen-comparator.spec
```

## 배포 파일

빌드 후 아래 두 파일을 같은 폴더에 두고 사용자에게 전달하세요.

- `dist\screen-comparator.exe`
- `config.json`

## 실행

```bat
screen-comparator.exe
```

비공개 Git 저장소 접근이 필요하면 실행 전 토큰을 설정하세요.

```bat
set GIT_TOKEN=ghp_your_token_here
screen-comparator.exe
```

PowerShell:

```powershell
$env:GIT_TOKEN="ghp_your_token_here"
.\screen-comparator.exe
```

## 주의

현재 Git 접근은 GitPython과 시스템 `git.exe` 명령을 함께 사용합니다. 대상 PC에서 원격 clone 또는 브랜치 전환을 하려면 Git for Windows 설치가 필요할 수 있습니다.
