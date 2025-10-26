from pathlib import Path
from analysis import single2,multi2
from util import bashAnalysis
import re
import pandas as pd
import json

class SelfAnalysis:

    def _load_log(self, log_path: Path) -> any:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                log_data = f.read()
            return log_data
        except OSError as e:
            print(e)
        except Exception as e:
            print(e)

        return None

    def get_Arch(self,log_path):
        log_data = self._load_log(log_path)
        pattern = re.compile(r"Analyst's Plan:\s*(.*?)\n---", re.DOTALL)

        matches = pattern.findall(log_data)

        if matches:
            arch_list = [code.strip() for code in matches]
            return arch_list
        else:
            return []
    def get_code(self,log_path):
        log_data = self._load_log(log_path)
        pattern = re.compile(r"Coder's Generated Code:\s*(.*?)\n---", re.DOTALL)

        matches = pattern.findall(log_data)
        if matches:
            code_list = [code.strip() for code in matches]
            return code_list
        else:
            return []

    def get_test(self,log_path):
        # Tester's Generated Tests:
        log_data = self._load_log(log_path)
        pattern = re.compile(r"Tester's Generated Tests:\s*(.*?)\n---", re.DOTALL)

        matches = pattern.findall(log_data)

        if matches:
            test_list = [code.strip() for code in matches]
            return test_list
        else:
            return []


    def analyze_single(self,log_path):
        arch_list = self.get_Arch(log_path)
        code_list = self.get_code(log_path)
        test_list = self.get_test(log_path)
        final_scores = {}

        # Arch
        arch_score_keys = ["Completeness", "Correctness", "Clarity", "Feasibility", "Modularity"]
        total_arch_scores = {key: 0 for key in arch_score_keys}
        if arch_list:
            for i, arch_doc in enumerate(arch_list):
                print(f"  Analyze #{i + 1}...")
                arch_score_dict = single2.analysis_plan(arch_doc)
                print(arch_score_dict)
                for key_capitalized in arch_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_arch_scores[key_capitalized] += arch_score_dict.get(dict_key_lowercase, 0)

            for key in arch_score_keys:
                avg_score = total_arch_scores[key] / len(arch_list)
                # print(avg_score)
                final_scores[f'avg_arch_{key.lower()}_score'] = avg_score
        else:
            for key in arch_score_keys:
                final_scores[f'avg_arch_{key.lower()}_score'] = -999

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

        # Test
        test_score_keys = ["Boundary", "Function", "Other"]
        total_test_scores = {key: 0 for key in test_score_keys}

        if test_list:
            for i, test_doc in enumerate(test_list):
                test_score_dict = single2.analysis_test(test_doc)
                print(test_score_dict)
                for key_capitalized in test_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_test_scores[key_capitalized] += test_score_dict.get(dict_key_lowercase, 0)

            for key in test_score_keys:
                avg_score = total_test_scores[key] / len(test_list)
                # print(avg_score)
                final_scores[f'avg_test_{key.lower()}_score'] = avg_score
        else:
            for key in test_score_keys:
                final_scores[f'avg_test_{key.lower()}_score'] = -999

        return final_scores

    def analyze_multi(self,log_path):
        arch_list = self.get_Arch(log_path)
        code_list = self.get_code(log_path)
        test_list = self.get_test(log_path)
        final_scores = {}


        # arch2Code
        arch_code_keys = ["Accuracy", "Redundancy"]
        for key in arch_code_keys:
            final_scores[f'avg_arch_code_{key.lower()}_score'] = -999

        if arch_list and code_list:

            first_arch = arch_list[0]
            first_code = code_list[0]
            score_dict = multi2.analysis_plan_code(first_arch, first_code)
            print(f"    ↳  scores: {score_dict}")

            for key in arch_code_keys:
                score = score_dict.get(key.lower(), None)
                final_key = f'avg_arch_code_{key.lower()}_score'
                final_scores[final_key] = score

        return final_scores

    def analyze_performance(self,log_path):
        performance_summary = {
            'Analyst': {'time': 0, 'tokens': 0},
            'Code': {'time': 0, 'tokens': 0},
            'Test': {'time': 0, 'tokens': 0}
        }
        log_data = self._load_log(log_path)

        pattern = re.compile(r"--- Final Session History \(for output\.jsonl\) ---\s*(\{.*\})", re.DOTALL)
        match = pattern.search(log_data)

        if not match:
            return None

        json_string = match.group(1)

        try:
            log_data = json.loads(json_string)
        except json.JSONDecodeError as e:
            return None

        try:
            if 'plan_performance' in log_data:
                plan_perf = log_data['plan_performance']
                performance_summary['Analyst']['time'] = plan_perf.get('duration', 0)
                if 'usage' in plan_perf and plan_perf['usage']:
                    performance_summary['Analyst']['tokens'] = plan_perf['usage'].get('total_tokens', 0)

            for key, round_data in log_data.items():
                if key.startswith("Round_"):
                    if 'code_performance' in round_data and round_data['code_performance']:
                        code_perf = round_data['code_performance']
                        performance_summary['Code']['time'] += code_perf.get('duration', 0)
                        if 'usage' in code_perf and code_perf['usage']:
                            performance_summary['Code']['tokens'] += code_perf['usage'].get('total_tokens', 0)

                    if 'tests_performance' in round_data and round_data['tests_performance']:
                        tests_perf = round_data['tests_performance']
                        performance_summary['Test']['time'] += tests_perf.get('duration', 0)
                        if 'usage' in tests_perf and tests_perf['usage']:
                            performance_summary['Test']['tokens'] += tests_perf['usage'].get('total_tokens', 0)

        except (KeyError, TypeError) as e:
            return None

        return performance_summary

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

    def bash_performance(self,dir_path):

        def performance_wrapper(log_path: str) -> dict:

            nested_dict = self.analyze_performance(log_path)

            flat_dict = {}
            if nested_dict:
                for agent, data in nested_dict.items():
                    #  'Programmer' -> 'programmer_time', 'programmer_tokens'
                    agent_key_prefix = agent.replace(" ", "_").lower()
                    flat_dict[f'{agent_key_prefix}_time'] = data.get('time', 0)
                    flat_dict[f'{agent_key_prefix}_tokens'] = data.get('tokens', 0)
            return flat_dict

        df = bashAnalysis.process_and_report_generic(dir_path, performance_wrapper)

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

if __name__=='__main__':
    log_path = "../logTest/log.txt"
    dir_path = "../Results/self-3.5/part3"
    # log_path ="G:/python/MASProject/Results/self/instruction0/4/log.txt"
    analysis = SelfAnalysis()
    result = analysis.bash_multi(dir_path)
    result.to_csv('output.txt', sep='\t', index=True)
    # print(result)
    # print(len(result))