"""

프론트엔드 파일 분석기

JavaScript 및 CLX 파일 파싱

"""

import os

import re

from pathlib import Path

from typing import Dict, List, Any, Optional

from dataclasses import dataclass, field, asdict


 


 

@dataclass

class FunctionInfo:

    """함수 정보"""

    name: str

    start_line: int

    end_line: int

    code: str

    calls: List[str] = field(default_factory=list)

    api_calls: List[Dict[str, str]] = field(default_factory=list)

    is_business_logic: bool = False

    conditions: List[str] = field(default_factory=list)


 


 

@dataclass

class UIElementInfo:

    """UI 요소 정보"""

    name: str

    element_type: str  # input, grid, combobox, button, etc.

    clx_file: str

    attributes: Dict[str, str] = field(default_factory=dict)

    bindings: List[str] = field(default_factory=list)  # data binding expressions


 


 

@dataclass

class FrontendFileInfo:

    """프론트엔드 파일 분석 결과"""

    file_name: str

    file_type: str  # 'js' or 'clx'

    total_lines: int

    functions: List[FunctionInfo]

    ui_elements: List[UIElementInfo]

    imports: List[str]

    screen_name: str = ""

    full_path: str = ""


 


 

class FrontendAnalyzer:

    """프론트엔드 코드 분석기"""


 

    def __init__(self):

        self.file_infos: List[FrontendFileInfo] = []


 

    def analyze_directory(self, base_path: str) -> List[FrontendFileInfo]:

        """

        디렉토리의 모든 JS/CLX 파일 분석


 

        Args:

            base_path: 검색 시작 디렉토리


 

        Returns:

            분석된 파일 정보 리스트

        """

        self.file_infos = []

        base = Path(base_path)


 

        if not base.exists():

            print(f"[WARN] 경로 없음: {base_path}")

            return []


 

        # JS 파일 찾기

        js_files = list(base.rglob("*.js"))


 

        # CLX 파일 찾기

        clx_files = list(base.rglob("*.clx"))


 

        all_files = js_files + clx_files


 

        print(f"발견된 파일: {len(all_files)}개 (JS: {len(js_files)}, CLX: {len(clx_files)})")


 

        for file_path in all_files:

            try:

                file_info = self._analyze_file(file_path)

                if file_info:

                    self.file_infos.append(file_info)

            except Exception as e:

                print(f"[ERROR] {file_path.name} 분석 실패: {e}")


 

        return self.file_infos


 

    def analyze_single_file(self, file_name: str, content: str, screen_name: str) -> Optional[Dict[str, Any]]:

        """

        단일 파일 내용 분석 (Git 저장소용)


 

        Args:

            file_name: 파일명

            content: 파일 내용

            screen_name: 화면명


 

        Returns:

            분석 결과 딕셔너리 또는 None

        """

        try:

            # 파일 타입 결정

            if file_name.endswith('.js'):

                file_type = 'js'

            elif file_name.endswith('.clx'):

                file_type = 'clx'

            else:

                return None


 

            # 임시 파일처럼 처리

            lines = content.split('\n')

            total_lines = len(lines)


 

            result = {

                'file_name': file_name,

                'file_type': file_type,

                'total_lines': total_lines,

                'screen_name': screen_name

            }


 

            if file_type == 'js':

                functions = self._parse_javascript(content, file_name)

                imports = self._extract_imports(content)

                result['functions'] = [asdict(f) for f in functions]

                result['imports'] = imports

            else:  # clx

                ui_elements = self._parse_clx(content, file_name)

                result['ui_elements'] = [asdict(e) for e in ui_elements]

                result['functions'] = []


 

            return result


 

        except Exception as e:

            print(f"[ERROR] 파일 분석 실패 ({file_name}): {e}")

            return None


 

    def _analyze_file(self, file_path: Path) -> Optional[FrontendFileInfo]:

        """파일 분석"""

        try:

            with open(file_path, 'r', encoding='utf-8') as f:

                content = f.read()

        except UnicodeDecodeError:

            # 다른 인코딩 시도

            try:

                with open(file_path, 'r', encoding='cp949') as f:

                    content = f.read()

            except:

                print(f"[WARN] 인코딩 오류: {file_path}")

                return None


 

        file_type = 'js' if file_path.suffix == '.js' else 'clx'

        lines = content.split('\n')

        total_lines = len(lines)


 

        file_info = FrontendFileInfo(

            file_name=file_path.name,

            file_type=file_type,

            total_lines=total_lines,

            functions=[],

            ui_elements=[],

            imports=[],

            full_path=str(file_path)

        )


 

        if file_type == 'js':

            file_info.functions = self._parse_javascript(content, file_path.name)

            file_info.imports = self._extract_imports(content)

        else:

            file_info.ui_elements = self._parse_clx(content, file_path.name)


 

        return file_info


 

    def _parse_javascript(self, content: str, file_name: str) -> List[FunctionInfo]:

        """JavaScript 파일에서 함수 추출"""

        functions = []

        lines = content.split('\n')


 

        # 함수 패턴들

        func_patterns = [

            # function declarePattern

            r'function\s+(\w+)\s*\(([^)]*)\)\s*\{',

            # arrow function assign

            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>\s*\{',

            # arrow function simple

            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function\s*\(([^)]*)\)',

            # method shorthand

            r'(\w+)\s*\(([^)]*)\)\s*\{',

        ]


 

        i = 0

        while i < len(lines):

            line = lines[i].strip()


 

            # 주석 건너뛰기

            if line.startswith('//') or line.startswith('*') or line == '':

                i += 1

                continue


 

            # 블록 주석 찾기

            if '/*' in line:

                i = self._skip_block_comment(lines, i)

                continue


 

            for pattern in func_patterns:

                match = re.search(pattern, line)

                if match:

                    func_name = match.group(1)

                    params = match.group(2) if len(match.groups()) > 1 else ""


 

                    # 함수 본문 찾기

                    brace_count = line.count('{') - line.count('}')

                    start_line = i

                    end_line = i


 

                    if brace_count <= 0:

                        # 본문이 같은 줄에 있는지 확인

                        if '{' in line and '}' in line and line.rindex('{') < line.rindex('}'):

                            func_code = line[line.find('{'):line.rfind('}')+1]

                            end_line = i

                        else:

                            i += 1

                            continue

                    else:

                        # 여러 줄에 걸친 함수 본문

                        j = i + 1

                        while j < len(lines) and brace_count > 0:

                            brace_count += lines[j].count('{') - lines[j].count('}')

                            end_line = j

                            j += 1

                        func_code = '\n'.join(lines[start_line:end_line+1])


 

                    # 함수 정보 생성

                    func_info = FunctionInfo(

                        name=func_name,

                        start_line=start_line + 1,

                        end_line=end_line + 1,

                        code=func_code,

                        calls=self._extract_function_calls(func_code),

                        api_calls=self._extract_api_calls(func_code),

                        is_business_logic=self._is_business_logic(func_name, func_code),

                        conditions=self._extract_conditions(func_code)

                    )


 

                    functions.append(func_info)

                    i = end_line + 1

                    break

            else:

                i += 1


 

        return functions


 

    def _extract_imports(self, content: str) -> List[str]:

        """import 문 추출"""

        imports = []

        patterns = [

            r'import\s+(?:{[^}]+}\s+from\s+)?[\'"]([^\'"]+)[\'"]',

            r'require\([\'"]([^\'"]+)[\'"]\)'

        ]

        for pattern in patterns:

            for match in re.finditer(pattern, content):

                imports.append(match.group(1))

        return list(set(imports))


 

    def _parse_clx(self, content: str, file_name: str) -> List[UIElementInfo]:

        """CLX 파일에서 UI 요소 추출"""

        ui_elements = []

        lines = content.split('\n')


 

        # UI 컴포넌트 패턴들

        element_patterns = [

            (r'<wd:input\s+([^>]+)/>', 'input'),

            (r'<wd:grid\s+([^>]+)/>', 'grid'),

            (r'<wd:combobox\s+([^>]+)/>', 'combobox'),

            (r'<wd:textbox\s+([^>]+)/>', 'textbox'),

            (r'<wd:button\s+([^>]+)/>', 'button'),

            (r'<wd:select\s+([^>]+)/>', 'select'),

            (r'<wd:datebox\s+([^>]+)/>', 'datebox'),

            (r'<wd:numberbox\s+([^>]+)/>', 'numberbox'),

        ]


 

        for line in lines:

            line = line.strip()

            if line.startswith('//') or line.startswith('*') or not any(p[0] in line for p in element_patterns):

                continue


 

            for pattern, elem_type in element_patterns:

                match = re.search(pattern, line)

                if match:

                    attrs_str = match.group(1)

                    attrs = self._parse_attributes(attrs_str)


 

                    ui_elem = UIElementInfo(

                        name=attrs.get('id', attrs.get('name', 'unknown')),

                        element_type=elem_type,

                        clx_file=file_name,

                        attributes=attrs,

                        bindings=self._extract_bindings(attrs_str)

                    )

                    ui_elements.append(ui_elem)

                    break


 

        return ui_elements


 

    def _parse_attributes(self, attrs_str: str) -> Dict[str, str]:

        """XML 속성 파싱"""

        attrs = {}

        pattern = r'(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]'

        for match in re.finditer(pattern, attrs_str):

            attrs[match.group(1)] = match.group(2)

        return attrs


 

    def _extract_bindings(self, attrs_str: str) -> List[str]:

        """데이터 바인딩 표현식 추출"""

        bindings = []

        # value, textField, dataField 등의 속성에서 바인딩 찾기

        patterns = [

            r'(?:value|textField|dataField)\s*=\s*[\'"]([^\'"]+)[\'"]',

            r'bind\s*:\s*[\'"]([^\'"]+)[\'"]',

        ]

        for pattern in patterns:

            for match in re.finditer(pattern, attrs_str):

                bindings.append(match.group(1))

        return bindings


 

    def _extract_function_calls(self, code: str) -> List[str]:

        """함수 호출 추출"""

        calls = []

        # 함수 호출 패턴: functionName(...)

        pattern = r'(\w+)\s*\('

        for match in re.finditer(pattern, code):

            func_name = match.group(1)

            if func_name not in ['if', 'while', 'for', 'switch', 'catch', 'return']:

                calls.append(func_name)

        return list(set(calls))


 

    def _extract_api_calls(self, code: str) -> List[Dict[str, str]]:

        """API 호출 추출"""

        api_calls = []


 

        # util.Submit.send 패턴

        submit_pattern = r'util\.Submit\.send\(\s*[\'"]([^\'"]+)[\'"]'

        for match in re.finditer(submit_pattern, code):

            api_calls.append({

                'type': 'submit',

                'url': match.group(1)

            })


 

        # $http, axios 패턴

        http_patterns = [

            (r'\$http\.(post|get|put|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]', 'angular'),

            (r'axios\.(post|get|put|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]', 'axios'),

            (r'fetch\s*\(\s*[\'"]([^\'"]+)[\'"]', 'fetch'),

        ]


 

        for pattern, lib in http_patterns:

            for match in re.finditer(pattern, code):

                api_calls.append({

                    'type': 'http',

                    'library': lib,

                    'method': match.group(1) if 'post' in pattern else 'GET',

                    'url': match.group(2) if len(match.groups()) > 1 else match.group(1)

                })


 

        return api_calls


 

    def _is_business_logic(self, func_name: str, code: str) -> bool:

        """비즈니스 로직 함수 판별"""

        # API 호출이 있으면 비즈니스 로직

        api_calls = self._extract_api_calls(code)

        if api_calls:

            return True


 

        # 특정 접두사/접미사

        business_prefixes = ['fn', 'save', 'delete', 'update', 'create', 'retrieve', 'query', 'search', 'load']

        business_suffixes = ['Action', 'Handler', 'Service', 'Manager']


 

        func_lower = func_name.lower()

        if any(func_lower.startswith(p) for p in business_prefixes):

            return True

        if any(func_lower.endswith(s) for s in business_suffixes):

            return True


 

        return False


 

    def _extract_conditions(self, code: str) -> List[str]:

        """조건문 추출"""

        conditions = []


 

        # if 문

        if_pattern = r'if\s*\(([^)]+)\)'

        for match in re.finditer(if_pattern, code):

            conditions.append(match.group(1).strip())


 

        # else if

        elif_pattern = r'else\s+if\s*\(([^)]+)\)'

        for match in re.finditer(elif_pattern, code):

            conditions.append(match.group(1).strip())


 

        # switch case

        case_pattern = r'case\s+([^:]+):'

        for match in re.finditer(case_pattern, code):

            conditions.append(f"case: {match.group(1).strip()}")


 

        # 3항 연산자

        ternary_pattern = r'\?\s*([^:]+)\s*:'

        for match in re.finditer(ternary_pattern, code):

            conditions.append(f"ternary: {match.group(1).strip()}")


 

        return conditions


 

    def _skip_block_comment(self, lines: List[str], start_idx: int) -> int:

        """블록 주석 건너뛰기"""

        i = start_idx

        while i < len(lines):

            if '*/' in lines[i]:

                return i + 1

            i += 1

        return i
