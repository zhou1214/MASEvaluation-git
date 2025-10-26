
import ast

from MAS2 import agnetcoder,agentverse,chatdev,Self
import os
import subprocess
import json
import tempfile
from openai import OpenAI
import coveragePrompt
import pandas as pd


def get_agentcoder_code(log_path):
    analysis = agnetcoder.AgentCoderAnalysis()
    code = analysis.get_final_code(log_path)
    return code


def get_agentcoder_test(log_path):
    analysis = agnetcoder.AgentCoderAnalysis()
    test = analysis.get_test_list(log_path)
    return test

def get_agentverse_code(log_path):
    analysis = agentverse.AgentVerseAnalysis()
    dirty_code = analysis.get_final_code(log_path)

    if not dirty_code:
        return ""

    lines = dirty_code.split('\n')
    clean_code = ""

    for i in range(len(lines), 0, -1):
        potential_code = "\n".join(lines[:i])
        if not potential_code.strip():
            continue

        try:
            ast.parse(potential_code)
            clean_code = potential_code
            break
        except SyntaxError:
            continue

    if not clean_code:
        return dirty_code

    return clean_code

def get_agentverse_test(log_path):
    analysis = agentverse.AgentVerseAnalysis()
    test = analysis.get_test_list(log_path)
    print("test")
    print(test)
    return test

def get_chatdev_code(log_path):
    analysis = chatdev.ChatDevAnalysis()
    code = analysis.get_final_code(log_path)
    print("code")
    print(code)
    return code


def get_chatdev_test(log_path):
    analysis = chatdev.ChatDevAnalysis()
    code,test = analysis.get_list(log_path)
    print("test")
    print(test)
    return test

def get_self_code(log_path):
    analysis = Self.SelfAnalysis()
    code = analysis.get_final_code(log_path)
    print("code")
    print(code)
    return code

def get_self_test(log_path):
    analysis = Self.SelfAnalysis()
    test = analysis.get_test_list(log_path)
    print("test")
    print(test)
    return test

def get_llm_evaluation(final_prompt: str) -> str:
    client = OpenAI(
        base_url=os.getenv('BASE_URL', ''),
        api_key=os.environ.get('OPENAI_API_KEY', ""),
    )

    try:
        response = client.chat.completions.create(
            model="",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant that generates standardized test code according to user instructions."},
                {"role": "user", "content": final_prompt},
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        return ""


def standardize_tests_with_llm(source_code: str, raw_test_code: str) -> str:
    prompt_template = coveragePrompt.prompt
    final_prompt = prompt_template.format(
        source_code=source_code,
        raw_test_code=raw_test_code
    )
    response_text = get_llm_evaluation(final_prompt)
    print(response_text)
    return response_text


def calculate_coverage(source_code: str, standardized_pytest_code: str) -> float:
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            source_path = os.path.join(temp_dir, "source_to_test.py")
            test_path = os.path.join(temp_dir, "test_generated.py")

            with open(source_path, "w", encoding="utf-8") as f:
                f.write(source_code)
            with open(test_path, "w", encoding="utf-8") as f:
                f.write(standardized_pytest_code)

            run_command = ["coverage", "run", "--source=source_to_test", "-m", "pytest", test_path]


            proc = subprocess.run(run_command, capture_output=True, text=True, cwd=temp_dir)
            if proc.returncode > 1:
                print(f"--- STDERR ---\n{proc.stderr}")
                return -1.0

            if proc.returncode == 1:
                print({proc.stdout})

            json_command = ["coverage", "json", "-o", "coverage.json"]
            subprocess.run(json_command, check=True, capture_output=True, text=True, cwd=temp_dir)

            with open(os.path.join(temp_dir, "coverage.json"), "r") as f:
                coverage_data = json.load(f)

            return round(coverage_data.get("totals", {}).get("percent_covered", 0.0), 2)

        except FileNotFoundError:
            return -1.0
        except Exception as e:
            return -1.0


def evaluate_agent_coverage(get_code_func, get_test_func, log_path: str) -> float | None:

    final_code = get_code_func(log_path)
    raw_tests_output = get_test_func(log_path)
    raw_tests = "\n".join(raw_tests_output) if isinstance(raw_tests_output, list) else str(raw_tests_output)

    if not final_code:
        return None

    llm_json_response = standardize_tests_with_llm(final_code, raw_tests)

    if not llm_json_response:
        return -1.0

    try:
        start_index = llm_json_response.find('{')
        end_index = llm_json_response.rfind('}')
        if start_index == -1 or end_index == -1:
            return -1.0
        clean_json_str = llm_json_response[start_index : end_index + 1]
        parsed_data = json.loads(clean_json_str)
        standardized_tests = parsed_data.get("pytest_code")

        if not standardized_tests:
            return None
    except (json.JSONDecodeError, AttributeError):
        return -1.0

    coverage_result = calculate_coverage(final_code, standardized_tests)

    if coverage_result >= 0:
        print({coverage_result})
    return coverage_result

def batch_evaluate_directory(dir_path: str, get_code_func, get_test_func):
    results = []

    if not os.path.isdir(dir_path):
        return
    subdirectories = sorted([d for d in os.scandir(dir_path) if d.is_dir()], key=lambda d: d.name)

    for item in subdirectories:
        instruction_name = item.name
        log_path = os.path.join(item.path, "log.txt")

        if os.path.exists(log_path):
            coverage = evaluate_agent_coverage(get_code_func, get_test_func, log_path)
            results.append({
                "instruction": instruction_name,
                "Coverage": coverage
            })

    if results:
        df = pd.DataFrame(results)
        df['Coverage'] = df['Coverage'].apply(lambda x: 'Skipped' if x is None else ('Failed' if x == -1.0 else x))
        output_filename = "output.txt"

        print(df.to_string())
        df.to_csv(output_filename, sep='\t', index=True)


if __name__ == '__main__':
    TARGET_MAS = "agentcoder"
    DIR_PATH = "../Results/agentcoder/human"
    mas_functions = {
        "agentverse": (get_agentverse_code, get_agentverse_test),
        "agentcoder": (get_agentcoder_code, get_agentcoder_test),
        "chatdev": (get_chatdev_code, get_chatdev_test),
        "self": (get_self_code, get_self_test)
    }
    if TARGET_MAS in mas_functions:
        code_func, test_func = mas_functions[TARGET_MAS]
        batch_evaluate_directory(
            dir_path=DIR_PATH,
            get_code_func=code_func,
            get_test_func=test_func
        )
