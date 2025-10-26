prompt='''
# Task  
Your task is to evaluate the following code across three dimensions: Consistency, Readability, and Efficiency.  
Each dimension should be scored on a 100-point scale, where higher scores indicate better quality.

# Evaluation Metrics

1. Consistency  
Description: Evaluates whether the generated code satisfies all explicit and implicit requirements of the given task.  
Scoring:  
90~100: Fully satisfies all requirements; perfectly aligned with both explicit and implicit objectives.  
70~89: Meets most requirements, with minor omissions or misinterpretations.  
40~69: Partially meets requirements; several aspects are missing or inconsistent.  
10~39: Major inconsistencies with task objectives; key parts of the task unmet.  
0~9: Completely irrelevant or off-task.


2. Readability  
Description: Measures the clarity and comprehensibility of the code, considering naming conventions, logical structure, comments, and formatting.  
Scoring:  
90~100: Exceptionally clear and well-structured; naming is consistent and meaningful, code fully follows style conventions.  
70~89: Mostly clear; minor inconsistencies or missing comments.  
40~69: Understandable but contains ambiguous naming or loose structure.  
10~39: Hard to read due to poor structure or lack of clarity.  
0~9: Extremely confusing and disorganized.

3. Efficiency  
Description: Measures the performance of the code in terms of time and space complexity.  
Scoring:  
90~100: Highly efficient; employs optimal algorithms and data structures.  
70~89: Generally efficient; some non-critical optimizations possible.  
40~69: Acceptable but includes redundant or suboptimal logic.  
10~39: Noticeably inefficient; unnecessary computation or high resource usage.  
0~9: Severe inefficiency such as excessive loops, recursion, or blocking operations.

# Output Format  
Return the evaluation result strictly in **valid JSON** format with the following structure:

{
  "Consistency": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  },
  "Readability": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  },
  "Efficiency": {
    "score": <int 0~100>,
    "analysis": "<detailed explanation>"
  }
}

Ensure the response is strictly valid JSON and includes clear reasoning for each dimension.

# Given Task:
{task}

# Code to Evaluate:
{code}
'''