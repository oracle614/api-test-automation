---
name: api-test-automation
version: 1.0.0
description: API接口测试自动化 - 支持Swagger/文档解析、自动生成测试脚本、参数校验、返回验证
author: Sisyphus
trigger:
  - API测试
  - 接口测试
  - Swagger测试
  - 接口文档测试
  - API自动化
  - 接口校验
capabilities:
  - 解析Swagger/OpenAPI文档
  - 解析接口文档生成测试用例
  - 自动生成API测试脚本
  - 参数必填校验
  - 返回值结构校验
  - 响应码验证
  - 数据类型校验
  - 生成测试报告
category: testing
---

# API 接口测试自动化

## 概述

本 Skill 支持从 Swagger UI、OpenAPI 文档或接口说明自动生成 API 测试脚本，包含参数校验和返回结果验证。

## 触发词

API测试、接口测试、Swagger测试、接口文档测试、API自动化、接口校验

## 支持的输入

### 1. Swagger URL

```
https://api.example.com/swagger-ui.html
https://api.example.com/v2/api-docs
https://api.example.com/openapi.json
```

### 2. 本地文档

- OpenAPI JSON/YAML 文件
- API Markdown 文档
- 接口说明文档

### 3. 直接输入

```
接口: /api/login
方法: POST
参数: {username, password}
返回: {token, userId}
```

## 生成测试脚本

### 示例：登录接口

**输入**：
```
接口: POST /api/login
参数:
  - username (string, 必填)
  - password (string, 必填)
返回:
  - code (int)
  - message (string)
  - data.token (string)
```

**生成的脚本**：

```python
import requests
import pytest
import json

BASE_URL = "https://api.example.com"

class TestLogin:
    """登录接口测试"""
    
    def test_login_success(self):
        """测试正常登录"""
        url = f"{BASE_URL}/api/login"
        payload = {
            "username": "testuser",
            "password": "Test123456"
        }
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "token" in data["data"]
    
    def test_login_missing_username(self):
        """测试缺少用户名"""
        url = f"{BASE_URL}/api/login"
        payload = {"password": "Test123456"}
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        assert data["code"] != 0
        assert "username" in data["message"]
    
    def test_login_missing_password(self):
        """测试缺少密码"""
        url = f"{BASE_URL}/api/login"
        payload = {"username": "testuser"}
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        assert data["code"] != 0
        assert "password" in data["message"]
    
    def test_login_empty_username(self):
        """测试用户名为空"""
        url = f"{BASE_URL}/api/login"
        payload = {"username": "", "password": "Test123456"}
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        assert data["code"] != 0
    
    def test_login_invalid_credentials(self):
        """测试错误密码"""
        url = f"{BASE_URL}/api/login"
        payload = {"username": "testuser", "password": "wrongpass"}
        
        response = requests.post(url, json=payload)
        data = response.json()
        
        assert data["code"] != 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

## 参数校验规则

### 1. 必填参数校验

```python
def validate_required_params(required_params, payload):
    missing = []
    for param in required_params:
        if param not in payload or payload[param] is None:
            missing.append(param)
    return missing
```

### 2. 参数类型校验

| 类型 | 校验规则 |
|------|----------|
| string | isinstance(value, str) |
| integer | isinstance(value, int) |
| number | isinstance(value, (int, float)) |
| boolean | isinstance(value, bool) |
| array | isinstance(value, list) |
| object | isinstance(value, dict) |

### 3. 格式校验

```python
FORMATS = {
    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    "phone": r"^1[3-9]\d{9}$",
    "url": r"^https?://",
    "date": r"^\d{4}-\d{2}-\d{2}$",
    "datetime": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
}

def validate_format(value, format_type):
    import re
    return re.match(FORMATS[format_type], value)
```

## 返回值校验

### 1. 结构校验

```python
def validate_response_schema(actual_data, expected_schema):
    errors = []
    
    for field, field_type in expected_schema.items():
        if field not in actual_data:
            errors.append(f"Missing field: {field}")
        elif not isinstance(actual_data[field], field_type):
            errors.append(f"Type error: {field} expected {field_type}")
    
    return errors
```

### 2. 响应码校验

| 场景 | 预期响应码 |
|------|------------|
| 成功 | 200, 201 |
| 客户端错误 | 400, 401, 403, 404 |
| 服务端错误 | 500, 502, 503 |

### 3. 业务码校验

```python
def validate_business_code(response, expected_code):
    return response.json().get("code") == expected_code
```

## 完整测试用例设计

### 用例矩阵

| 用例类型 | 说明 | 示例 |
|----------|------|------|
| 正向 | 正常参数通过 | 登录成功 |
| 缺参 | 缺少必填参数 | 不传username |
| 空值 | 参数为空 | username="" |
| 类型错 | 参数类型错误 | username=123 |
| 格式错 | 格式不符合 | email="abc" |
| 超限 | 超出长度限制 | username="a"*100 |
| 错误值 | 错误业务值 | 错误密码 |

## 测试报告

```python
def generate_api_test_report(results):
    report = f"""
# API 测试报告

## 概览
- 接口: {results['endpoint']}
- 方法: {results['method']}
- 总用例: {results['total']}
- 通过: {results['passed']}
- 失败: {results['failed']}

## 详细结果
| 用例 | 状态 | 响应码 | 耗时 |
|------|------|--------|------|
"""
    for case in results['cases']:
        status = "✓" if case['passed'] else "✗"
        report += f"| {case['name']} | {status} | {case['status_code']} | {case['duration']}ms |\n"
    
    return report
```

## 使用方式

### 1. 读取 Swagger

```python
from swagger_parser import SwaggerParser

parser = SwaggerParser("https://api.example.com/swagger.json")
endpoints = parser.get_all_endpoints()

for endpoint in endpoints:
    generate_test_script(endpoint)
```

### 2. 直接输入接口信息

```python
api_info = {
    "endpoint": "/api/login",
    "method": "POST",
    "parameters": [
        {"name": "username", "type": "string", "required": True},
        {"name": "password", "type": "string", "required": True}
    ],
    "responses": {
        "200": {"schema": {"token": "string"}}
    }
}

script = generate_api_script(api_info)
```

### 3. 批量测试

```python
apis = load_apis_from_file("apis.yaml")
results = []

for api in apis:
    result = run_api_tests(api)
    results.append(result)

generate_summary_report(results)
```

## 工具文件

- `tools/swagger_parser.py` - Swagger解析
- `tools/test_generator.py` - 测试脚本生成
- `tools/validator.py` - 参数和返回校验

## 版本

v1.0.0 - 支持Swagger解析、参数校验、返回验证