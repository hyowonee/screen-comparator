"""

백엔드 Java 코드 분석기

Spring Controller 기반 API 추출

"""

import os

import re

from pathlib import Path

from typing import List, Dict, Any

from dataclasses import dataclass, field


 


 

@dataclass

class BackendAPI:

    """백엔드 API 정보"""

    class_name: str

    method_name: str

    http_method: str  # GET, POST, etc.

    path: str

    full_signature: str

    file_path: str

    line_number: int = 0

    parameters: List[str] = field(default_factory=list)

    return_type: str = ""


 


 

class BackendAnalyzer:

    """Java 백엔드 분석기"""


 

    def __init__(self):

        self.apis: List[BackendAPI] = []


 

    def analyze_directory(self, search_paths: List[str]) -> List[BackendAPI]:

        """

        지정된 경로에서 Java 파일 분석


 

        Args:

            search_paths: 검색할 디렉토리 경로 리스트


 

        Returns:

            발견된 API 목록

        """

        self.apis = []


 

        for search_path in search_paths:

            path = Path(search_path)

            if not path.exists():

                print(f"[WARN] 경로 없음: {search_path}")

                continue


 

            print(f"검색 중: {search_path}")

            java_files = list(path.rglob("*.java"))


 

            for java_file in java_files:

                try:

                    self._analyze_file(java_file)

                except Exception as e:

                    print(f"[ERROR] {java_file} 분석 실패: {e}")


 

        print(f"✓ 발견된 API: {len(self.apis)}개")

        return self.apis


 

    def _analyze_file(self, file_path: Path):

        """단일 Java 파일 분석"""

        try:

            with open(file_path, 'r', encoding='utf-8') as f:

                content = f.read()

                lines = content.split('\n')

        except Exception as e:

            print(f"[WARN] 파일 읽기 실패: {file_path} - {e}")

            return


 

        # @RestController 또는 @Controller 클래스 찾기

        class_pattern = r'@(RestController|Controller)\s+public\s+class\s+(\w+)'

        class_match = re.search(class_pattern, content)


 

        if not class_match:

            return


 

        class_name = class_match.group(2)


 

        # @GetMapping, @PostMapping 등 찾기

        mapping_patterns = [

            (r'@GetMapping\([^)]*path\s*=\s*"([^"]+)"', 'GET'),

            (r'@GetMapping\([^)]*value\s*=\s*"([^"]+)"', 'GET'),

            (r'@PostMapping\([^)]*path\s*=\s*"([^"]+)"', 'POST'),

            (r'@PostMapping\([^)]*value\s*=\s*"([^"]+)"', 'POST'),

            (r'@PutMapping\([^)]*path\s*=\s*"([^"]+)"', 'PUT'),

            (r'@DeleteMapping\([^)]*path\s*=\s*"([^"]+)"', 'DELETE'),

            (r'@RequestMapping\([^)]*method\s*=\s*RequestMethod\.(GET|POST|PUT|DELETE)', None),

        ]


 

        # 메서드 패턴

        method_pattern = r'(public|private|protected)\s+([\w<>\[\], ?]+)\s+(\w+)\s*\(([^)]*)\)'


 

        for i, line in enumerate(lines):

            # 매핑 어노테이션 찾기

            for pattern, http_method in mapping_patterns:

                match = re.search(pattern, line)

                if match:

                    path = match.group(1) if http_method else self._extract_path_from_requestmapping(line)

                    if path:

                        # 같은 줄이나 다음 줄에 메서드 정의 찾기

                        method_sig = self._find_method_signature(lines, i)

                        if method_sig:

                            method_match = re.match(method_pattern, method_sig)

                            if method_match:

                                api = BackendAPI(

                                    class_name=class_name,

                                    method_name=method_match.group(3),

                                    http_method=http_method or 'GET',

                                    path=path,

                                    full_signature=method_sig.strip(),

                                    file_path=str(file_path),

                                    line_number=i + 1,

                                    parameters=self._parse_parameters(method_match.group(4)),

                                    return_type=method_match.group(2).strip()

                                )

                                self.apis.append(api)


 

    def _extract_path_from_requestmapping(self, line: str) -> str:

        """@RequestMapping에서 path 추출"""

        match = re.search(r'path\s*=\s*"([^"]+)"', line)

        return match.group(1) if match else ""


 

    def _find_method_signature(self, lines: List[str], start_idx: int) -> str:

        """메서드 시그니처 찾기"""

        for j in range(start_idx, min(start_idx + 5, len(lines))):

            line = lines[j].strip()

            # 메서드 정의 패턴

            if re.match(r'^(public|private|protected)\s+[\w<>\[\]]+\s+\w+\s*\(', line):

                # 여러 줄에 걸친 경우 고려

                sig = line

                if not line.endswith(')'):

                    # 다음 줄들 찾기

                    for k in range(j + 1, min(j + 10, len(lines))):

                        sig += lines[k].strip()

                        if ')' in lines[k]:

                            break

                return sig

        return ""


 

    def _parse_parameters(self, param_str: str) -> List[str]:

        """파라미터 문자열 파싱"""

        if not param_str.strip():

            return []


 

        params = []

        for param in param_str.split(','):

            param = param.strip()

            if param:

                params.append(param)

        return params


 

    def get_api_by_path(self, path: str, http_method: str = None) -> List[BackendAPI]:

        """

        경로로 API 검색


 

        Args:

            path: API 경로

            http_method: HTTP 메서드 (선택)


 

        Returns:

            일치하는 API 리스트

        """

        results = []

        for api in self.apis:

            if api.path == path:

                if http_method is None or api.http_method == http_method:

                    results.append(api)

        return results


 

    def find_similar_apis(self, path: str, max_distance: int = 2) -> List[BackendAPI]:

        """유사한 경로의 API 찾기 (prefix match)"""

        results = []

        for api in self.apis:

            # prefix match

            if api.path.startswith(path) or path.startswith(api.path):

                results.append(api)

        return sorted(results, key=lambda x: len(x.path))
