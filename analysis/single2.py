from certifi import contents

from util import llm
from Prompt import PRD, Arch, Test, Role, Example, Plan
from analysis import evaluator
import os  # 导入 os 模块来读取环境变量
from Prompt2 import Code,Consistency

NUM_RUNS = 2


def _run_evaluation_repeatedly(prompt: str, content: str, score_types: list, num_runs: int = NUM_RUNS):
    if not content:
        return {key.lower(): 0 for key in score_types}

    total_scores = {key: 0 for key in score_types}
    successful_runs = 0

    print(f"  -> [Analysis] Running evaluation up to {num_runs} times...")

    for i in range(num_runs):
        try:
            result_text = llm.get_llm_evaluation(prompt, content)
            run_scores = evaluator.get_dimensional_scores(result_text, score_types)
            if not run_scores:
                continue
            for key in score_types:
                total_scores[key] += run_scores.get(key.lower(), 0)
            successful_runs += 1
        except Exception as e:
            continue

    # 计算平均分
    if successful_runs > 0:
        avg_scores = {key.lower(): val / successful_runs for key, val in total_scores.items()}
        print(f"  -> Analysis complete. Averaged over {successful_runs}/{num_runs} successful runs.")
        print(f"     ↳ Scores: {avg_scores}")
    else:
        avg_scores = {key.lower(): 0 for key in score_types}

    return avg_scores


def _run_evaluation_repeatedly2(prompt: str, task: str, code: str, score_types: list, num_runs: int = NUM_RUNS):


    if not code:
        return {key.lower(): 0 for key in score_types}

    content = f"# given task:\n{task}\n\n# code:\n{code}"
    total_scores = {key: 0 for key in score_types}
    successful_runs = 0

    print(f"  -> [Analysis] Running evaluation up to {num_runs} times...")

    for i in range(num_runs):
        try:
            result_text = llm.get_llm_evaluation(prompt, content)
            run_scores = evaluator.get_dimensional_scores(result_text, score_types)
            if not run_scores:
                continue
            for key in score_types:
                total_scores[key] += run_scores.get(key.lower(), 0)
            successful_runs += 1
        except Exception as e:
            continue

    if successful_runs > 0:
        avg_scores = {key.lower(): val / successful_runs for key, val in total_scores.items()}
        print(f"  -> Analysis complete. Averaged over {successful_runs}/{num_runs} successful runs.")
        print(f"     ↳ Scores: {avg_scores}")
    else:
        avg_scores = {key.lower(): 0 for key in score_types}

    return avg_scores

def analysis_code(code_doc, num_runs=NUM_RUNS):
    score_types = ["Consistency", "Integrity", "Correctness", "Readability", "Efficiency"]

    avg_scores_dict = _run_evaluation_repeatedly(Code.prompt, code_doc, score_types, num_runs)

    scores_list = []
    for key in score_types:
        score = avg_scores_dict.get(key.lower(), 0)
        scores_list.append(score)

    return scores_list

def analysis_consistency(instruction,code_doc, num_runs=NUM_RUNS):
    score_types = ["Consistency"]

    avg_scores_dict = _run_evaluation_repeatedly2(Consistency.prompt, instruction, code_doc, score_types, num_runs)

    scores_list = []
    for key in score_types:
        score = avg_scores_dict.get(key.lower(), 0)
        scores_list.append(score)

    return scores_list


