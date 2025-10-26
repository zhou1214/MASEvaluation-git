import collections
from pathlib import Path
import re
from typing import Optional, Callable

import pandas as pd

from analysis import single2, multi2
from util import bashAnalysis
import metagptHuman


class MetagptAnalysis:
    def _load_log(self, txt_path):
        if not txt_path:
            return []
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
                return [content]
        except FileNotFoundError:
            return []
        except Exception as e:
            return []

    def load_log_out(self, txt_path):
        if not txt_path:
            return []
        try:
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
                return [content]
        except FileNotFoundError:
            return []
        except Exception as e:
            return []

    def find_file(self, dirNum_path: str, name: str) -> str | None:

        directory = Path(dirNum_path)
        if not directory.is_dir():
            return None

        target_filename = f"{name}.txt"

        target_file = directory / target_filename
        if target_file.is_file():
            return str(target_file.resolve())
        else:
            return None

    def analyze_single(self, dirNum_path):
        prd_path = self.find_file(dirNum_path, "prd")
        prd_list = self._load_log(prd_path)

        arch_path = self.find_file(dirNum_path, "arch")
        arch_list = self._load_log(arch_path)

        # code_path = self.find_file(dirNum_path,"code")
        code_list = metagptHuman.extract_code(dirNum_path)
        final_scores = {}

        # PRD
        prd_score_keys = ["Final"]
        total_prd_scores = {key: 0 for key in prd_score_keys}
        if prd_list:
            for i, prd_doc in enumerate(prd_list):
                print(f"  PRD #{i + 1}...")
                prd_score_dict = single2.analysis_PRD(prd_doc)
                for key_capitalized in prd_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_prd_scores[key_capitalized] += prd_score_dict.get(dict_key_lowercase, 0)

            for key in prd_score_keys:
                avg_score = total_prd_scores[key] / len(prd_list)
                # print(avg_score)
                final_scores[f'avg_prd_{key.lower()}_score'] = avg_score
        else:
            for key in prd_score_keys:
                final_scores[f'avg_prd_{key.lower()}_score'] = -999

        # Arch
        arch_score_keys = ["Final"]
        total_arch_scores = {key: 0 for key in arch_score_keys}
        if arch_list:
            for i, arch_doc in enumerate(arch_list):
                print(f"  Arch #{i + 1}...")
                arch_score_dict = single2.analysis_Arch(arch_doc)
                for key_capitalized in arch_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_arch_scores[key_capitalized] += arch_score_dict.get(dict_key_lowercase, 0)

            for key in arch_score_keys:
                avg_score = total_arch_scores[key] / len(arch_list)
                final_scores[f'avg_arch_{key.lower()}_score'] = avg_score
        else:
            for key in arch_score_keys:
                final_scores[f'avg_arch_{key.lower()}_score'] = -999

        # code
        code_score_keys = ["Integrity", "Correctness", "Readability", "Efficiency"]
        total_code_scores = {key: 0 for key in code_score_keys}
        if code_list:
            for i, code_doc in enumerate(code_list):
                print(f"  Code #{i + 1}...")
                code_score_dict = single2.analysis_code(code_doc)
                for key_capitalized in code_score_keys:
                    dict_key_lowercase = key_capitalized.lower()
                    total_code_scores[key_capitalized] += code_score_dict.get(dict_key_lowercase, 0)

            for key in code_score_keys:
                avg_score = total_code_scores[key] / len(code_list)
                final_scores[f'avg_code_{key.lower()}_score'] = avg_score
        else:
            for key in code_score_keys:
                final_scores[f'avg_code_{key.lower()}_score'] = -999

        return final_scores

    def analyze_multi(self, dirNum_path):
        prd_path = self.find_file(dirNum_path, "prd")
        prd_list = self._load_log(prd_path)

        arch_path = self.find_file(dirNum_path, "arch")
        arch_list = self._load_log(arch_path)

        # code_path = self.find_file(dirNum_path, "code")
        code_list = metagptHuman.extract_code(dirNum_path)
        final_scores = {}

        # PRD2Arch
        prd_arch_keys = ["Accuracy", "Redundancy"]
        for key in prd_arch_keys:
            final_scores[f'avg_prd_arch_{key.lower()}_score'] = -999

        if prd_list and arch_list:
            first_prd = prd_list[0]
            first_arch = arch_list[0]
            score_dict = multi2.analysis_prd_arch(first_prd, first_arch)
            print(f"    ↳  scores: {score_dict}")

            for key in prd_arch_keys:
                score = score_dict.get(key.lower(), -999)
                final_key = f'avg_prd_arch_{key.lower()}_score'
                final_scores[final_key] = score


        # Arch2Code
        arch_code_keys = ["File", "Data", "Calling", "Functionality"]
        for key in arch_code_keys:
            final_scores[f'avg_arch_code_{key.lower()}_score'] = -999

        if arch_list and code_list:
            first_arch = arch_list[0]
            first_code = code_list[0]
            score_dict = multi2.analysis_arch_code(first_arch, first_code)
            print(f"    ↳  scores: {score_dict}")

            for key in arch_code_keys:
                score = score_dict.get(key.lower(), -999)
                final_key = f'avg_arch_code_{key.lower()}_score'
                final_scores[final_key] = score


        return final_scores

    def analyze_performance(self, dirNum_path):
        log_path = self.find_file(dirNum_path, "log")

        agent_stats = collections.defaultdict(lambda: {'time_cost': 0.0, 'total_tokens': 0})
        agent_pattern = re.compile(r"metagpt\..*?:\d+ - (\w+)\(.*\)")

        perf_pattern = re.compile(
            r"LLM Performance: Time cost: ([\d.]+)s.*?Total tokens: (\d+)"
        )

        current_agent = None

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    agent_match = agent_pattern.search(line)
                    if agent_match:
                        current_agent = agent_match.group(1)
                    perf_match = perf_pattern.search(line)
                    if perf_match and current_agent:
                        time_cost = float(perf_match.group(1))
                        total_tokens = int(perf_match.group(2))

                        agent_stats[current_agent]['time_cost'] += time_cost
                        agent_stats[current_agent]['total_tokens'] += total_tokens

        except FileNotFoundError:
            return None

        return agent_stats

    def _run_analysis_batch(self,
                            dir_path: str,
                            analysis_func: Callable[[str], Optional[dict]],
                            analysis_title: str,
                            target_filename: Optional[str] = None):
        root_path = Path(dir_path)
        if not root_path.is_dir():
            return None

        try:
            instruction_paths = [p for p in root_path.iterdir() if p.is_dir() and p.name.startswith('instruction')]
            sorted_instructions = sorted(instruction_paths, key=lambda p: int(p.name.replace('instruction', '')))
        except ValueError:
            return None
        if not sorted_instructions:
            return None

        all_results = []
        for instruction_path in sorted_instructions:
            instruction_name = instruction_path.name

            if target_filename:
                path_to_analyze = instruction_path / target_filename
                if not path_to_analyze.is_file():
                    continue
            else:
                path_to_analyze = instruction_path

            try:
                result_dict = analysis_func(str(path_to_analyze))
                if result_dict:
                    result_dict['instruction'] = instruction_name
                    all_results.append(result_dict)
            except Exception as e:
                print(e)

        if not all_results:
            return None

        df = pd.DataFrame(all_results).fillna(0)
        if 'instruction' in df.columns:
            cols = ['instruction'] + [col for col in df.columns if col != 'instruction']
            df = df[cols]

        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

    def bash_single(self, dir_path: str) -> Optional[pd.DataFrame]:
        return self._run_analysis_batch(
            dir_path=dir_path,
            analysis_func=self.analyze_single,
            analysis_title="Single Analysis",
            target_filename=None
        )

    def bash_multi(self, dir_path: str) -> Optional[pd.DataFrame]:
        return self._run_analysis_batch(
            dir_path=dir_path,
            analysis_func=self.analyze_multi,
            analysis_title="Multi Analysis",
            target_filename=None
        )

    def _analyze_and_flatten_performance(self, log_path: str) -> Optional[dict]:
        nested_result_dict = self.analyze_performance(log_path)

        if not nested_result_dict:
            return None
        flat_result_dict = {}
        for agent_name, performance_data in nested_result_dict.items():
            flat_result_dict[f'{agent_name}_time_cost'] = performance_data.get('time_cost', 0)
            flat_result_dict[f'{agent_name}_total_tokens'] = performance_data.get('total_tokens', 0)

        return flat_result_dict

    def bash_performance(self, dir_path):
        return self._run_analysis_batch(
            dir_path=dir_path,
            analysis_func=self._analyze_and_flatten_performance,
            analysis_title="Performance Analysis",
            target_filename=None
        )


if __name__ == "__main__":
    dirnum_path = "../Results/Test"
    dir_path = "../Results/metagpt/part4"
    analysis = MetagptAnalysis()
    result = analysis.bash_multi(dir_path)
    # print(result)
    result.to_csv('output.txt', sep='\t', index=True)