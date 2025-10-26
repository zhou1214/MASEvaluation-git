import json
import re
import os

def get_content(log_file):

    quickthink_results = []

    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if '"cause_by":"QuickThink"' in line:
                try:
                    json_start = line.find("{")
                    json_data = json.loads(line[json_start:])

                    content = json_data.get("content", "")
                    code_blocks = re.findall(r"```(?:python)?\n(.*?)```", content, re.DOTALL)

                    if code_blocks:
                        quickthink_results.append({
                            "type": "code",
                            "content": code_blocks,
                            "raw_text": content
                        })
                    else:
                        quickthink_results.append({
                            "type": "text",
                            "content": content
                        })
                except Exception as e:
                    print(f"解析失败: {e}")
                    continue

    return quickthink_results


def extract_code(dir_path):
    code_path = os.path.join(dir_path, "code.txt")
    log_path = os.path.join(dir_path, "log.txt")
    code_doc = []

    if os.path.exists(code_path):
        with open(code_path, "r", encoding="utf-8") as f:
            code_doc.append(f.read())
        return code_doc
    if os.path.exists(log_path):
        results = get_content(log_path)
        for result in results:
            if result.get('type') == 'code':
                code_doc.extend(result.get('content', []))
        return code_doc
    else:
        return code_doc

if __name__ == "__main__":
    log_path = "../Results/metagpt/human/instruction5"
    result = extract_code(log_path)
    print(result)