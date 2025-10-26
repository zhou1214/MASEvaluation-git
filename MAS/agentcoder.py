
import json
from pathlib import Path
from analysis import single2,multi2
from util import bashAnalysis
import pandas as pd


class AgentCoderAnalysis:
    def _load_log(self, log_path: Path) -> any:
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            return None
    def get_code(self,log_path):
        code_list = []
        log_data = self._load_log(log_path)

        epochs = log_data.get("epochs", [])
        if not epochs:
            return []

        for epoch in epochs:
            epoch_number = epoch.get("epoch", "N/A")

            current_epoch_programmer_outputs = []
            steps = epoch.get("steps", [])
            for step in steps:
                if step.get("agent") == "Programmer":
                    outputs = step.get("outputs", [])
                    current_epoch_programmer_outputs.extend(outputs)
            if current_epoch_programmer_outputs:
                separator = "\n\n" + "=" * 25 + " NEXT CODE VERSION IN SAME EPOCH " + "=" * 25 + "\n\n"
                combined_code = separator.join(current_epoch_programmer_outputs)
                code_list.append(combined_code)
        return code_list

    def get_test(self,log_path):
        test_list = []
        log_data = self._load_log(log_path)

        epochs = log_data.get("epochs", [])
        if not epochs:
            return []

        for epoch in epochs:
            epoch_number = epoch.get("epoch", "N/A")
            current_epoch_test_outputs = []
            steps = epoch.get("steps", [])
            for step in steps:
                if step.get("agent") == "Test Designer":
                    outputs = step.get("outputs", [])
                    current_epoch_test_outputs.extend(outputs)

            if current_epoch_test_outputs:
                separator = "\n\n" + "=" * 25 + " NEXT Test VERSION IN SAME EPOCH " + "=" * 25 + "\n\n"
                combined_code = separator.join(current_epoch_test_outputs)
                test_list.append(combined_code)
        return test_list


    def get_best_tests(self, log_path: Path) -> list[str]:
        log_data = self._load_log(log_path)
        best_tests_list = []
        epochs = log_data.get("epochs", [])
        if not epochs:
            return []

        for i, epoch in enumerate(epochs):
            best_tests_found = None
            steps = epoch.get("steps", [])
            for step in steps:
                if step.get("agent") == "Test Executor":
                    best_tests_found = step.get("best_tests")
                    break
            if best_tests_found:
                best_tests_list.append(best_tests_found)
            else:

                best_tests_list.append(None)

        return best_tests_list

    def analysis_Test_Code_Exe(self,log_path):
        log_data = self._load_log(log_path)

        scores_list = []
        epochs = log_data.get("epochs", [])
        for epoch in epochs:
            epoch_number = epoch.get("epoch")

            programmer_outputs = []
            test_designer_outputs = []
            executor_best_code = None
            executor_best_tests = None

            steps = epoch.get("steps", [])
            for step in steps:
                agent = step.get("agent")
                if agent == "Programmer":
                    programmer_outputs.extend(step.get("outputs", []))
                elif agent == "Test Designer":
                    test_designer_outputs.extend(step.get("outputs", []))
                elif agent == "Test Executor":
                    executor_best_code = step.get("best_code")
                    executor_best_tests = step.get("best_tests")

            code_origin_score = 0
            test_origin_score = 0

            if executor_best_code and programmer_outputs:
                if executor_best_code in programmer_outputs:
                    code_origin_score = 1


            if executor_best_tests and test_designer_outputs:
                if executor_best_tests in test_designer_outputs:
                    test_origin_score = 1

            # 3. 将当前epoch的结果存入列表
            scores_list.append({
                'code_score': code_origin_score,
                'test_score': test_origin_score
            })

        return scores_list

    def analysis_test_to_code(self,best_tests_doc: str, new_code_doc: str):

        if not best_tests_doc or not new_code_doc:
            return {"accuracy": 0, "redundancy": 0}

        score_types = [
            "Accuracy",
            "Redundancy"
        ]
        return multi2.analysis_test_code(best_tests_doc,new_code_doc)


    def analyze_single(self, log_path) -> dict:
        code_list = self.get_code(log_path)
        test_list = self.get_test(log_path)
        exe_score_list = self.get_exe_score(log_path)
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
                final_scores[f'avg_code_{key.lower()}_score'] = None

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
                final_scores[f'avg_test_{key.lower()}_score'] = None

        # Exe
        valid_exe_scores = [score for score in exe_score_list if score is not None]

        if valid_exe_scores:
            avg_exe_score = sum(valid_exe_scores) / len(valid_exe_scores)
            final_scores['avg_exe_score'] = avg_exe_score
        else:
            final_scores['avg_exe_score'] = None

        print(f"======== 结束分析日志文件: {log_path} ========\n")
        return final_scores

    def analyze_multi(self, log_path):

        code_list = self.get_code(log_path)
        test_list = self.get_test(log_path)
        exe_score_list = self.analysis_Test_Code_Exe(log_path)
        best_tests_list = self.get_best_tests(log_path)
        final_scores = {}

        # code_test
        code_test_keys = ["Functionality", "Accuracy", "Redundancy"]

        final_key_map = {
            key: f'avg_code_test_{key.lower().replace(" ", "_")}_score'
            for key in code_test_keys
        }

        for final_key in final_key_map.values():
            final_scores[final_key] = None

        total_code_test_scores = {key: 0 for key in code_test_keys}

        num_code_test_pairs = min(len(code_list), len(test_list))
        if num_code_test_pairs > 0:
            print(f"\n--- 正在分析 {num_code_test_pairs} 个 Code-Test 对 ---")

            # 累加分数
            for i, (code_doc, test_doc) in enumerate(zip(code_list, test_list)):
                score_dict = multi2.analysis_code_test(code_doc, test_doc)
                # print(f"    ↳  分数: {score_dict}")
                for key in code_test_keys:
                    dict_key = key.lower().replace(" ", "_")
                    total_code_test_scores[key] += score_dict.get(dict_key, 0)
            for key in code_test_keys:
                avg_score = total_code_test_scores[key] / num_code_test_pairs
                final_key = final_key_map[key]
                final_scores[final_key] = avg_score


        # Test2Code
        test_to_code_keys = ["Accuracy", "Redundancy"]
        total_test_to_code_scores = {key: 0 for key in test_to_code_keys}

        for key in test_to_code_keys:
            final_scores[f'avg_test_to_code_{key.lower()}_score'] = None

        num_feedback_loops = min(len(best_tests_list), len(code_list)) - 1
        valid_loops_count = 0

        if num_feedback_loops > 0:
            for i in range(num_feedback_loops):
                previous_best_tests = best_tests_list[i]
                current_code = code_list[i + 1]

                if not previous_best_tests or not current_code:
                    continue
                score_dict = self.analysis_test_to_code(previous_best_tests, current_code)

                for key in test_to_code_keys:
                    total_test_to_code_scores[key] += score_dict.get(key.lower(), 0)
                valid_loops_count += 1
            if valid_loops_count > 0:
                for key in test_to_code_keys:
                    avg_score = total_test_to_code_scores[key] / valid_loops_count
                    final_scores[f'avg_test_to_code_{key.lower()}_score'] = avg_score

        return final_scores

    def analyze_performance(self, log_path):
        log_data = self._load_log(log_path)

        performance_summary = {
            'Programmer': {'time': 0, 'tokens': 0},
            'Test Designer': {'time': 0, 'tokens': 0},
            'Test Executor': {'time': 0, 'tokens': 0}
        }

        epochs = log_data.get("epochs", [])
        for epoch in epochs:
            steps = epoch.get("steps", [])
            for step in steps:
                agent = step.get("agent")
                performance = step.get("performance", {})

                if agent in performance_summary:
                    time_cost = performance.get("time_cost_seconds", 0)
                    performance_summary[agent]['time'] += time_cost

                    token_usage = performance.get("token_usage", {})
                    total_tokens = token_usage.get("total", 0)
                    performance_summary[agent]['tokens'] += total_tokens

        return performance_summary

    def bash_single(self,dir_path):

        df =  bashAnalysis.process_and_report_generic(dir_path, self.analyze_single)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df
    def bash_multi(self,dir_path):
        df = bashAnalysis.process_and_report_generic(dir_path, self.analyze_multi)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

    def bash_performance(self,dir_path):

        def performance_wrapper(log_path):
            perf_dict = self.analyze_performance(log_path)
            flat_dict = {}
            if perf_dict:
                for agent, data in perf_dict.items():
                    flat_dict[f'{agent}_time'] = data.get('time', 0)
                    flat_dict[f'{agent}_tokens'] = data.get('tokens', 0)
            return flat_dict

        df = bashAnalysis.process_and_report_generic(dir_path, performance_wrapper)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)

        return df

if __name__=='__main__':
    log_path = "../logTest/log.txt"
    dir_path = "../Results/agentcoder/part3"
    analysis = AgentCoderAnalysis()
    score = analysis.bash_performance(dir_path)
    # print(df_single)
    score.to_csv('output.txt', sep='\t', index=True)
    # print(df_single.to_string())