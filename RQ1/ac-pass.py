import io
import os
import re
import contextlib
from typing import Dict, List, Optional, Any
from datasets import load_dataset


class CodeAnalysisBase:

    def _load_log(self, log_path: str) -> Optional[str]:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            return None
        except Exception as e:
            return None

    def get_log_files(self, dir_path: str, file_name: str = 'log.txt') -> Dict[str, str]:
        log_files = {}
        if not os.path.isdir(dir_path):
            return log_files

        for item in os.listdir(dir_path):
            if item.startswith('instruction') and os.path.isdir(os.path.join(dir_path, item)):
                file_path = os.path.join(dir_path, item, file_name)
                if os.path.exists(file_path):
                    log_files[item] = file_path
        return log_files

    def _safe_exec(self, code_str: str) -> bool:
        try:
            exec_globals = {}
            with contextlib.redirect_stdout(io.StringIO()):
                exec(code_str, exec_globals)
            return True
        except Exception:
            return False

    def _evaluate_pass1(self, code_dir: str, dataset_name: str, use_first_code: bool = False):
        if not load_dataset:
            return None

        if dataset_name == "HumanEval":
            dataset = load_dataset("openai/openai_humaneval")
            test_cases = {item["task_id"]: item for item in dataset["test"]}
        elif dataset_name == "MBPP":
            dataset = load_dataset("mbpp", split="test")
            test_cases = {int(item['task_id']): item for item in dataset}


        file_name = 'code.txt' if self.__class__.__name__ == "MetagptAnalysis" else 'log.txt'
        log_files = self.get_log_files(code_dir, file_name)
        if not log_files:

            return None

        total, passed = 0, 0
        results = []
        sorted_log_files = sorted(log_files.items(), key=lambda x: int(x[0].replace("instruction", "")))

        for instruction, file_path in sorted_log_files:
            instruction_num = int(instruction.replace("instruction", ""))

            code = self.get_first_code(file_path) if use_first_code else self.get_final_code(file_path)

            if not self._is_valid_code(code):
                results.append({
                    "instruction": instruction,
                    "pass": False,
                    "reason": "No valid code found"
                })
                total += 1
                continue

            if dataset_name == "HumanEval":
                task_id = f"HumanEval/{instruction_num}"
                if task_id not in test_cases:
                    total += 1
                    continue
                prompt = test_cases[task_id]["prompt"]
                test_code = test_cases[task_id]["test"]
                code_to_run = f"{prompt}\n{code}\n{test_code}"

            elif dataset_name == "MBPP":
                if instruction_num < 10:
                    continue
                task_id = instruction_num + 1
                if task_id not in test_cases:
                    results.append({
                        "instruction": instruction,
                        "task_id": task_id,
                        "pass": False,
                        "reason": "Task ID not found in dataset"
                    })
                    total += 1
                    continue
                test_code = "\n".join(test_cases[task_id]["test_list"])
                code_to_run = f"{code}\n{test_code}"

            success = self._safe_exec(code_to_run)
            if success:
                passed += 1
                print(f"  [pass] {task_id}")
            else:
                print(f"  [failed] {task_id}")

            results.append({
                "instruction": instruction,
                "task_id": task_id,
                "pass": bool(success)
            })
            total += 1

        pass_at_1 = passed / total if total > 0 else 0
        print(f"\n {dataset_name} pass@1 = {passed}/{total} = {pass_at_1:.3f}")
        return pass_at_1, results

    def _is_valid_code(self, code: str) -> bool:
        if not code:
            return False
        if "Error:" in code:
            return False
        return bool(code.strip())


class AgentverseAnalysis(CodeAnalysisBase):

    def get_final_code(self, log_path: str) -> str:
        log_content = self._load_log(log_path)
        if not log_content:
            return None

        pattern = re.compile(
            r"Final Result:\n(.*?)(?=\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}|$)",
            re.DOTALL
        )
        match = pattern.search(log_content)
        return match.group(1).strip()

    def get_first_code(self, log_path: str) -> str:

        log_content = self._load_log(log_path)
        if not log_content:
            return None

        pattern = re.compile(
            r"INFO Initial Plan:\n(.*?)(?=\n\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} INFO|$)",
            re.DOTALL
        )
        match = pattern.search(log_content)
        return match.group(1).strip()

    def evaluate_pass1_on_humaneval(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "HumanEval", use_first_code)

    def evaluate_pass1_on_mbpp(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "MBPP", use_first_code)


class SelfAnalysis(CodeAnalysisBase):

    def get_final_code(self, log_path: str) -> Optional[str]:
        log_data = self._load_log(log_path)
        if not log_data:
            return None

        pattern = re.compile(r"Coder's Generated Code:\s*(.*?)\n---", re.DOTALL)
        matches = pattern.findall(log_data)
        return matches[-1].strip() if matches else None

    def get_first_code(self, log_path: str) -> Optional[str]:
        log_data = self._load_log(log_path)
        if not log_data:
            return None

        pattern = re.compile(r"Coder's Generated Code:\s*(.*?)\n---", re.DOTALL)
        matches = pattern.findall(log_data)
        return matches[0].strip() if matches else None

    def evaluate_pass1_on_humaneval(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "HumanEval", use_first_code)

    def evaluate_pass1_on_mbpp(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "MBPP", use_first_code)


class MapcoderAnalysis(CodeAnalysisBase):

    def get_code(self, log_path: str) -> str:
        log_data = self._load_log(log_path)
        if not log_data:
            return ""

        pattern = re.compile(
            r"Response from final code generation:\s*\n(.*?)\n\n________________________",
            re.DOTALL
        )
        matches = pattern.findall(log_data)
        return matches[-1].strip() if matches else ""

    get_final_code = get_code
    get_first_code = get_code

    def evaluate_pass1_on_humaneval(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "HumanEval", use_first_code)

    def evaluate_pass1_on_mbpp(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "MBPP", use_first_code)


class MetagptAnalysis(CodeAnalysisBase):

    def get_code(self, code_path: str) -> str:
        try:
            with open(code_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return ""

    get_final_code = get_code
    get_first_code = get_code

    def _load_tasks(self, file_path: str) -> List[str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            return []

    def evaluate_pass1_on_humaneval(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "HumanEval", use_first_code)

    def evaluate_pass1_on_mbpp(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "MBPP", use_first_code)


class AgentcoderAnalysis(CodeAnalysisBase):
    def get_final_code(self, log_path: str) -> Optional[str]:
        log_data = self._load_log(log_path)
        if not log_data:
            return None

        try:
            import json
            log_json = json.loads(log_data)
            last_epoch = log_json['epochs'][-1]
            for step in reversed(last_epoch['steps']):
                if step.get('agent') == 'Test Executor':
                    code = step.get('best_code')
                    return code
            return None
        except Exception as e:
            return None

    def get_first_code(self, log_path: str) -> Optional[str]:

        log_data = self._load_log(log_path)
        if not log_data:
            return None

        try:
            import json
            log_json = json.loads(log_data)
            first_epoch = log_json['epochs'][0]
            for step in first_epoch['steps']:
                if step.get('agent') == 'Test Executor':
                    code = step.get('best_code')
                    return code if code else "Error: best_code为空"
            return None
        except Exception as e:
            return None

    def evaluate_pass1_on_humaneval(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "HumanEval", use_first_code)

    def evaluate_pass1_on_mbpp(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "MBPP", use_first_code)


class ChatDevAnalysis(CodeAnalysisBase):

    def get_final_code(self, log_path: str) -> str:
        log_content = self._load_log(log_path)
        if not log_content:
            return None

        block_pattern = re.compile(
            r'Ideas:\s*""\s*\nCodes:\s*(.*?)(?=\n\[\d{4}-\d{2}-\d{2}.*?INFO\])',
            re.DOTALL
        )
        matches = block_pattern.findall(log_content)
        if not matches:
            return None

        code_pattern = re.compile(r'```python\n(.*?)\n```', re.DOTALL)
        extracted_code = code_pattern.findall(matches[-1])
        return "\n\n".join(extracted_code) if extracted_code else "错误: 未提取到Python代码"

    def get_first_code(self, log_path: str) -> str:
        log_content = self._load_log(log_path)
        if not log_content:
            return ""

        start_keyword = 'on : Coding, turn 0'
        start_idx = log_content.find(start_keyword)
        if start_idx == -1:
            return ""

        end_match = re.search(r'\n\[\d{4}-\d{2}-\d{2}', log_content[start_idx:])
        end_idx = start_idx + end_match.start() if end_match else len(log_content)

        code_pattern = re.compile(r'```python\n(.*?)\n```', re.DOTALL)
        extracted_code = code_pattern.findall(log_content[start_idx:end_idx])
        return "\n\n".join(extracted_code) if extracted_code else ""

    def evaluate_pass1_on_humaneval(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "HumanEval", use_first_code)

    def evaluate_pass1_on_mbpp(self, code_dir: str, use_first_code: bool = False):
        return self._evaluate_pass1(code_dir, "MBPP", use_first_code)


if __name__ == "__main__":

    chatdev_analyzer = ChatDevAnalysis()
    chatdev_analyzer.evaluate_pass1_on_humaneval("../Results/chatdev/human")
    chatdev_analyzer.evaluate_pass1_on_mbpp("../Results/chatdev/mbpp")
