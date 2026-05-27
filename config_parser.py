"""

설정 파일 파싱 모듈

"""

import json

from pathlib import Path

from typing import Dict, List, Any


 


 

class ConfigParser:

    """설정 파일 파서"""


 

    def __init__(self, config_path: str = "config.json"):

        self.config_path = Path(config_path)

        self.config = self._load_config()


 

    def _load_config(self) -> Dict[str, Any]:

        """설정 파일 로드"""

        if not self.config_path.exists():

            raise FileNotFoundError(f"설정 파일이 없습니다: {self.config_path}")


 

        with open(self.config_path, 'r', encoding='utf-8') as f:

            return json.load(f)


 

    def get_pods(self) -> Dict[str, Dict[str, Any]]:

        """Pods 설정 반환"""

        return self.config.get('pods', {})


 

    def get_backend_config(self) -> Dict[str, Any]:

        """백엔드 설정 반환"""

        return self.config.get('backend', {})


 

    def get_output_config(self) -> Dict[str, Any]:

        """출력 설정 반환"""

        return self.config.get('output', {})


 

    def get_screens_legacy(self) -> List[Dict[str, Any]]:

        """기존 screens 형식 호환"""

        return self.config.get('screens', [])
