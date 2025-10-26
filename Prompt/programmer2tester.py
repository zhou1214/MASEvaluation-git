prompt = '''
# Task
You will be provided with a programmer’s implementation (code) and the corresponding tester/reviewer’s outputs.  
Your task is to evaluate how consistently the tester/reviewer’s outputs reflect the programmer’s implementation or the user’s original task.  
Focus on two key dimensions: Completeness and Accuracy, and generate a detailed analysis report.

# Evaluation Metrics

1. Completeness  
Description: Measures whether the tester/reviewer’s outputs comprehensively cover all the functionalities or behaviors implemented by the programmer.  
Scoring:  
- 90–100: Fully covers all functionalities implemented in the code; no missing aspects.  
- 70–89: Mostly covers the implemented functionality; minor gaps exist.  
- 40–69: Covers only part of the implementation; several functions untested or unreviewed.  
- 10–39: Very limited coverage; many functionalities not reflected.  
- 0–9: Almost no alignment; outputs fail to address the implementation.

2. Accuracy  
Description: Measures whether the tester/reviewer’s outputs are relevant and correctly aligned with the programmer’s implementation or the user’s task.  
Scoring:  
- 90–100: All outputs are accurate and directly related to the implementation; no irrelevant or incorrect points.  
- 70–89: Mostly accurate; minor irrelevant or imprecise comments.  
- 40–69: Contains several inaccurate or unrelated outputs; moderate noise present.  
- 10–39: Largely inaccurate or irrelevant; tester misunderstands much of the implementation.  
- 0–9: Completely off-topic or incorrect; outputs bear no relation to the code.

# Output Format
Return the evaluation result strictly in **valid JSON** format with the following structure:

{
  "Completeness": {
    "score": <int 0–100>,
    "analysis": "<detailed explanation>"
  },
  "Accuracy": {
    "score": <int 0–100>,
    "analysis": "<detailed explanation>"
  }
}

Ensure the response is strictly valid JSON (no extra text outside the JSON) and include clear reasoning for each dimension.

# Given task:
{task}

# Given Code:
{code}

# Given Tester/Reviewer Outputs:
{test}

'''