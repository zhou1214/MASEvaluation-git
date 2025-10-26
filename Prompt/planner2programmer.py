prompt='''
# Task
You will be provided with a plan and the corresponding source code.  
Your task is to evaluate how well the programmer implements the plan, focusing on two key dimensions: Completeness and Accuracy.  
Generate a detailed analysis report for each dimension.

# Evaluation Metrics

1. Completeness  
Description: Measures whether all steps outlined in the plan are correctly implemented in the code.  
Scoring:  
90~100: All steps from the plan are fully implemented; nothing is missing.  
70~89: Most steps are implemented; minor steps or details missing.  
40~69: Some critical steps are missing or partially implemented.  
10~39: Many plan steps are missing; major parts of the plan not implemented.  
0~9: Almost no steps from the plan are implemented; completely incomplete.

2. Accuracy 
Description: Measures whether the code implements extra functionality that was not prescribed in the plan.  
Scoring:  
90~100: No extra or unprescribed functionality; code strictly follows the plan.  
70~89: Minor extra functionality that does not affect correctness.  
40~69: Some unnecessary steps present; moderately deviates from the plan.  
10~39: Significant extra functionality not in the plan; may confuse the implementation.  
0~9: Excessive unrelated functionality; largely deviates from the plan.

# Output Format
Return the evaluation result strictly in **valid JSON** format with the following structure:

{
  "Completeness": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  },
  "Accuracy": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  }
}

Ensure the response is strictly valid JSON (no extra text outside the JSON) and include clear reasoning for each dimension.

# Given Plan:
{plan}
# Given Code:
{code}
'''