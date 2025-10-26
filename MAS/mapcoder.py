import json
import re

import pandas as pd

from analysis import single2,multi2
from util import bashAnalysis


def load_instructions_from_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            instructions = [line.strip() for line in f if line.strip()]
            return instructions
    except FileNotFoundError:
        print(f"错误: 指令文件未找到 at path: {filepath}")
        return []


class MapcoderAnalysis:
    instruction_list = load_instructions_from_file('../Others/part3-2.txt')

    def _load_log(self, log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
                return log_content
        except FileNotFoundError:
            return []

    def get_example(self, log_path):
        # Response from knowledge base and exemplars:
        # <description></description>
        # list
        log_data = self._load_log(log_path)
        start_marker = "Response from knowledge base and exemplars:"
        start_index = log_data.find(start_marker)

        if start_index == -1:
            return []

        content_to_search = log_data[start_index:]
        pattern = re.compile(r"<description><!\[CDATA\[(.*?)\]\]></description>", re.DOTALL)

        matches = pattern.findall(content_to_search)

        result_list = [match.strip() for match in matches]

        return result_list

    def get_planning(self, log_path):
        log_data = self._load_log(log_path)
        pattern = re.compile(
            r"Response from our problem planning:.*?# Planning:\n(.*?)\n-",
            re.DOTALL
        )
        matches = pattern.findall(log_data)
        result_list = [match.strip() for match in matches]
        return result_list

    def get_verification(self, log_path):
        log_data = self._load_log(log_path)
        pattern = re.compile(r"Response from planning verification:\s*\n({.*?})", re.DOTALL)
        matches = pattern.findall(log_data)
        result_list = [match.strip() for match in matches]
        return result_list

    def get_code_plan(self, log_path):
        # Input for final code generation:
        log_data = self._load_log(log_path)
        start_marker = "c:"
        start_index = log_data.find(start_marker)

        if start_index == -1:
            return []

        content_to_search = log_data[start_index:]

        pattern = re.compile(r"## Planning:\s*(.*?)\s*## Sample Test cases:", re.DOTALL)

        matches = pattern.findall(content_to_search)

        result_list = [match.strip() for match in matches]

        return result_list

    def get_code(self, log_path):
        log_data = self._load_log(log_path)

        pattern = re.compile(
            r"Response from final code generation:\s*\n(.*?)\n\n________________________",
            re.DOTALL
        )

        matches = pattern.findall(log_data)
        result_list = [match.strip() for match in matches]
        return result_list

    def analyze_single(self, log_path, instruction):

        example_list = self.get_example(log_path)
        codePlan_list = self.get_code_plan(log_path)
        code_list = self.get_code(log_path)

        final_scores = {}

        example_score_keys = ["Final"]
        total_example_scores = {key: 0 for key in example_score_keys}
        if example_list:
            for i, example_doc in enumerate(example_list):
                print(f"  Example #{i + 1}...")
                input = f"example:\n{example_doc}\ninstruction:{instruction}"
                example_score_dict = single2.analysis_example(input)
                print(example_score_dict)
                for key_capitalized in example_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_example_scores[key_capitalized] += example_score_dict.get(dict_key_lowercase, 0)

            for key in example_score_keys:
                avg_score = total_example_scores[key] / len(example_list)
                # print(avg_score)
                final_scores[f'avg_example_{key.lower()}_score'] = avg_score
        else:
            for key in example_score_keys:
                final_scores[f'avg_example_{key.lower()}_score'] = -999

        plan_score_keys = ["Completeness", "Correctness", "Clarity", "Feasibility", "Modularity"]
        total_plan_scores = {key: 0 for key in plan_score_keys}
        if codePlan_list:
            for i, plan_doc in enumerate(codePlan_list):
                print(f"  Plan #{i + 1}...")

                plan_score_dict = single2.analysis_plan(plan_doc)
                print(plan_score_dict)
                for key_capitalized in plan_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_plan_scores[key_capitalized] += plan_score_dict.get(dict_key_lowercase, 0)

            for key in plan_score_keys:
                avg_score = total_plan_scores[key] / len(codePlan_list)
                # print(avg_score)
                final_scores[f'avg_plan_{key.lower()}_score'] = avg_score
        else:
            for key in plan_score_keys:
                final_scores[f'avg_plan_{key.lower()}_score'] = -999

        # Code
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

        return final_scores

    def analyze_multi(self, log_path):
        plan_list = self.get_code_plan(log_path)
        code_list = self.get_code(log_path)
        final_scores = {}

        plan_code_keys = ["Accuracy", "Redundancy"]

        for key in plan_code_keys:
            formatted_key = key.lower().replace(' ', '_')
            final_scores[f'avg_plan_code_{formatted_key}_score'] = -999

        if plan_list and code_list:
            first_plan = plan_list[0]
            first_code = code_list[0]
            score_dict = multi2.analysis_plan_code(first_plan, first_code)
            print(f"    ↳  scores: {score_dict}")

            for key in plan_code_keys:
                lookup_key = key.lower().replace(' ', '_')
                score = score_dict.get(lookup_key, None)

                final_key = f'avg_plan_code_{lookup_key}_score'  # <--- 修改点 3
                final_scores[final_key] = score

        return final_scores

    # summary
    def analyze_performance1(self, log_path):

        log_data = self._load_log(log_path)
        pattern = re.compile(
            r"#################### PERFORMANCE SUMMARY ####################\s*(\{.*?\})\s*###########################################################",
            re.DOTALL
        )
        match = pattern.search(log_data)

        if not match:
            return {}

        json_text = match.group(1)

        try:
            performance_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            return {}

        stage_names = {
            '1': "Stage 1: Knowledge Generation",
            '2': "Stage 2: Problem Planning (Aggregated)",
            '3': "Stage 3: Planning Verification (Aggregated)",
            '4': "Stage 4: Final Code Generation"
        }

        stage_summary = {
            name: {'time': 0.0, 'total_tokens': 0.0}
            for name in stage_names.values()
        }

        for stage_key, metrics in performance_data.get("stages", {}).items():
            stage_number = stage_key[0]

            if stage_number in stage_names:
                summary_key = stage_names[stage_number]
                stage_summary[summary_key]['time'] += metrics.get('time_cost', 0.0)

                prompt_tokens = metrics.get('prompt_tokens', 0.0)
                completion_tokens = metrics.get('completion_tokens', 0.0)
                stage_summary[summary_key]['total_tokens'] += (prompt_tokens + completion_tokens)

        return stage_summary

    def analyze_performance(self, log_path):
        log_data = self._load_log(log_path)

        stage_summary = {
            "Stage 1: Knowledge Generation": {'time': 0.0, 'total_tokens': 0},
            "Stage 2: Problem Planning (Aggregated)": {'time': 0.0, 'total_tokens': 0},
            "Stage 3: Planning Verification (Aggregated)": {'time': 0.0, 'total_tokens': 0},
            "Stage 4: Final Code Generation": {'time': 0.0, 'total_tokens': 0}
        }

        pattern = re.compile(
            r"^(\w+)\s+([\d.]+)\s+(\d+)\s+(\d+)",
            re.MULTILINE
        )

        matches = pattern.findall(log_data)

        if not matches:
            return {}
        for match in matches:
            stage_name, time_str, in_tokens_str, out_tokens_str = match

            time = float(time_str)
            total_tokens = int(in_tokens_str) + int(out_tokens_str)

            if stage_name.startswith("Knowledge_Base_Generation"):
                summary_key = "Stage 1: Knowledge Generation"
            elif stage_name.startswith("Planning_Generation"):
                summary_key = "Stage 2: Problem Planning (Aggregated)"
            elif stage_name.startswith("Planning_Verification"):
                summary_key = "Stage 3: Planning Verification (Aggregated)"
            elif stage_name.startswith("Final_Code_Generation"):
                summary_key = "Stage 4: Final Code Generation"
            else:
                continue

            stage_summary[summary_key]['time'] += time
            stage_summary[summary_key]['total_tokens'] += total_tokens

        return stage_summary

    def bash_single(self, dir_path):

        log_groups = bashAnalysis.get_log_groups(dir_path)
        if not log_groups:
            return None

        all_results = []
        sorted_instruction_names = sorted(log_groups.keys(), key=lambda x: int(x.replace('instruction', '')))

        for instruction_name in sorted_instruction_names:
            log_paths = log_groups[instruction_name]

            try:
                instruction_index = int(instruction_name.replace('instruction', ''))
                current_instruction_text = self.instruction_list[instruction_index]
            except (ValueError, IndexError) as e:
                continue
            group_scores = {}
            valid_logs_count = 0

            for log_path in log_paths:
                try:
                    result_dict = self.analyze_single(log_path, current_instruction_text)

                    if result_dict:
                        valid_logs_count += 1
                        for key, value in result_dict.items():
                            if isinstance(value, (int, float)) and value is not None:
                                group_scores[key] = group_scores.get(key, 0) + value
                except Exception as e:
                    print(e)

            if valid_logs_count > 0:
                avg_scores = {key: val / valid_logs_count for key, val in group_scores.items()}
                avg_scores['instruction'] = instruction_name
                all_results.append(avg_scores)

        if not all_results:
            return None

        df = pd.DataFrame(all_results).fillna(0)
        if 'instruction' in df.columns:
            df = df[['instruction'] + [col for col in df.columns if col != 'instruction']]

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

    def bash_multi(self, dir_path):
        df = bashAnalysis.process_and_report_generic(dir_path, self.analyze_multi)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

    def bash_performance(self, dir_path):

        def performance_wrapper(log_path: str) -> dict:
            nested_dict = self.analyze_performance(log_path)

            flat_dict = {}
            if nested_dict:
                for stage_name, data in nested_dict.items():
                    prefix = stage_name.lower()
                    prefix = re.sub(r'[^a-z0-9\s]', '', prefix)
                    prefix = prefix.replace(" ", "_")
                    flat_dict[f'{prefix}_time'] = data.get('time', 0)
                    flat_dict[f'{prefix}_total_tokens'] = data.get('total_tokens', 0)

            return flat_dict

        df = bashAnalysis.process_and_report_generic(dir_path, performance_wrapper)

        if df is not None:
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1200)

        return df


if __name__ == "__main__":
    log_path = '../Results/mapcoder/part3/instruction1/log.txt'
    dir_path = "../Results/mapcoder/Mapcoderoutput-part3-2"
    instruction = "write a program implement a snake game based on pygame"
    analysis = MapcoderAnalysis()
    result = analysis.bash_performance(dir_path)
    # print(result)
    result.to_csv('output.txt', sep='\t', index=True)
