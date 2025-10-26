import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Tuple, List
import re

import pandas as pd

from analysis import single2,multi2
from util import bashAnalysis


class ChatDevAnalysis:

    def _load_log(self, log_path) -> any:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
                return log_content
        except FileNotFoundError:
            return []

    def _extract_content_by_role(self, log_path: str, roles: Tuple[str, str]) -> List[str]:
        assistant_role, user_role = roles
        log_data = self._load_log(log_path)

        blocks = log_data.split('System: **[chatting]**')
        extracted_contents = []
        timestamp_pattern = re.compile(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} INFO\]')

        assistant_role_marker = f'| **assistant_role_name** | {assistant_role} |'
        user_role_marker = f'| **user_role_name** | {user_role} |'
        capture_start_marker = f'INFO] {assistant_role}:'

        for block in blocks:
            if not (assistant_role_marker in block and user_role_marker in block):
                continue

            lines = block.split('\n')
            is_capturing = False
            captured_lines = []

            for line in lines:
                if capture_start_marker in line:
                    is_capturing = True
                    continue

                if is_capturing:
                    if timestamp_pattern.match(line):
                        break
                    captured_lines.append(line)

            if captured_lines:
                content = '\n'.join(captured_lines).strip()
                prompt_end_marker = ']'
                prompt_end_index = content.find(prompt_end_marker)
                actual_content = content[prompt_end_index + 1:].strip() if prompt_end_index != -1 else content
                if actual_content:
                    extracted_contents.append(actual_content)

        return extracted_contents

    def _extract_content_by_role_in_phase(self, log_path, phase_roles: Tuple[str, str], target_role_name: str) -> List[str]:

        log_data = self._load_log(log_path)
        assistant_role, user_role = phase_roles
        blocks = log_data.split('System: **[chatting]**')
        extracted_contents = []
        timestamp_pattern = re.compile(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} INFO\]')
        prompt_block_pattern = re.compile(r'\[.*?\]', re.DOTALL)
        assistant_role_marker = f'| **assistant_role_name** | {assistant_role} |'
        user_role_marker = f'| **user_role_name** | {user_role} |'
        capture_start_marker = f'INFO] {target_role_name}:'
        special_extraction_marker = "Comments on Codes:"
        is_special_case = (phase_roles == ("Programmer", "Code Reviewer") and target_role_name == "Code Reviewer")

        for block in blocks:
            if not (assistant_role_marker in block and user_role_marker in block):
                continue
            lines = block.split('\n')
            is_capturing = False
            captured_lines = []
            for line in lines:
                if capture_start_marker in line:
                    is_capturing = True
                    line_content = line.split(capture_start_marker, 1)[-1].strip()
                    if line_content: captured_lines.append(line_content)
                    continue
                if is_capturing:
                    if timestamp_pattern.match(line): break
                    captured_lines.append(line)
            if captured_lines:
                content = '\n'.join(captured_lines).strip()
                if is_special_case:
                    actual_content = content.split(special_extraction_marker, 1)[
                        1].strip() if special_extraction_marker in content else ""
                else:
                    actual_content = prompt_block_pattern.sub('', content).strip()
                if actual_content: extracted_contents.append(actual_content)
        return extracted_contents

    def get_init_code(self, log_path):
        roles = ("Programmer", "Chief Technology Officer")
        return self._extract_content_by_role(log_path, roles)

    def get_review(self, log_path) -> List[str]:
        roles = ("Code Reviewer", "Programmer")
        return self._extract_content_by_role(log_path, roles)

    # Code Reviewer -> Programmer
    def get_content(self, log_path, roles: Tuple[str, str], content_type: str) -> List[str]:

        if content_type == "review":
            target_role_name = "Code Reviewer"
        elif content_type == "code":
            target_role_name = "Programmer"

        return self._extract_content_by_role_in_phase(log_path,roles, target_role_name)

    def analyze_single(self, log_path) -> dict:


        code_list = self.get_init_code(log_path)
        test_list = self.get_review(log_path)
        final_scores = {}

        # Code
        code_score_keys = ["Integrity", "Correctness", "Readability", "Efficiency"]
        total_code_scores = {key: 0 for key in code_score_keys}
        if code_list:
            for i, code_doc in enumerate(code_list):
                print(f"  Code #{i + 1}...")
                code_score_dict = single2.analysis_code(code_doc)
                # print(code_score_dict)
                for key_capitalized in code_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_code_scores[key_capitalized] += code_score_dict.get(dict_key_lowercase, 0)

            for key in code_score_keys:
                avg_score = total_code_scores[key] / len(code_list)
                print(avg_score)
                final_scores[f'avg_code_{key.lower()}_score'] = avg_score
        else:
            for key in code_score_keys:
                final_scores[f'avg_code_{key.lower()}_score'] = -999

        # Test
        test_score_keys = ["Boundary", "Function", "Other"]
        total_test_scores = {key: 0 for key in test_score_keys}

        if test_list:
            for i, test_doc in enumerate(test_list):
                test_score_dict = single2.analysis_test(test_doc)
                # print(test_score_dict)
                for key_capitalized in test_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_test_scores[key_capitalized] += test_score_dict.get(dict_key_lowercase, 0)

            for key in test_score_keys:
                avg_score = total_test_scores[key] / len(test_list)
                print(avg_score)
                final_scores[f'avg_test_{key.lower()}_score'] = avg_score
        else:
            for key in test_score_keys:
                final_scores[f'avg_test_{key.lower()}_score'] = -999

        return final_scores

    def analyze_multi(self, log_path) -> dict:
        final_scores = {}

        # code2Test
        roles = ("Code Reviewer", "Programmer")
        code_list = self.get_content(log_path, roles, "code")
        test_list = self.get_content(log_path, roles, "review")

        code_test_keys = ["Functionality", "Accuracy", "Redundancy"]

        final_key_map = {
            key: f'avg_code_test_{key.lower().replace(" ", "_")}_score'
            for key in code_test_keys
        }

        for final_key in final_key_map.values():
            final_scores[final_key] = -999

        total_code_test_scores = {key: 0 for key in code_test_keys}

        num_code_test_pairs = min(len(code_list), len(test_list))
        if num_code_test_pairs > 0:

            for i, (code_doc, test_doc) in enumerate(zip(code_list, test_list)):
                score_dict = multi2.analysis_code_test(code_doc, test_doc)
                for key in code_test_keys:
                    dict_key = key.lower().replace(" ", "_")  # <--- 修正这一行
                    total_code_test_scores[key] += score_dict.get(dict_key, 0)

            for key in code_test_keys:
                avg_score = total_code_test_scores[key] / num_code_test_pairs
                final_key = final_key_map[key]  # 从映射中获取最终键名
                final_scores[final_key] = avg_score

        # Test2Code
        roles2 = ("Programmer", "Code Reviewer")
        code_list2 = self.get_content(log_path,roles2, "code")
        test_list2 = self.get_content(log_path,roles2, "review")

        test_code_keys = ["Accuracy", "Redundancy"]
        for key in test_code_keys:
            final_scores[f'avg_test_code_{key.lower()}_score'] = -999

        total_test_code_scores = {key: 0 for key in test_code_keys}

        num_test_code_pairs = 0
        if len(test_list2) > 0 and len(code_list2) >= len(test_list2):
            num_test_code_pairs = len(test_list2)-1

        if num_test_code_pairs > 0:

            for i in range(num_test_code_pairs):
                test_doc = test_list2[i]
                code_doc = code_list2[i + 1]
                score_dict = multi2.analysis_test_code(test_doc, code_doc)
                for key in test_code_keys:
                    total_test_code_scores[key] += score_dict.get(key.lower(), 0)

            for key in test_code_keys:
                avg_score = total_test_code_scores[key] / num_test_code_pairs
                final_scores[f'avg_test_code_{key.lower()}_score'] = avg_score


        return final_scores

    def bash_single(self,dir_path):
        df = bashAnalysis.process_and_report_generic(dir_path, self.analyze_single)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        return df

    def bash_multi(self,dir_path):
        df = bashAnalysis.process_and_report_generic(dir_path, self.analyze_multi)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

class ChatDevPerformance:
    def performance(self,log_path):
        ALLOWED_AGENTS = {
            "Chief Product Officer",
            "Chief Technology Officer",
            "Programmer",
            "Code Reviewer",
            "Software Test Engineer",
            "Chief Executive Officer"
        }

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            return None
        all_timestamps_in_log = []
        info_timestamps_str = re.findall(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) INFO\]', content)
        all_timestamps_in_log.extend([datetime.strptime(ts, '%Y-%d-%m %H:%M:%S') for ts in info_timestamps_str])

        end_timestamp_match = re.search(r'ChatDev Ends \((\d{14})\)', content)
        if end_timestamp_match:
            all_timestamps_in_log.append(datetime.strptime(end_timestamp_match.group(1), '%Y%m%d%H%M%S'))

        if not all_timestamps_in_log:
            return None

        last_log_timestamp = max(all_timestamps_in_log)

        block_info_pattern = re.compile(
            r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) INFO\] System: \*\*\[chatting\]\*\*',
            re.DOTALL
        )
        chatting_starts = list(block_info_pattern.finditer(content))

        if not chatting_starts:
            return None

        performance_data = defaultdict(lambda: {"time_costs": [], "token_costs": []})

        for i, start_match in enumerate(chatting_starts):
            start_pos = start_match.end()
            end_pos = chatting_starts[i + 1].start() if i + 1 < len(chatting_starts) else len(content)
            current_block_content = content[start_pos:end_pos]

            agent_name_match = re.search(r'\|\s+\*\*assistant_role_name\*\*\s+\|\s+(.*?)\s+\|', current_block_content)
            agent_name = agent_name_match.group(1).strip() if agent_name_match else "Unknown Agent"

            if agent_name not in ALLOWED_AGENTS:
                continue

            token_matches = re.findall(r'(?:total_tokens|num_total_tokens)[:=]\s*(\d+)', current_block_content)
            token_cost = sum(int(t) for t in token_matches)

            current_time = datetime.strptime(start_match.group(1), '%Y-%d-%m %H:%M:%S')
            next_time = datetime.strptime(chatting_starts[i + 1].group(1), '%Y-%d-%m %H:%M:%S') if i + 1 < len(
                chatting_starts) else last_log_timestamp
            time_cost = (next_time - current_time).total_seconds()

            performance_data[agent_name]["time_costs"].append(time_cost)
            performance_data[agent_name]["token_costs"].append(token_cost)

        return performance_data

    def print_detailed_report(self, performance_data):
        print("=" * 60)
        print("Aggregated Performance Summary")
        print("-" * 60)
        print(f"{'Agent Name':<30} | {'Total Time (sec)':>12} | {'Total Tokens':>12}")
        print("-" * 60)

        sorted_agents = sorted(performance_data.keys())

        for agent in sorted_agents:
            data = performance_data[agent]
            if not data['time_costs']:
                continue

            if agent == "Chief Product Officer":
                total_time = data['time_costs'][0]
                total_tokens = data['token_costs'][0]
            else:
                # 其他 Agent 正常计算总和
                total_time = sum(data['time_costs'])
                total_tokens = sum(data['token_costs'])

            print(f"{agent:<30} | {total_time:>12.2f} | {total_tokens:>12}")

        print("-" * 60)

    def run_bash(self, dir_path):
        root_path = Path(dir_path)
        if not root_path.is_dir():
            print(f"错误: 目录 '{dir_path}' 不存在。")
            return

        try:
            instruction_paths = [p for p in root_path.iterdir() if p.is_dir() and p.name.startswith('instruction')]
            sorted_instructions = sorted(instruction_paths, key=lambda p: int(p.name.replace('instruction', '')))
        except (ValueError, FileNotFoundError):
            return

        final_reports = {}

        for instruction_path in sorted_instructions:
            instruction_name = instruction_path.name

            log_path = instruction_path / 'log.txt'

            if not log_path.is_file():
                continue

            single_run_data = self.performance(str(log_path))
            if not single_run_data:
                continue

            report_data = {}
            for agent, costs in single_run_data.items():
                if not costs.get('time_costs'):
                    continue

                time_cost = 0
                token_cost = 0

                if agent == "Chief Product Officer":
                    time_cost = costs['time_costs'][0] if costs['time_costs'] else 0
                    token_cost = costs['token_costs'][0] if costs['token_costs'] else 0
                else:
                    time_cost = sum(costs['time_costs'])
                    token_cost = sum(costs['token_costs'])

                report_data[agent] = {
                    "time_cost": time_cost,
                    "token_cost": token_cost
                }

            final_reports[instruction_name] = report_data

        for instruction in sorted(final_reports.keys(), key=lambda x: int(x.replace('instruction', ''))):
            report_data = final_reports[instruction]

            print("=" * 70)
            print(f"--- Performance Report for: {instruction} ---")
            print("-" * 70)
            print(f"{'Agent Name':<30} | {'Time Cost (sec)':>15} | {'Total Tokens':>15}")
            print("-" * 70)
            for agent in sorted(report_data.keys()):
                cost_data = report_data[agent]
                print(f"{agent:<30} | {cost_data['time_cost']:>15.2f} | {cost_data['token_cost']:>15.0f}")

            print("-" * 70 + "\n")


if __name__ == "__main__":
    log_path = "../logTest/log.txt"
    dir_path = "../Results/chatdev/part2"
    # analysis = ChatDevAnalysis()
    # result = analysis.bash_multi(dir_path)
    # print(result)

    analysis = ChatDevPerformance()
    analysis.run_bash(dir_path)
    # result.to_csv('output.txt', sep='\t', index=True)