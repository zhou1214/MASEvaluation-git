import os
import ast
import json
import re
import pandas as pd
from openai import OpenAI

from Prompt2 import Consistency





def check_syntax(code: str) -> bool:
    if not code or not code.strip():
        return False
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        return False


def get_content_from_file(file_path: str) -> str | None:
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return None


def load_tasks(file_path: str) -> list[str] | None:

    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tasks = [line.strip() for line in f.readlines()]
        return tasks
    except Exception as e:
        print(f"读取任务文件时出错 {file_path}: {e}")
        return None


def get_consistency_score(task: str, code: str, prompt_template: str):
    if not task or not code:
        return 0
    try:
        prompt = prompt_template.format(task=task, code=code)

        client = OpenAI(
            base_url=os.getenv('BASE_URL', ''),
            api_key=os.environ.get('OPENAI_API_KEY', ""),
        )

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an evaluator that scores code consistency."},
                {"role": "user", "content": prompt},
            ],
            stream=False,
            temperature=0.0
        )

        raw_output = response.choices[0].message.content.strip()
        cleaned_output = raw_output
        if cleaned_output.startswith("```json"):
            cleaned_output = cleaned_output[7:]
        if cleaned_output.endswith("```"):
            cleaned_output = cleaned_output[:-3]

        try:
            result_json = json.loads(cleaned_output)
            score = int(result_json.get("Consistency", {}).get("score", 0))
            analysis = result_json.get("Consistency", {}).get("analysis", "LLM 未提供分析文本。")
        except json.JSONDecodeError:

            return -1
        return score, analysis

    except Exception as e:
        return -1


def evaluate_project_directory(dir_path: str, tasks_file_path: str):


    tasks = load_tasks(tasks_file_path)
    if tasks is None:
        return

    if not os.path.isdir(dir_path):
        return

    results = []
    instruction_dirs = sorted(
        [d for d in os.listdir(dir_path) if d.startswith('instruction') and os.path.isdir(os.path.join(dir_path, d))],
        key=lambda x: int(re.search(r'\d+', x).group())
    )

    if not instruction_dirs:
        return

    for instruction_dir_name in instruction_dirs:
        instruction_path = os.path.join(dir_path, instruction_dir_name)
        # ------------------
        # code_file_path = os.path.join(instruction_path, "code.txt")
        code_file_path = os.path.join(instruction_path, "firstcode.txt")

        try:
            task_index = int(re.search(r'\d+', instruction_dir_name).group())
            task_content = tasks[task_index]
        except (IndexError, AttributeError, ValueError):
            continue

        code_content = get_content_from_file(code_file_path)
        if code_content is None:
            results.append(
                {'Instruction': instruction_dir_name, 'Compilable': False, 'Consistency': 0, 'WSS': 0.0,
                 'Message': 'code None'})
            continue

        is_compilable = check_syntax(code_content)
        compilation_status = 1 if is_compilable else 0

        consistency_score, analysis = get_consistency_score(task_content, code_content,
                                                            Consistency.LLM_PROMPT_TEMPLATE)

        if consistency_score == -1:
            normalized_consistency = 0.0
        else:
            normalized_consistency = consistency_score

        weighted_score = compilation_status * normalized_consistency

        results.append({
            'Instruction': instruction_dir_name,
            'Compilable': is_compilable,
            'Consistency (0-100)': consistency_score,
            'WSS': weighted_score,
        })

    if not results:
        return

    df = pd.DataFrame(results)
    total_count = len(df)
    compilation_success_rate = df['Compilable'].mean()
    avg_consistency_on_success = df[df['Compilable']]['Consistency (0-100)'].mean()
    final_wss_score = df['WSS'].mean()

    print("\n\n--- report ---")
    print(df.to_string())



if __name__ == "__main__":

    main_dir_path = "../Results/self-3.5/part3"

    # tasks_path = "../Others/part3-2.txt"
    tasks_path = "../Others/instructions-1.txt"
    evaluate_project_directory(main_dir_path, tasks_path)
