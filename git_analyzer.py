"""
인터랙티브 Git 기반 단일 화면 요건 분석 도구

EXE 패키징 시 주 실행 파일입니다.
"""
import re
import sys
from typing import Dict, List, Optional

from config_parser import ConfigParser
from frontend_analyzer import FrontendAnalyzer
from git_repo_manager_hybrid import HybridGitRepoManager, SmartGitAccessManager
from requirements_excel_generator_v2 import RequirementsExcelGeneratorV2
from screen_requirements_analyzer_v2 import ScreenRequirementsAnalyzerV2


def _safe_filename(value: str) -> str:
    value = value or "result"
    return re.sub(r'[^0-9A-Za-z가-힣_.-]+', '_', value).strip('_') or "result"


class GitAnalyzer:
    """단일 Pod/브랜치/프로그램을 선택하여 요건 Excel을 생성합니다."""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.config_parser = ConfigParser(config_path)
        self.access_manager: Optional[SmartGitAccessManager] = None

    def run_interactive(self) -> bool:
        try:
            print("=" * 60)
            print("🎯 Git 기반 화면 요건 분석 도구")
            print("   (원격-first + 로컬-fallback)")
            print("=" * 60)
            print()

            pods_config = self.config_parser.get_pods()
            if not pods_config:
                print("[ERROR] 설정 파일에 'pods' 항목이 없습니다.")
                return False

            print(f"✓ 설정 파일 로드: {self.config_path}")
            print(f"  - 정의된 Pods: {len(pods_config)}개")
            for pod_key in pods_config.keys():
                print(f"    * {pod_key}")
            print()

            pod_key, pod_config = self._select_pod(pods_config)
            if not pod_key:
                return False

            self.access_manager = SmartGitAccessManager({pod_key: pod_config})
            manager = self.access_manager.get_manager(pod_key)

            branch = self._select_branch(manager)
            if not branch:
                return False

            print("\n📋 프로그램명 입력")
            print("-" * 40)
            program_name = input("프로그램명을 입력하세요 (예: CCTMElectronicFundsTransferStore): ").strip()
            if not program_name:
                print("프로그램명을 입력해주세요.")
                return False

            return self._analyze(pod_key, pod_config, manager, program_name)

        except KeyboardInterrupt:
            print("\n[INFO] 사용자에 의해 중단되었습니다.")
            return False
        except Exception as e:
            print(f"[ERROR] 분석 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            if self.access_manager:
                self.access_manager.cleanup_all()

    def _select_pod(self, pods_config: Dict) -> tuple:
        pod_keys = list(pods_config.keys())
        print("📋 Pod 선택")
        print("-" * 40)
        for i, pod_key in enumerate(pod_keys, 1):
            config = pods_config[pod_key]
            has_remote = 'git' in config and 'remote_url' in config.get('git', {})
            has_local = 'local_fallback' in config
            status = "🌐" if has_remote else "💾" if has_local else "❓"
            screen_name = config.get('screen_name', '')
            print(f"  {i}. {pod_key} {status} {screen_name}")

        while True:
            try:
                choice = input("\nPod 번호를 선택하세요: ").strip()
                idx = int(choice) - 1
                if 0 <= idx < len(pod_keys):
                    selected_key = pod_keys[idx]
                    print(f"✓ 선택된 Pod: {selected_key}")
                    return selected_key, pods_config[selected_key]
                print("유효하지 않은 번호입니다.")
            except ValueError:
                print("숫자를 입력해주세요.")
            except KeyboardInterrupt:
                return None, None

    def _select_branch(self, manager: HybridGitRepoManager) -> Optional[str]:
        print("\n📋 브랜치 선택")
        print("-" * 40)
        branches = manager.get_branches()
        if not branches:
            print("[ERROR] 브랜치를 조회할 수 없습니다.")
            return None

        current_idx = 0
        for i, branch in enumerate(branches):
            marker = " (현재)" if branch.is_current else ""
            remote_marker = " [원격]" if branch.is_remote else ""
            print(f"  {i+1}. {branch.name}{marker}{remote_marker}")
            if branch.is_current:
                current_idx = i

        while True:
            try:
                choice = input(f"\n브랜치 번호를 선택하세요 (기본: {current_idx+1}): ").strip()
                idx = current_idx if not choice else int(choice) - 1
                if 0 <= idx < len(branches):
                    selected_branch = branches[idx]
                    if not selected_branch.is_current:
                        print(f"\n브랜치 전환 중: {selected_branch.name}")
                        if not manager.switch_branch(selected_branch.name):
                            print("[ERROR] 브랜치 전환에 실패했습니다.")
                            return None
                    else:
                        print(f"✓ 현재 브랜치 유지: {selected_branch.name}")
                    return selected_branch.name
                print("유효하지 않은 번호입니다.")
            except ValueError:
                print("숫자를 입력해주세요.")
            except KeyboardInterrupt:
                return None

    def _analyze(self, pod_key: str, pod_config: Dict, manager: HybridGitRepoManager, program_name: str) -> bool:
        base_path = pod_config.get('base_path', '.')
        screen_name = pod_config.get('screen_name') or pod_key

        print("\n🔍 파일 검색 중...")
        files = manager.find_program_files(base_path, program_name)
        print(f"\n[{pod_key}] 발견된 파일: {len(files)}개")
        for f in files:
            print(f"  - [{f.file_type}] {f.file_name}")

        if not files:
            print("[ERROR] 파일을 찾을 수 없습니다.")
            return False

        print("\n📊 파일 분석 중...")
        frontend_analyzer = FrontendAnalyzer()
        file_infos: List[Dict] = []
        for file_info in files:
            parsed = frontend_analyzer.analyze_single_file(file_info.file_name, file_info.content, screen_name)
            if parsed:
                file_infos.append(parsed)

        print("\n🔍 요건 추출 중...")
        analyzer = ScreenRequirementsAnalyzerV2()
        requirements = analyzer.analyze_screen(screen_name, file_infos)

        branch_name = _safe_filename(manager.current_branch or "branch")
        program = _safe_filename(program_name)
        output_file = f"{program}_요건_{branch_name}.xlsx"
        excel_gen = RequirementsExcelGeneratorV2(output_file)
        excel_gen.generate(requirements)

        print(f"\n✅ 분석 완료: {output_file}")
        return True


def main():
    config_path = "config.json"
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    analyzer = GitAnalyzer(config_path)
    success = analyzer.run_interactive()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
