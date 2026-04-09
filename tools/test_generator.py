#!/usr/bin/env python3
import json
import re
from datetime import datetime


class APITestGenerator:
    def __init__(self, base_url="https://api.example.com"):
        self.base_url = base_url
        self.imports = []
        self.test_class = ""

    def generate(self, endpoint):
        self.imports = ["import requests", "import pytest", "import json", ""]

        class_name = self.to_class_name(endpoint["path"])
        self.test_class = f"""
class Test{class_name}:
    '''{endpoint.get("summary", endpoint["path"])}'''
    
    BASE_URL = "{self.base_url}"
    ENDPOINT = "{endpoint["path"]}"
"""

        methods = self.generate_test_methods(endpoint)
        self.test_class += methods

        self.test_class += f"""

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""

        return "\n".join(self.imports) + self.test_class

    def to_class_name(self, path):
        parts = [p.capitalize() for p in path.split("/") if p]
        if not parts:
            return "API"
        return "".join(parts[:2]) if len(parts) >= 2 else parts[0]

    def generate_test_methods(self, endpoint):
        methods = ""
        path = endpoint["path"]
        params = endpoint.get("parameters", [])
        method = endpoint.get("method", "GET").upper()

        required_params = [p for p in params if p.get("required")]
        optional_params = [p for p in params if not p.get("required")]

        methods += self.generate_positive_case(path, method, required_params)

        for param in required_params:
            methods += self.generate_missing_param_case(path, method, param)

        if optional_params:
            methods += self.generate_optional_case(path, method, optional_params)

        for param in params:
            methods += self.generate_type_error_case(path, method, param)

        return methods

    def generate_positive_case(self, path, method, params):
        if method == "GET":
            param_str = self.params_to_string(params)
            code = f'''
    def test_{self.to_method_name(path)}_success(self):
        """正常{path}请求"""
        url = f"{{self.BASE_URL}}{{self.ENDPOINT}}"
        params = {{{param_str}}}
        
        response = requests.get(url, params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("code") == 0 or response.status_code == 200
'''
        else:
            param_str = self.params_to_string(params)
            code = f'''
    def test_{self.to_method_name(path)}_success(self):
        """正常{path}请求"""
        url = f"{{self.BASE_URL}}{{self.ENDPOINT}}"
        payload = {{{param_str}}}
        headers = {{"Content-Type": "application/json"}}
        
        response = requests.{method.lower()}(url, json=payload, headers=headers)
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("code") == 0 or response.status_code in [200, 201]
'''
        return code

    def generate_missing_param_case(self, path, method, param):
        name = param["name"]
        if method == "GET":
            code = f'''
    def test_{self.to_method_name(path)}_missing_{name}(self):
        """缺少必填参数 {name}"""
        url = f"{{self.BASE_URL}}{{self.ENDPOINT}}"
        
        response = requests.get(url)
        
        assert response.status_code == 400
        data = response.json()
        assert data.get("code") != 0
'''
        else:
            code = f'''
    def test_{self.to_method_name(path)}_missing_{name}(self):
        """缺少必填参数 {name}"""
        url = f"{{self.BASE_URL}}{{self.ENDPOINT}}"
        
        response = requests.{method.lower()}(url, json={{}})
        
        assert response.status_code == 400
        data = response.json()
        assert data.get("code") != 0
'''
        return code

    def generate_optional_case(self, path, method, params):
        name = params[0]["name"]
        code = f'''
    def test_{self.to_method_name(path)}_optional_{name}(self):
        """可选参数 {name}为空"""
        url = f"{{self.BASE_URL}}{{self.ENDPOINT}}"
        payload = {{"{name}": ""}}
        
        response = requests.{method.lower()}(url, json=payload)
        
        assert response.status_code in [200, 400]
'''
        return code

    def generate_type_error_case(self, path, method, param):
        name = param["name"]
        param_type = param.get("type", "string")

        wrong_type_value = self.get_wrong_type_value(param_type)

        if method == "GET":
            code = f'''
    def test_{self.to_method_name(path)}_type_error_{name}(self):
        """参数 {name} 类型错误"""
        url = f"{{self.BASE_URL}}{{self.ENDPOINT}}"
        params = {{"{name}": {wrong_type_value}}}
        
        response = requests.get(url, params=params)
        
        assert response.status_code in [400, 500]
'''
        else:
            code = f'''
    def test_{self.to_method_name(path)}_type_error_{name}(self):
        """参数 {name} 类型错误"""
        url = f"{{self.BASE_URL}}{{self.ENDPOINT}}"
        payload = {{"{name}": {wrong_type_value}}}
        
        response = requests.{method.lower()}(url, json=payload)
        
        assert response.status_code in [400, 500]
'''
        return code

    def params_to_string(self, params):
        if not params:
            return ""
        pairs = []
        for p in params:
            name = p["name"]
            default = self.get_default_value(p.get("type", "string"))
            pairs.append(f'"{name}": {default}')
        return ", ".join(pairs)

    def get_default_value(self, param_type):
        defaults = {
            "string": '"test"',
            "integer": "123",
            "number": "123.45",
            "boolean": "True",
            "array": "[]",
            "object": "{}",
        }
        return defaults.get(param_type, '"test"')

    def get_wrong_type_value(self, param_type):
        wrong_values = {
            "string": "123",
            "integer": '"abc"',
            "number": '"abc"',
            "boolean": '"true"',
            "array": "{}",
            "object": "[]",
        }
        return wrong_values.get(param_type, "123")

    def to_method_name(self, path):
        return "_".join([p for p in path.split("/") if p])[:50]


def generate_from_swagger(spec):
    generator = APITestGenerator()

    if isinstance(spec, dict):
        paths = spec.get("paths", {})
    else:
        return "Invalid spec"

    all_tests = []

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                endpoint = {
                    "path": path,
                    "method": method.upper(),
                    "summary": details.get("summary", ""),
                    "parameters": details.get("parameters", []),
                }
                test_code = generator.generate(endpoint)
                all_tests.append(test_code)

    return "\n\n".join(all_tests)


if __name__ == "__main__":
    test_spec = {
        "paths": {
            "/api/login": {
                "post": {
                    "summary": "用户登录",
                    "parameters": [
                        {"name": "username", "type": "string", "required": True},
                        {"name": "password", "type": "string", "required": True},
                    ],
                }
            },
            "/api/user": {
                "get": {
                    "summary": "获取用户信息",
                    "parameters": [
                        {"name": "userId", "type": "integer", "required": True}
                    ],
                }
            },
        }
    }

    result = generate_from_swagger(test_spec)
    print(result)
