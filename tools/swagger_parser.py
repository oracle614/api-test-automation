#!/usr/bin/env python3
import json
import re
import urllib.request
import urllib.parse


class SwaggerParser:
    def __init__(self, source):
        self.source = source
        self.spec = None
        self.base_url = ""
        self.endpoints = []

    def load(self):
        if self.source.startswith("http"):
            return self.load_from_url()
        else:
            return self.load_from_file()

    def load_from_url(self):
        try:
            with urllib.request.urlopen(self.source, timeout=10) as response:
                content = response.read().decode("utf-8")

            if self.source.endswith(".yaml") or self.source.endswith(".yml"):
                import yaml

                self.spec = yaml.safe_load(content)
            else:
                self.spec = json.loads(content)

            self.base_url = self.spec.get("host", "")
            schemes = self.spec.get("schemes", ["https"])
            self.base_url = f"{schemes[0]}://{self.base_url}"

            base_path = self.spec.get("basePath", "")
            self.base_url += base_path

            return True
        except Exception as e:
            print(f"加载失败: {e}")
            return False

    def load_from_file(self):
        try:
            with open(self.source, "r", encoding="utf-8") as f:
                content = f.read()

            if self.source.endswith(".yaml") or self.source.endswith(".yml"):
                import yaml

                self.spec = yaml.safe_load(content)
            else:
                self.spec = json.loads(content)

            return True
        except Exception as e:
            print(f"加载文件失败: {e}")
            return False

    def parse_endpoints(self):
        if not self.spec:
            return []

        paths = self.spec.get("paths", {})

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "summary": details.get("summary", ""),
                        "description": details.get("description", ""),
                        "parameters": self.parse_parameters(
                            details.get("parameters", [])
                        ),
                        "responses": self.parse_responses(details.get("responses", {})),
                        "tags": details.get("tags", []),
                    }
                    self.endpoints.append(endpoint)

        return self.endpoints

    def parse_parameters(self, parameters):
        parsed = []
        for param in parameters:
            p = {
                "name": param.get("name", ""),
                "in": param.get("in", ""),
                "required": param.get("required", False),
                "type": param.get("type", "string"),
                "description": param.get("description", ""),
                "format": param.get("format", ""),
                "enum": param.get("enum", []),
                "schema": param.get("schema", {}),
            }

            if "schema" in param and "type" in param["schema"]:
                p["type"] = param["schema"]["type"]

            parsed.append(p)

        return parsed

    def parse_responses(self, responses):
        parsed = {}
        for code, details in responses.items():
            parsed[code] = {
                "description": details.get("description", ""),
                "schema": details.get("schema", {}),
            }
        return parsed

    def get_endpoints_by_tag(self, tag):
        return [e for e in self.endpoints if tag in e["tags"]]

    def search_endpoint(self, keyword):
        results = []
        for e in self.endpoints:
            if (
                keyword.lower() in e["path"].lower()
                or keyword.lower() in e["summary"].lower()
            ):
                results.append(e)
        return results


class APIInfoParser:
    def __init__(self):
        pass

    def parse_text(self, text):
        endpoint = {"path": "", "method": "GET", "parameters": [], "responses": {}}

        lines = text.strip().split("\n")

        for line in lines:
            line = line.strip()

            if "接口" in line or "endpoint" in line.lower():
                match = re.search(r"[:：]\s*(/\S+)", line)
                if match:
                    endpoint["path"] = match.group(1)

            if "方法" in line or "method" in line.lower():
                methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
                for m in methods:
                    if m in line.upper():
                        endpoint["method"] = m

            if "参数" in line or "parameter" in line.lower():
                if "必填" in line or "required" in line.lower():
                    param = {"name": "", "type": "string", "required": True}
                    match = re.search(r"(\w+)\s*\(", line)
                    if match:
                        param["name"] = match.group(1)
                    endpoint["parameters"].append(param)

            if "返回" in line or "response" in line.lower():
                endpoint["responses"] = {"200": {"description": "success"}}

        return endpoint


if __name__ == "__main__":
    parser = SwaggerParser("https://petstore.swagger.io/v2/swagger.json")
    if parser.load():
        endpoints = parser.parse_endpoints()
        print(f"解析到 {len(endpoints)} 个接口")
        for e in endpoints[:3]:
            print(f"  {e['method']} {e['path']}")
