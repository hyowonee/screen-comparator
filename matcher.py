"""

프론트엔드와 백엔드 매칭 모듈

"""

from typing import List, Dict, Any, Tuple

from backend_analyzer import BackendAPI

from dataclasses import dataclass


 


 

@dataclass

class MatchedFeature:

    """매칭된 기능"""

    api_path: str

    frontend_functions: List[Dict[str, Any]]

    backend_apis: List[BackendAPI]

    match_type: str  # 'exact', 'prefix', 'none'


 


 

class ScreenMatcher:

    """화면 매처"""


 

    def __init__(self, screen_configs: List[Dict[str, Any]]):

        """

        Args:

            screen_configs: 화면 설정 목록 (name, frontend.base_path, frontend.files)

        """

        self.screen_configs = screen_configs

        self.matches: List[MatchedFeature] = []


 

    def match(self, frontend_functions: List[Dict[str, Any]],

              backend_apis: List[BackendAPI]) -> List[MatchedFeature]:

        """

        프론트엔드 함수와 백엔드 API 매칭


 

        Returns:

            매칭 결과 리스트

        """

        self.matches = []


 

        # 프론트엔드 함수를 API 경로별로 grouping

        api_groups = self._group_by_api(frontend_functions)


 

        for api_path, funcs in api_groups.items():

            match_type = 'none'

            backend_matches = []


 

            # exact match

            exact = [api for api in backend_apis if api.path == api_path]

            if exact:

                backend_matches = exact

                match_type = 'exact'

            else:

                # prefix match

                prefix = [api for api in backend_apis

                          if api.path.startswith(api_path) or api_path.startswith(api.path)]

                if prefix:

                    backend_matches = prefix

                    match_type = 'prefix'


 

            self.matches.append(MatchedFeature(

                api_path=api_path,

                frontend_functions=funcs,

                backend_apis=backend_matches,

                match_type=match_type

            ))


 

        return self.matches


 

    def _group_by_api(self, functions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:

        """API 경로별 함수 grouping"""

        groups = {}


 

        for func in functions:

            for api_call in func.get('api_calls', []):

                if api_call.get('type') == 'submit':

                    url = api_call.get('url', '')

                    if url:

                        if url not in groups:

                            groups[url] = []

                        groups[url].append(func)


 

        return groups


 

    def get_screen_name(self, file_path: str) -> str:

        """

        파일 경로에서 화면 이름 찾기


 

        Args:

            file_path: 파일 경로


 

        Returns:

            화면 이름 또는 "Unknown"

        """

        for screen in self.screen_configs:

            base_path = screen.get('frontend', {}).get('base_path', '')

            files = screen.get('frontend', {}).get('files', [])


 

            if base_path in file_path:

                for file_pattern in files:

                    if file_pattern in file_path:

                        return screen.get('name', 'Unknown')


 

        return "Unknown"


 

    def get_screen_configs(self) -> List[Dict[str, Any]]:

        """화면 설정 반환"""

        return self.screen_configs


 

    def separate_by_screen(self) -> Tuple[List[MatchedFeature], List[MatchedFeature]]:

        """

        A/B 화면별 매칭 결과 분리


 

        Returns:

            (a_screen_matches, b_screen_matches)

        """

        a_matches = []

        b_matches = []


 

        for match in self.matches:

            # 함수의 파일 경로로 화면 판별

            sample_func = match.frontend_functions[0] if match.frontend_functions else {}

            file_path = sample_func.get('file_path', '')


 

            screen_name = self.get_screen_name(file_path)


 

            if screen_name.lower().startswith('a') or 'cct' in screen_name.lower():

                a_matches.append(match)

            else:

                b_matches.append(match)


 

        return a_matches, b_matches
