"""

하이브리드 Git 저장소 관리자

원격 저장소 → 로컬 fallback 자동 전환

"""

import os

import sys

import tempfile

import shutil

import subprocess

from pathlib import Path

from typing import Optional, List, Dict

from dataclasses import dataclass


 

try:

    import git

    GITPYTHON_AVAILABLE = True

except ImportError:

    GITPYTHON_AVAILABLE = False


 


 

@dataclass

class GitBranch:

    """Git 브랜치 정보"""

    name: str

    is_current: bool = False

    is_remote: bool = False


 


 

class HybridGitRepoManager:

    """

    원격 + 로컬 하이브리드 Git 접근 관리자


 

    시도 순서:

    1. 원격 저장소 clone (remote_url이 설정된 경우)

       - token 인증 포함

       - shallow clone으로 빠른 접근

    2. 실패 시 → local_fallback 경로 사용

    3. 최종 실패 → 예외 발생

    """


 

    def __init__(self, pod_name: str, pod_config: dict):

        """

        Args:

            pod_name: Pod 이름 (CCT, PAY 등)

            pod_config: 설정 파일의 pods.{pod_name} 내용

        """

        self.pod_name = pod_name

        self.pod_config = pod_config

        self.git_repo_path: Optional[Path] = None

        self.repo = None

        self.current_branch: Optional[str] = None

        self.commit_hash: Optional[str] = None

        self.use_remote = False

        self.is_temp_dir = False  # 임시 디렉토리인지 여부 (clone한 경우 True)

        self.error_message = ""


 

        # 접근 모드 초기화

        self._initialize()


 

    def _initialize(self):

        """저장소 접근 초기화 (원격 → 로컬 fallback)"""

        print(f"\n[{self.pod_name}] 저장소 접근 시도 중...")


 

        # 1. 원격 저장소 시도

        remote_config = self.pod_config.get('git', {})

        remote_url = remote_config.get('remote_url')


 

        if remote_url:

            print(f"  [1/2] 원격 저장소 접근 시도: {remote_url}")

            if self._try_remote_access(remote_url, remote_config.get('token')):

                print(f"  ✓ 원격 저장소 접근 성공")

                self.use_remote = True

                return

            else:

                print(f"  ⚠️  원격 접근 실패: {self.error_message}")


 

        # 2. 로컬 fallback 시도

        local_path = self.pod_config.get('local_fallback')

        if local_path:

            print(f"  [2/2] 로컬 저장소 fallback: {local_path}")

            if self._try_local_access(local_path):

                print(f"  ✓ 로컬 저장소 접근 성공")

                self.use_remote = False

                return

            else:

                print(f"  ⚠️  로컬 접근 실패: {self.error_message}")


 

        # 3. 모두 실패

        raise Exception(f"저장소 접근 실패: 원격 및 로컬 모두 접근 불가")


 

    def _try_remote_access(self, remote_url: str, token: Optional[str]) -> bool:

        """원격 저장소 clone 및 접근"""

        try:

            # token이 ${VAR} 형식이면 환경변수에서 읽기

            if token and token.startswith('${') and token.endswith('}'):

                env_var = token[2:-1]

                token = os.environ.get(env_var)

                if not token:

                    print(f"    ⚠️  환경변수 {env_var}가 설정되지 않았습니다.")


 

            # token이 있으면 URL에 포함

            auth_url = remote_url

            if token:

                # https://github.com/user/repo.git → https://token@github.com/user/repo.git

                if remote_url.startswith('https://'):

                    auth_url = remote_url.replace('https://', f'https://{token}@')

                elif remote_url.startswith('http://'):

                    auth_url = remote_url.replace('http://', f'http://{token}@')


 

            # 임시 디렉토리 생성

            temp_dir = Path(tempfile.mkdtemp(prefix=f"git_remote_{self.pod_name}_"))

            self.git_repo_path = temp_dir

            self.is_temp_dir = True


 

            print(f"    클론 위치: {temp_dir}")


 

            # GitPython으로 clone

            if GITPYTHON_AVAILABLE:

                try:

                    self.repo = git.Repo.clone_from(

                        auth_url,

                        temp_dir,

                        depth=1,  # shallow clone

                        single_branch=True,

                        branch='HEAD'  # 기본 브랜치

                    )

                except git.GitCommandError as e:

                    # GitPython 실패 시 CLI 시도

                    self.repo = None

                    raise e

            else:

                # CLI로 clone

                cmd = ['git', 'clone', '--depth', '1', auth_url, str(temp_dir)]

                result = subprocess.run(

                    cmd,

                    capture_output=True,

                    text=True,

                    encoding='utf-8',

                    errors='ignore',

                    timeout=300

                )

                if result.returncode != 0:

                    raise Exception(f"git clone failed: {result.stderr}")


 

            # clone 성공

            self.repo = git.Repo(temp_dir) if GITPYTHON_AVAILABLE else None

            self.current_branch = self._get_current_branch_cli(temp_dir)

            self.commit_hash = self._get_current_hash_cli(temp_dir)

            return True


 

        except Exception as e:

            self.error_message = str(e)

            # 임시 디렉토리 정리

            if self.git_repo_path and self.git_repo_path.exists():

                try:

                    shutil.rmtree(self.git_repo_path)

                except:

                    pass

            return False


 

    def _try_local_access(self, local_path: str) -> bool:

        """로컬 저장소 접근"""

        try:

            path = Path(local_path).resolve()

            if not path.exists():

                self.error_message = f"Path not found: {path}"

                return False


 

            if not (path / '.git').exists():

                self.error_message = f"Not a Git repository: {path}"

                return False


 

            # GitPython으로 열기

            if GITPYTHON_AVAILABLE:

                try:

                    self.repo = git.Repo(path)

                    self.current_branch = self.repo.active_branch.name

                    self.commit_hash = self.repo.head.commit.hexsha[:8]

                except Exception as e:

                    raise Exception(f"GitPython failed: {e}")

            else:

                # CLI로 확인

                self.current_branch = self._get_current_branch_cli(path)

                self.commit_hash = self._get_current_hash_cli(path)


 

            self.git_repo_path = path

            self.is_temp_dir = False

            return True


 

        except Exception as e:

            self.error_message = str(e)

            return False


 

    def _get_current_branch_cli(self, repo_path: Path) -> Optional[str]:

        """CLI로 현재 브랜치 조회"""

        try:

            result = subprocess.run(

                ['git', 'branch', '--show-current'],

                cwd=repo_path,

                capture_output=True,

                text=True,

                encoding='utf-8',

                errors='ignore'

            )

            if result.returncode == 0:

                branch = result.stdout.strip()

                if branch:

                    return branch


 

            # detached state인 경우

            result2 = subprocess.run(

                ['git', 'rev-parse', 'HEAD'],

                cwd=repo_path,

                capture_output=True,

                text=True,

                encoding='utf-8',

                errors='ignore'

            )

            if result2.returncode == 0:

                commit = result2.stdout.strip()[:8]

                return f"DETACHED_{commit}"

        except:

            pass

        return None


 

    def _get_current_hash_cli(self, repo_path: Path) -> Optional[str]:

        """CLI로 현재 commit hash 조회"""

        try:

            result = subprocess.run(

                ['git', 'rev-parse', 'HEAD'],

                cwd=repo_path,

                capture_output=True,

                text=True,

                encoding='utf-8',

                errors='ignore'

            )

            if result.returncode == 0:

                return result.stdout.strip()[:8]

        except:

            pass

        return None


 

    def get_branches(self) -> List[GitBranch]:

        """모든 브랜치 목록 조회"""

        branches = []


 

        if not self.git_repo_path:

            return branches


 

        try:

            # CLI로 브랜치 목록 조회 (원격/로컬 모두)

            result = subprocess.run(

                ['git', 'branch', '-a'],

                cwd=self.git_repo_path,

                capture_output=True,

                text=True,

                encoding='utf-8',

                errors='ignore'

            )


 

            if result.returncode == 0:

                current_branch = self.current_branch or ''


 

                for line in result.stdout.split('\n'):

                    line = line.strip()

                    if not line:

                        continue


 

                    is_current = line.startswith('* ')

                    branch_name = line[2:] if is_current else line


 

                    # (detached) 제외

                    if '(' in branch_name and 'detached' in branch_name.lower():

                        continue


 

                    # 원격 브랜치 표시 처리

                    is_remote = branch_name.startswith('remotes/') or 'origin/' in branch_name

                    clean_name = branch_name.replace('remotes/', '').replace('origin/', '')


 

                    branches.append(GitBranch(

                        name=clean_name,

                        is_current=(clean_name == current_branch) or is_current,

                        is_remote=is_remote

                    ))

        except Exception as e:

            print(f"[ERROR] branch listing failed: {e}")


 

        # 중복 제거 및 정렬

        unique = {}

        for b in branches:

            if b.name not in unique:

                unique[b.name] = GitBranch(

                    name=b.name,

                    is_current=b.is_current,

                    is_remote=b.is_remote

                )


 

        return sorted(unique.values(), key=lambda x: (x.is_remote, x.name))


 

    def switch_branch(self, branch_name: str) -> bool:

        """브랜치 전환"""

        if not self.git_repo_path:

            return False


 

        try:

            # 원격 브랜치인지 확인

            cmd = ['git', 'checkout', branch_name]

            result = subprocess.run(

                cmd,

                cwd=self.git_repo_path,

                capture_output=True,

                text=True,

                encoding='utf-8',

                errors='ignore'

            )


 

            if result.returncode == 0:

                self.current_branch = branch_name

                # commit hash 업데이트

                self.commit_hash = self._get_current_hash_cli(self.git_repo_path)

                print(f"    ✓ 전환 완료: {self.current_branch} ({self.commit_hash})")

                return True

            else:

                print(f"    ✗ 전환 실패: {result.stderr}")

                return False

        except Exception as e:

            print(f"    ✗ 전환 오류: {e}")

            return False


 

    def read_file_content(self, file_path: str) -> Optional[str]:

        """

        Git 객체에서 파일 내용 읽기


 

        Args:

            file_path: 저장소 내 상대 경로


 

        Returns:

            파일 내용 또는 None

        """

        if not self.git_repo_path:

            return None


 

        try:

            normalized_path = file_path.replace('\\', '/').lstrip('/')


 

            # git show 명령어 사용 (.git/objects에서 직접 읽음)

            cmd = ['git', 'show', f'{self.current_branch}:{normalized_path}']

            result = subprocess.run(

                cmd,

                cwd=self.git_repo_path,

                capture_output=True,

                text=True,

                encoding='utf-8',

                errors='ignore'

            )


 

            if result.returncode == 0:

                return result.stdout

            else:

                # 파일이 이 브랜치에 없음

                return None

        except Exception as e:

            print(f"[ERROR] 파일 읽기 실패: {file_path} - {e}")

            return None


 

    def find_program_files(self, base_path: str, program_name: str) -> List:

        """Git 저장소에서 프로그램 파일 검색"""

        from pathlib import Path

        import os


 

        # Git tree-traverse로 파일 찾기

        try:

            # git ls-tree 명령으로 전체 파일 목록 조회

            cmd = ['git', 'ls-tree', '-r', '--name-only', self.current_branch]

            result = subprocess.run(

                cmd,

                cwd=self.git_repo_path,

                capture_output=True,

                text=True,

                encoding='utf-8',

                errors='ignore'

            )


 

            if result.returncode != 0:

                return []


 

            all_files = result.stdout.strip().split('\n')


 

            # base_path로 필터링

            base_norm = base_path.replace('\\', '/').rstrip('/')

            if base_norm != '.' and not base_norm:

                base_norm = '.'


 

            matches = []

            patterns = [

                f"{program_name}.js",

                f"{program_name}.clx",

                f"{program_name.upper()}.js",

                f"{program_name.upper()}.clx",

                f"{program_name.lower()}.js",

                f"{program_name.lower()}.clx",

            ]


 

            for file_path in all_files:

                if base_norm != '.' and not file_path.startswith(base_norm):

                    continue


 

                file_name = os.path.basename(file_path)

                if any(pattern.lower() in file_name.lower() for pattern in patterns):

                    # 파일 내용 읽기

                    content = self.read_file_content(file_path)

                    if content is not None:

                        file_ext = os.path.splitext(file_name)[1].lower()[1:]

                        file_type = 'js' if file_ext == 'js' else 'clx' if file_ext == 'clx' else 'unknown'


 

                        # FileInfo-like object 생성

                        from collections import namedtuple

                        FileInfo = namedtuple('FileInfo', ['file_name', 'relative_path', 'content', 'file_type'])

                        relative_path = os.path.relpath(file_path, base_norm) if base_norm != '.' else file_path

                        matches.append(FileInfo(

                            file_name=file_name,

                            relative_path=relative_path,

                            content=content,

                            file_type=file_type

                        ))


 

            return matches


 

        except Exception as e:

            print(f"[ERROR] Git search failed: {e}")

            return []


 

    def cleanup(self):

        """리소스 정리 (임시 디렉토리 삭제)"""

        if self.is_temp_dir and self.git_repo_path and self.git_repo_path.exists():

            try:

                shutil.rmtree(self.git_repo_path)

                print(f"[DEBUG] 임시 디렉토리 삭제: {self.git_repo_path}")

            except Exception as e:

                print(f"[WARN] 임시 디렉토리 삭제 실패: {e}")


 

    def __del__(self):

        """소멸자에서 정리"""

        self.cleanup()


 


 

class SmartGitAccessManager:

    """

    여러 Pod에 대한 스마트 Git 접근 관리자

    """


 

    def __init__(self, pods_config: dict):

        self.pods_config = pods_config

        self.managers: Dict[str, HybridGitRepoManager] = {}


 

    def get_manager(self, pod_name: str) -> HybridGitRepoManager:

        """Pod에 대한 manager 획득 (싱글턴)"""

        if pod_name not in self.managers:

            config = self.pods_config.get(pod_name)

            if not config:

                raise ValueError(f"Pod '{pod_name}' not found in config")

            self.managers[pod_name] = HybridGitRepoManager(pod_name, config)


 

        return self.managers[pod_name]


 

    def cleanup_all(self):

        """모든 manager 정리"""

        for manager in self.managers.values():

            manager.cleanup()


 


 

if __name__ == "__main__":

    # 테스트 코드

    import json


 

    test_config = {

        "CCT": {

            "git": {

                "remote_url": "https://github.com/yourorg/cbh_cct_frt.git",

                "token": "${GIT_TOKEN}"

            },

            "local_fallback": "C:/develop/repository/git/cbh_cct_frt",

            "base_path": "clx-src/cbhcct/prmumdep"

        }

    }


 

    manager = HybridGitRepoManager("CCT", test_config["CCT"])

    print(f"Access mode: {'REMOTE' if manager.use_remote else 'LOCAL'}")

    print(f"Branch: {manager.current_branch}")

    print(f"Commit: {manager.commit_hash}")

    print(f"Path: {manager.git_repo_path}")


 

    # 테스트 파일 검색

    files = manager.find_program_files("clx-src/cbhcct/prmumdep", "CCTMDeathBenefitScrtz")

    print(f"Found {len(files)} files")

    for f in files[:3]:

        print(f"  - {f.file_name} ({f.file_type})")


 

    manager.cleanup()
