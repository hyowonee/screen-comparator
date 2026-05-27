"""

화면 요건 분석기 v2

프론트엔드 분석 결과에서 사용자 요건 추출

"""

import re

from dataclasses import dataclass, field

from typing import List, Dict, Any, Optional


 


 

@dataclass

class UIElementInfo:

    """UI 요소 정보"""

    name: str

    element_type: str

    clx_file: str

    attributes: Dict[str, str]

    bindings: List[str]

    used_in_rules: List[str] = field(default_factory=list)  # 이 UI를 사용하는 규칙 ID들


 


 

@dataclass

class RequirementRule:

    """요건 규칙"""

    rule_id: str

    rule_type: str  # '조건', '검증', '상태', 'UI', 'API'

    category: str  # '입력값 검증', 'feld null 체크', '조건부'

    title: str

    user_description: str  # 사용자 언어로 설명

    technical_condition: str

    then_actions: List[str]

    ui_elements: List[UIElementInfo]

    api_calls: List[Dict[str, str]]

    tags: List[str] = field(default_factory=list)

    source_file: str = ""

    line_number: int = 0


 


 

@dataclass

class RequiremFrontendFileInfo:

    """프론트엔드 파일 정보 (분석 결과)"""

    file_name: str

    file_type: str

    total_lines: int

    functions: List[Dict[str, Any]]

    ui_elements: List[Dict[str, Any]]

    imports: List[str]

    screen_name: str

    full_path: str


 


 

class ScreenRequirementsAnalyzerV2:

    """화면 요건 추출 분석기 v2"""


 

    def __init__(self):

        self.ui_elements: Dict[str, UIElementInfo] = {}

        self.rules: List[RequirementRule] = []

        self.functions: List[Dict] = []

        self.api_calls: List[Dict] = []


 

    def analyze_screen(self, screen_name: str, frontend_files: List[RequiremFrontendFileInfo]) -> Dict[str, Any]:

        """

        화면 분석 실행


 

        Args:

            screen_name: 화면 이름

            frontend_files: 프론트엔드 파일 정보 리스트


 

        Returns:

            요건 분석 결과 딕셔너리

        """

        self.screen_name = screen_name

        self._reset_state()


 

        # 1. UI 요소 등록

        for file_info in frontend_files:

            for ui_elem in file_info.get('ui_elements', []):

                elem_key = f"{file_info['file_name']}:{ui_elem['name']}"

                self.ui_elements[elem_key] = UIElementInfo(

                    name=ui_elem['name'],

                    element_type=ui_elem['element_type'],

                    clx_file=file_info['file_name'],

                    attributes=ui_elem.get('attributes', {}),

                    bindings=ui_elem.get('bindings', [])

                )


 

        # 2. 함수와 API 수집

        for file_info in frontend_files:

            for func in file_info.get('functions', []):

                func_with_file = {

                    **func,

                    'file_name': file_info['file_name'],

                    'screen_name': screen_name

                }

                self.functions.append(func_with_file)


 

                # API 호출 추출

                if func.get('api_calls'):

                    for api_call in func['api_calls']:

                        api_call['file_name'] = file_info['file_name']

                        api_call['function_name'] = func['name']

                        self.api_calls.append(api_call)


 

        # 3. 규칙 추출

        self._extract_validation_rules()

        self._extract_condition_rules()

        self._extract_state_rules()

        self._extract_tab_transition_rules()

        self._extract_api_call_rules()

        self._extract_initialization_rules()


 

        # 4. UI 요소와 규칙 연결

        self._link_ui_to_rules()


 

        # 5. 결과요약

        return self._build_result()


 

    def _reset_state(self):

        """상태 초기화"""

        self.ui_elements = {}

        self.rules = []

        self.functions = []

        self.api_calls = []


 

    def _extract_validation_rules(self):

        """검증 규칙 추출"""

        validation_keywords = [

            'validate', 'check', 'isValid', 'hasError', 'required',

            '필수', '유효성', '검증', '확인'

        ]


 

        for func in self.functions:

            func_name_lower = func['name'].lower()

            conditions = func.get('conditions', [])


 

            for cond in conditions:

                # util.validateXXX 패턴

                validate_match = re.search(r'util\.validate([A-Z]\w+)\s*\(\s*([^)]+)\)', cond)

                if validate_match:

                    rule_id = f"VAL_{func['name']}_{len(self.rules)}"

                    rule = RequirementRule(

                        rule_id=rule_id,

                        rule_type='검증',

                        category='입력값 검증',

                        title=f"{validate_match.group(1)} 검증",

                        user_description=self._interpret_validation_call(validate_match.group(0), func),

                        technical_condition=validate_match.group(0),

                        then_actions=[],

                        ui_elements=[],

                        api_calls=[],

                        tags=['validation'],

                        source_file=func['file_name'],

                        line_number=func.get('start_line', 0)

                    )

                    self.rules.append(rule)

                    continue


 

                # 일반 조건으로부터 검증 규칙 유추

                if any(kw in cond.lower() for kw in validation_keywords):

                    rule_id = f"VAL_COND_{func['name']}_{len(self.rules)}"

                    rule = RequirementRule(

                        rule_id=rule_id,

                        rule_type='검증',

                        category='입력값 검증',

                        title=f"'{func['name']}' 함수 내 검증 조건",

                        user_description=self._interpret_condition(cond),

                        technical_condition=cond,

                        then_actions=[],

                        ui_elements=[],

                        api_calls=[],

                        tags=['validation', 'condition'],

                        source_file=func['file_name'],

                        line_number=func.get('start_line', 0)

                    )

                    self.rules.append(rule)


 

    def _interpret_validation_call(self, call_text: str, func: Dict) -> str:

        """검증 호출 해석"""

        func_name_lower = func['name'].lower()


 

        if 'reqtype' in func_name_lower or 'request' in func_name_lower:

            return "사용자 요청 정보의 유효성을 검증합니다."

        elif 'save' in func_name_lower:

            return "저장 전 입력값의 유효성을 검증합니다."

        elif 'fnadd' in func_name_lower or 'fnedit' in func_name_lower:

            return "신규/변경 등록 시 필수 항목을 검증합니다."

        else:

            return "입력 데이터의 형식과 값을 검증합니다."


 

    def _extract_condition_rules(self):

        """조건 규칙 추출"""

        for func in self.functions:

            conditions = func.get('conditions', [])


 

            for cond in conditions:

                # 이미 처리한 validation pattern이면 건너뛰기

                if re.search(r'util\.validate', cond):

                    continue


 

                rule_id = f"COND_{func['name']}_{len(self.rules)}"

                category = self._categorize_condition(cond)

                user_desc = self._interpret_condition(cond)


 

                rule = RequirementRule(

                    rule_id=rule_id,

                    rule_type='조건',

                    category=category,

                    title=f"조건: {cond[:50]}...",

                    user_description=user_desc,

                    technical_condition=cond,

                    then_actions=[],

                    ui_elements=[],

                    api_calls=[],

                    tags=['condition'],

                    source_file=func['file_name'],

                    line_number=func.get('start_line', 0)

                )

                self.rules.append(rule)


 

    def _categorize_condition(self, condition: str) -> str:

        """조건 카테고리 분류"""

        cond_lower = condition.lower()


 

        if 'value' in cond_lower or 'rdb' in cond_lower:

            return '상태 기반 조건'

        elif '!= null' in cond or '== null' in cond or 'empty' in cond_lower:

            return '널 값 체크'

        elif '==' in cond_lower or '!=' in cond_lower:

            return '값 비교'

        elif '>' in cond_lower or '<' in cond_lower or '>= ' in cond_lower or '<= ' in cond_lower:

            return '크기 비교'

        elif 'includes' in cond_lower or 'indexof' in cond_lower:

            return '포함 여부'

        elif 'match' in cond_lower or 'regex' in cond_lower:

            return '패턴 매칭'

        else:

            return '기타 조건'


 

    def _interpret_condition(self, condition: str) -> str:

        """조건 해석 (사용자 친화적)"""

        cond_clean = condition.strip()


 

        # dmAccountInfoForBasis.procOption 관련

        if 'procOption' in cond_clean and ('== ' in cond_clean or '!= ' in cond_clean):

            return self._interpret_proc_option_condition(cond_clean)


 

        # dsTempSaveYn 관련

        if 'dsTempSaveYn' in cond_clean:

            return "임시 저장 여부에 따른 분기 처리"


 

        # rdbProcOption 관련

        if 'rdbProcOption' in cond_clean:

            return "처리 옵션(신규/변경/조회 등)에 따른 분기 처리"


 

        # null/empty 체크

        if 'null' in cond_clean or 'empty' in cond_clean:

            return "필수 입력값이 존재하는지 확인"


 

        # switch case

        if 'case' in cond_clean:

            return f"선택된 값에 따른 분기: {cond_clean[:50]}"


 

        return f"조건 충족 시: {cond_clean[:80]}"


 

    def _interpret_proc_option_condition(self, cond: str) -> str:

        """procOption 조건 해석"""

        match = re.search(r"[!=]=\s*['\"]?(\w+)['\"]?", cond)


 

        if not match:

            return "처리 옵션에 따른 분기"


 

        option_code = match.group(1)

        option_meanings = {

            '1': '신규(변경)',

            '2': '조회',

            '3': '삭제',

            '4': '승인',

            '5': '반려',

            'N': '신규',

            'U': '변경',

            'D': '삭제',

            'Q': '조회'

        }


 

        meaning = option_meanings.get(option_code, option_code)

        op = "=" if "==" in cond else "≠"

        return f"처리 옵션이 '{meaning}'({option_code}){op}일 때 실행"


 

    def _extract_state_rules(self):

        """상태 관리 규칙 추출"""

        state_patterns = [

            (r'rdbProcOption\.value\s*=\s*["\'](\d+)["\']', 'rdbProcOption 설정'),

            (r'dsTempSaveYn\.setValue\([\'"]([^\'"]+)[\'"]\)', '임시 저장 상태 설정'),

            (r'tabIndex\s*=\s*(\d+)', '탭 인덱스 변경'),

        ]


 

        for func in self.functions:

            code = func['code']


 

            for pattern, desc in state_patterns:

                for match in re.finditer(pattern, code):

                    rule_id = f"STATE_{func['name']}_{len(self.rules)}"

                    rule = RequirementRule(

                        rule_id=rule_id,

                        rule_type='상태',

                        category='상태 관리',

                        title=desc,

                        user_description=f"{desc}이(가) 변경됩니다.",

                        technical_condition=match.group(0),

                        then_actions=[match.group(0)],

                        ui_elements=[],

                        api_calls=[],

                        tags=['state'],

                        source_file=func['file_name'],

                        line_number=func.get('start_line', 0)

                    )

                    self.rules.append(rule)


 

    def _extract_tab_transition_rules(self):

        """탭 전환 규칙 추출"""

        # onTabXSelectionChange 패턴

        tab_pattern = r'onTab(\d+)SelectionChange\s*\(\s*\w+\s*,\s*\w+\s*\)\s*\{([^}]+)\}'


 

        for func in self.functions:

            code = func['code']


 

            match = re.search(tab_pattern, code, re.DOTALL)

            if match:

                tab_num = match.group(1)

                tab_body = match.group(2)


 

                rule_id = f"TAB_{func['name']}_{len(self.rules)}"

                rule = RequirementRule(

                    rule_id=rule_id,

                    rule_type='UI',

                    category='탭 전환',

                    title=f"탭 {tab_num} 전환 처리",

                    user_description=f"탭 {tab_num}으로(으로) 이동할 때 실행되는 초기화 로직입니다.",

                    technical_condition=f"탭 {tab_num} 선택 시",

                    then_actions=[],

                    ui_elements=[],

                    api_calls=[],

                    tags=['tab', 'initialization'],

                    source_file=func['file_name'],

                    line_number=func.get('start_line', 0)

                )

                self.rules.append(rule)


 

    def _extract_api_call_rules(self):

        """API 호출 규칙 추출"""

        for api_call in self.api_calls:

            func_name = api_call.pop('function_name', 'unknown')

            file_name = api_call.pop('file_name', '')


 

            rule_id = f"API_{func_name}_{len(self.rules)}"

            rule_type = 'API' if api_call.get('type') == 'submit' else 'HTTP'


 

            api_desc = self._interpret_api_call(api_call)


 

            rule = RequirementRule(

                rule_id=rule_id,

                rule_type=rule_type,

                category='API 호출',

                title=f"API 호출: {api_call.get('url', 'unknown')}",

                user_description=api_desc,

                technical_condition=f"함수 '{func_name}'에서 호출",

                then_actions=[],

                ui_elements=[],

                api_calls=[api_call],

                tags=['api', rule_type.lower()],

                source_file=file_name,

                line_number=0

            )

            self.rules.append(rule)


 

    def _interpret_api_call(self, api_call: Dict) -> str:

        """API 호출 해석"""

        url = api_call.get('url', '')


 

        if '/save/' in url or '/create/' in url or '/insert/' in url:

            return "데이터를 서버에 저장합니다."

        elif '/delete/' in url or '/remove/' in url:

            return "서버에서 데이터를 삭제합니다."

        elif '/update/' in url or '/modify/' in url:

            return "서버 데이터를 수정합니다."

        elif '/list/' in url or '/search/' in url or '/query/' in url:

            return "서버에서 데이터 목록을 조회합니다."

        elif '/detail/' in url or '/view/' in url:

            return "단일 데이터 상세 정보를 조회합니다."

        else:

            return f"서버와 통신하여 데이터를 처리합니다: {url}"


 

    def _extract_initialization_rules(self):

        """초기화 로직 규칙 추출"""

        init_patterns = [

            (r'onPageInit\s*\([^)]*\)\s*\{([^}]+)\}', '페이지 초기화'),

            (r'onTab.*Init\s*\([^)]*\)\s*\{([^}]+)\}', '탭 초기화'),

            (r'init[^;]*;', '초기화 문장'),

        ]


 

        for func in self.functions:

            code = func['code']


 

            for pattern, desc in init_patterns:

                for match in re.finditer(pattern, code, re.DOTALL):

                    rule_id = f"INIT_{func['name']}_{len(self.rules)}"

                    rule = RequirementRule(

                        rule_id=rule_id,

                        rule_type='상태',

                        category='초기화',

                        title=desc,

                        user_description=f"화면/탭이 로드될 때 {desc}이(가) 수행됩니다.",

                        technical_condition=f"{desc} 실행",

                        then_actions=[],

                        ui_elements=[],

                        api_calls=[],

                        tags=['initialization'],

                        source_file=func['file_name'],

                        line_number=func.get('start_line', 0)

                    )

                    self.rules.append(rule)


 

    def _link_ui_to_rules(self):

        """UI 요소와 규칙 연결"""

        for rule in self.rules:

            # 조건에 언급된 UI 요소 찾기

            condition = rule.technical_condition.lower()


 

            for elem_key, elem_info in self.ui_elements.items():

                elem_name_lower = elem_info.name.lower()


 

                # UI 요소 이름이 조건에 있으면 연결

                if elem_name_lower in condition:

                    if elem_info not in rule.ui_elements:

                        rule.ui_elements.append(elem_info)

                        elem_info.used_in_rules.append(rule.rule_id)


 

                # 바인딩 변수가 조건에 있으면 연결

                for binding in elem_info.bindings:

                    binding_lower = binding.lower()

                    if binding_lower in condition:

                        if elem_info not in rule.ui_elements:

                            rule.ui_elements.append(elem_info)

                            elem_info.used_in_rules.append(rule.rule_id)


 

            # then_actions에서도 UI 요소 찾기

            for action in rule.then_actions:

                action_lower = action.lower()

                for elem_key, elem_info in self.ui_elements.items():

                    if elem_info.name.lower() in action_lower:

                        if elem_info not in rule.ui_elements:

                            rule.ui_elements.append(elem_info)

                            elem_info.used_in_rules.append(rule.rule_id)


 

    def _build_result(self) -> Dict[str, Any]:

        """결과 구조화"""

        # 카테고리별 grouping

        categories = {}

        for rule in self.rules:

            cat = rule.category

            if cat not in categories:

                categories[cat] = []

            categories[cat].append(rule)


 

        # UI 요소 목록

        ui_list = list(self.ui_elements.values())


 

        return {

            'screen_name': self.screen_name,

            'total_rules': len(self.rules),

            'total_functions': len(self.functions),

            'total_ui_elements': len(ui_list),

            'categories': categories,

            'rules': self.rules,

            'ui_elements': ui_list,

            'functions': self.functions,

            'api_calls': self.api_calls

        }
