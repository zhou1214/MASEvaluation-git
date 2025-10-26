
import re
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional

import pandas as pd

from analysis import single2,multi2
from util import bashAnalysis

MODEL_PRICES = {
    "gpt-3.5-turbo_average": 0.75,
}


class AgentVerseAnalysis:

    def _load_log(self, log_path) -> any:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
                return log_content
        except FileNotFoundError:
            return []

    def _parse_log_file(self, log_path: str) -> List[Tuple[str, str, str, str]]:
        log_content = self._load_log(log_path)
        log_chunks = re.split(r'(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', log_content)

        parsed_data = []
        header_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\s+([A-Z]+)\s*(.*)", re.DOTALL)

        for chunk in log_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            lines = chunk.split('\n')
            first_line = lines[0]
            match = header_pattern.match(first_line)
            if not match:
                continue

            timestamp, log_type, message = match.group(1), match.group(2).capitalize(), match.group(3).strip()
            content_lines = lines[1:]
            title = ""

            if ':' in message:
                parts = message.split(':', 1)
                title = parts[0].strip()
                first_line_content = parts[1].strip()
                if first_line_content:
                    content_lines.insert(0, first_line_content)
            else:
                if message:
                    content_lines.insert(0, message)

            content = "\n".join(content_lines).strip()
            parsed_data.append((timestamp, log_type, title, content))

        return parsed_data

    def _parse_log_content(self, log_path: str, title_to_find: str) -> List[str]:

        parsed_logs = self._parse_log_file(log_path)

        if not parsed_logs:
            return []

        found_contents = [
            content for timestamp, log_type, title, content in parsed_logs
            if title == title_to_find
        ]

        return found_contents

    def get_Role(self, log_path):
        role_contents = self._parse_log_content(log_path, "Role Assignment")
        if role_contents:
            return role_contents
        else:
            return []

    def get_Code_init(self, log_path):
        #
        role_contents = self._parse_log_content(log_path, "Initial Plan")
        if role_contents:
            return role_contents
        else:
            return []

    def get_code_update(self, log_path):
        role_contents = self._parse_log_content(log_path, "Updated Plan")
        if role_contents:
            return role_contents
        else:
            return []

    def get_combine_code(self, log_path):
        code1 = self.get_Code_init(log_path)
        code2 = self.get_code_update(log_path)
        return code1 + code2

    def get_critic(self, log_path):
        role_contents = self._parse_log_content(log_path, "Reviews")
        if role_contents:
            return role_contents
        else:
            return []

    def get_evaluation(self, log_path):
        role_contents = self._parse_log_content(log_path, "Evaluation result")
        if role_contents:
            return role_contents
        else:
            return []

    def get_evaluation_score(self, content):
        if not content:
            return 0
        for result_string in content:
            if "Score: True" in result_string:
                return 1
        return 0

    def analyze_single(self, log_path) -> dict:
        role_list = self.get_Role(log_path)
        code_list = self.get_Code_init(log_path)
        critic_list = self.get_critic(log_path)
        evaluation_list = self.get_evaluation(log_path)
        final_scores = {}

        role_score_keys = ["Final"]
        total_role_scores = {key: 0 for key in role_score_keys}
        if role_list:
            for i, role_doc in enumerate(role_list):
                print(f"  role #{i + 1}...")
                role_score_dict = single2.analysis_role(role_doc)
                print(role_score_dict)
                for key_capitalized in role_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_role_scores[key_capitalized] += role_score_dict.get(dict_key_lowercase, 0)

            for key in role_score_keys:
                avg_score = total_role_scores[key] / len(role_list)
                # print(avg_score)
                final_scores[f'avg_role_{key.lower()}_score'] = avg_score
        else:
            for key in role_score_keys:
                final_scores[f'avg_role_{key.lower()}_score'] = -999

        # code
        code_score_keys = ["Integrity", "Correctness", "Readability", "Efficiency"]
        total_code_scores = {key: 0 for key in code_score_keys}
        if code_list:
            for i, code_doc in enumerate(code_list):
                print(f"  Code #{i + 1}...")
                code_score_dict = single2.analysis_code(code_doc)
                print(code_score_dict)
                for key_capitalized in code_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_code_scores[key_capitalized] += code_score_dict.get(dict_key_lowercase, 0)

            for key in code_score_keys:
                avg_score = total_code_scores[key] / len(code_list)
                # print(avg_score)
                final_scores[f'avg_code_{key.lower()}_score'] = avg_score
        else:
            for key in code_score_keys:
                final_scores[f'avg_code_{key.lower()}_score'] = -999

        # critic
        critic_score_keys = ["Integrity", "Correctness", "Readability", "Efficiency"]
        total_critic_scores = {key: 0 for key in critic_score_keys}
        if critic_list:
            for i, critic_doc in enumerate(critic_list):
                print(f"  Critic #{i + 1}...")
                critic_score_dict = single2.analysis_code(critic_doc)
                print(critic_score_dict)
                for key_capitalized in critic_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_critic_scores[key_capitalized] += critic_score_dict.get(dict_key_lowercase, 0)

            for key in critic_score_keys:
                avg_score = total_critic_scores[key] / len(critic_list)
                # print(avg_score)
                final_scores[f'avg_critic_{key.lower()}_score'] = avg_score
        else:
            for key in critic_score_keys:
                final_scores[f'avg_critic_{key.lower()}_score'] = -999

        # evaluation
        if evaluation_list:
            scores = self.get_evaluation_score(evaluation_list)
            final_scores['avg_evaluation_score'] = scores
        else:
            final_scores['avg_evaluation_score'] = -999

        return final_scores

    def analyze_multi(self, log_path) -> dict:
        code_list = self.get_combine_code(log_path)
        critic_list = self.get_critic(log_path)
        final_scores = {}

        # Code2Tese
        code_test_keys = ["Functionality", "Accuracy", "Redundancy"]

        final_key_map = {
            key: f'avg_code_test_{key.lower().replace(" ", "_")}_score'
            for key in code_test_keys
        }

        for final_key in final_key_map.values():
            final_scores[final_key] = -999

        total_code_test_scores = {key: 0 for key in code_test_keys}

        num_code_test_pairs = min(len(code_list), len(critic_list))
        if num_code_test_pairs > 0:

            for i, (code_doc, critic_doc) in enumerate(zip(code_list, critic_list)):
                score_dict = multi2.analysis_code_test(code_doc, critic_doc)
                print(f"    ↳  scores: {score_dict}")
                for key in code_test_keys:
                    dict_key = key.lower()
                    total_code_test_scores[key] += score_dict.get(dict_key, 0)

            for key in code_test_keys:
                avg_score = total_code_test_scores[key] / num_code_test_pairs
                final_key = final_key_map[key]
                final_scores[final_key] = avg_score

        critic_code_keys = ["Accuracy", "Redundancy"]
        for key in critic_code_keys:
            unified_key = key.lower().replace(" ", "_")
            final_scores[f'avg_critic_code_{unified_key}_score'] = -999

        total_critic_code_scores = {key: 0 for key in critic_code_keys}

        num_critic_code_pairs = 0
        if len(critic_list) > 0 and len(code_list) >= len(critic_list):
            num_critic_code_pairs = len(critic_list) - 1


        if num_critic_code_pairs > 0:

            for i in range(num_critic_code_pairs):
                critic_doc = critic_list[i]
                code_doc = code_list[i + 1]
                score_dict = multi2.analysis_critic_code(critic_doc, code_doc)
                print(f"    ↳  score: {score_dict}")
                for key in critic_code_keys:
                    lookup_key = key.lower().replace(" ", "_")
                    total_critic_code_scores[key] += score_dict.get(lookup_key, 0)
            for key in critic_code_keys:
                avg_score = total_critic_code_scores[key] / num_critic_code_pairs
                unified_key = key.lower().replace(" ", "_")
                final_scores[f'avg_critic_code_{unified_key}_score'] = avg_score

        return final_scores

    def bash_single(self, dir_path):
        df = bashAnalysis.process_and_report_generic(dir_path, self.analyze_single)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

    def bash_multi(self, dir_path):
        df = bashAnalysis.process_and_report_generic(dir_path, self.analyze_multi)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df


class PerformanceAnalysis:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        if not self.root_dir.is_dir():
            raise FileNotFoundError(f"file not found: {root_dir}")
        self.final_reports = {}

    def run_batch(self):
        self._find_and_process_logs()
        if not self.final_reports:
            return
        self._print_report()

    def _find_and_process_logs(self):
        log_files = sorted(list(self.root_dir.glob('instruction*/log.txt')))
        for log_path in log_files:
            try:
                instruction_name = log_path.parent.name
                analyzer = OutputAnalysis(str(log_path), "")
                performance_data = analyzer.log_performance()

                if performance_data:
                    self.final_reports[instruction_name] = performance_data
            except Exception as e:
                print(log_path)

    def _print_report(self):

        sorted_instruction_names = sorted(self.final_reports.keys(), key=lambda x: int(x.replace('instruction', '')))

        for instruction_name in sorted_instruction_names:
            report_data = self.final_reports[instruction_name]
            print(f"{'Agent':<17} | {'Time (s)':>15} | {'Tokens':>15}")
            print(f"{'-' * 17}-+-{'-' * 15}-+-{'-' * 15}")
            agent_order = ["Role Assignment", "Solver", "Critic", "Evaluation"]
            for agent_name in agent_order:
                if agent_name in report_data:
                    metrics = report_data[agent_name]
                    print(f"{agent_name:<17} | "
                          f"{metrics.get('time', 0):>15.2f} | "
                          f"{metrics.get('token', 0):>15.0f}")


class OutputAnalysis:
    def __init__(self, log_file_path: str, output_path: str):

        self.file_path = log_file_path  # log.txt
        self.output_path = output_path  # mytask.txt
        self.parsed_logs: Optional[List[Tuple[str, str, str, str]]] = None

    def log_analysis(self) -> List[Tuple[str, str, str, str]]:
        # timestamp type title content
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
        except FileNotFoundError:
            return []

        log_chunks = re.split(r'(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', log_content)
        parsed_data = []
        header_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3}\s+([A-Z]+)\s*(.*)", re.DOTALL)

        for chunk in log_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            lines = chunk.split('\n')
            first_line = lines[0]
            match = header_pattern.match(first_line)
            if not match:
                continue

            timestamp = match.group(1)
            log_type = match.group(2).capitalize()
            message = match.group(3).strip()

            content_lines = lines[1:]

            title = ""
            if ':' in message:
                parts = message.split(':', 1)
                title = parts[0].strip()
                first_line_of_content = parts[1].strip()
                if first_line_of_content:
                    content_lines.insert(0, first_line_of_content)
            else:
                if message:
                    content_lines.insert(0, message)
            content = "\n".join(content_lines).strip()
            if not title and len(lines) == 1 and (content.endswith('.') or content.endswith('!')):
                title = content
                content = ''

            parsed_data.append((timestamp, log_type, title, content))

        self.parsed_logs = parsed_data
        return self.parsed_logs

    def log_performance(self):
        self.parsed_logs = self.log_analysis()
        performance_data = {
            "Role Assignment": {"time": 0.0, "cost": 0.0},
            "Solver": {"time": 0.0, "cost": 0.0},
            "Critic": {"time": 0.0, "cost": 0.0},
            "Evaluation": {"time": 0.0, "cost": 0.0},
        }

        for i in range(len(self.parsed_logs) - 1):
            current_log = self.parsed_logs[i]
            next_log = self.parsed_logs[i + 1]

            time_format = "%Y-%m-%d %H:%M:%S"
            try:
                start_time = datetime.strptime(current_log[0], time_format)
                end_time = datetime.strptime(next_log[0], time_format)
            except ValueError:
                continue
            duration = (end_time - start_time).total_seconds()
            current_title = current_log[2]

            if current_title == "Role Assignment":
                performance_data["Role Assignment"]["time"] += duration
            elif "Plan" in current_title:
                performance_data["Solver"]["time"] += duration
            elif "Reviews" in current_title:
                performance_data["Critic"]["time"] += duration
            elif current_title == "Evaluation result":
                performance_data["Evaluation"]["time"] += duration

        cost_mapping = {
            "ROLE_ASSIGNMENT": "Role Assignment", "SOLVER": "Solver",
            "CRITIC": "Critic", "EVALUATION": "Evaluation",
        }
        cost_pattern = re.compile(r"Agent \(Role: AGENT_TYPES\.(\w+)\).*?\$([\d.]+)")
        for log_entry in self.parsed_logs:
            full_message = log_entry[2] + ": " + log_entry[3]
            match = cost_pattern.search(full_message)
            if match:
                role_type, cost_str = match.groups()
                agent_name = cost_mapping.get(role_type)
                if agent_name:
                    performance_data[agent_name]["cost"] = float(cost_str)

        price_per_million_tokens = MODEL_PRICES.get("gpt-3.5-turbo_average", 0)
        if price_per_million_tokens > 0:
            for agent_name, metrics in performance_data.items():
                cost = metrics.get("cost", 0.0)
                estimated_tokens = (cost / price_per_million_tokens) * 1_000_000
                metrics["token"] = round(estimated_tokens)

        final_result = {}
        for agent_name, metrics in performance_data.items():
            final_result[agent_name] = {
                "time": metrics["time"],
                "token": metrics["token"]
            }

        return final_result


if __name__ == "__main__":
    log_path = "../Results/agentverse/log.txt"
    dir_path = "../Results/agentverse/part3"
    # analysis = AgentVerseAnalysis()
    # score = analysis.bash_multi(dir_path)
    # # print(score)
    # score.to_csv('output.txt', sep='\t', index=True)

    # performance
    per = PerformanceAnalysis(dir_path)
    per.run_batch()
