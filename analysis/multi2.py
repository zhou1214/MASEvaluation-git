import os
from util import llm
from analysis import evaluator
from Prompt import code2test,test2code

NUM_RUNS = 1



def _run_evaluation_repeatedly2(prompt: str, content: str, score_types: list, num_runs: int = NUM_RUNS):

    if not content:
        return {key.lower(): 0 for key in score_types}
    total_scores = {key: 0 for key in score_types}
    successful_runs = 0

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




def analysis_code_test(code_doc, test_doc, num_runs=NUM_RUNS):
    if not code_doc or not test_doc:
        return {"Completeness": -999, "Accuracy": -999}

    score_types = ["Completeness", "Accuracy"]
    input_text = f"Code document:\n{code_doc}\n Test document:\n{test_doc}"
    return _run_evaluation_repeatedly2(code2test.prompt, input_text, score_types, num_runs)


def analysis_test_code(test_doc, code_doc, num_runs=NUM_RUNS):
    if not test_doc or not code_doc:
        return {"Completeness": -999, "Accuracy": -999}
    score_types = ["Completeness", "Accuracy"]
    input_text = f"Test document:\n{test_doc}\n Code document:\n{code_doc}"
    return _run_evaluation_repeatedly2(test2code.prompt, input_text, score_types, num_runs)


