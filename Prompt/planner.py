prompt=''''
# Task
Your task is to evaluate the following plan across three dimensions: Completeness, Correctness, Clarity.  
Each dimension should be scored on a 100-point scale, where higher scores indicate better quality.

# Evaluation Metrics

1. Completeness  
Description: Evaluates whether the plan covers all critical steps required to solve the problem.  
Scoring:  
90~100: Fully comprehensive; includes all major and minor steps needed for a complete solution.  
70~89: Mostly complete; only minor steps or details missing.  
40~69: Partially complete; several critical steps omitted.  
10~39: Incomplete; lacks most essential steps.  
0~9: Severely incomplete or entirely irrelevant.

2. Correctness  
Description: Measures whether the steps in the plan are logically valid and lead toward a working and correct solution.  
Scoring:  
90~100: All steps are logically sound and would clearly result in a correct implementation.  
70~89: Mostly correct; contains minor logical flaws that are fixable.  
40~69: Some correct reasoning, but several incorrect or misleading steps.  
10~39: Major logical errors; plan unlikely to work as intended.  
0~9: Entirely incorrect reasoning or irrelevant to the problem.

3. Clarity  
Description: Evaluates the precision, organization, and readability of the plan.  
Scoring:  
90~100: Exceptionally clear and well-organized; each step is easy to follow and unambiguous.  
70~89: Generally clear; minor issues with expression or structure.  
40~69: Understandable but somewhat vague or disorganized.  
10~39: Hard to follow; unclear reasoning or step descriptions.  
0~9: Extremely confusing or incoherent.


# Output Format
Return the evaluation result strictly in **valid JSON** format with the following structure:

{
  "Completeness": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  },
  "Correctness": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  },
  "Clarity": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  }
}

Ensure the response is strictly valid JSON (no extra text outside the JSON) and includes clear reasoning for each dimension.

# Given Plan:
{plan}
'''