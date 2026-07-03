import urllib.request
import json

def get_openapi():
    req = urllib.request.Request("http://127.0.0.1:8000/openapi.json")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())

def generate_curls(openapi):
    curls = []
    base_url = "http://localhost:8000"
    for path, methods in openapi.get("paths", {}).items():
        for method, details in methods.items():
            if method.lower() == "parameters":
                continue
            
            curl = f"curl -X '{method.upper()}' '{base_url}{path}' \\\n"
            curl += "  -H 'accept: application/json' \\\n"
            
            # Check for body
            if "requestBody" in details:
                content = details["requestBody"].get("content", {})
                if "application/json" in content:
                    curl += "  -H 'Content-Type: application/json' \\\n"
                    schema_ref = content["application/json"].get("schema", {}).get("$ref")
                    # Usually would look up schema, but we can just put a generic body
                    curl += "  -d '{}' \\\n"
                elif "multipart/form-data" in content:
                    curl += "  -H 'Content-Type: multipart/form-data' \\\n"
                    curl += "  -F 'file=@/path/to/file' \\\n"
                elif "application/x-www-form-urlencoded" in content:
                    curl += "  -H 'Content-Type: application/x-www-form-urlencoded' \\\n"
                    curl += "  -d 'username=test&password=test' \\\n"
            
            # Check for auth
            if "security" in details:
                curl += "  -H 'Authorization: Bearer YOUR_TOKEN' \\\n"
            
            # Remove trailing slash and newline
            curl = curl.rstrip(" \\\n")
            
            curls.append(f"# {details.get('summary', 'Endpoint')}\n{curl}\n")
    return "\n".join(curls)

if __name__ == "__main__":
    try:
        openapi = get_openapi()
        print(generate_curls(openapi))
    except Exception as e:
        print(f"Error: {e}")
