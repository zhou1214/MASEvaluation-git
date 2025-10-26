prompt ='''
# Task
You will be provided with the previous feedback from a tester/reviewer and the revised version of the programmer’s code.  
Your task is to evaluate how effectively the programmer addressed the feedback during the revision process.  
Focus on two key dimensions: Completeness and Accuracy, and generate a detailed analysis report.

# Evaluation Metrics

1. Completeness  
Description: Measures whether all test cases,suggestions, or comments mentioned in the tester/reviewer’s feedback are fully addressed in the revised code.  
Scoring:  
- 90–100: Fully addresses all feedback points; every issue and suggestion has been correctly resolved.  
- 70–89: Addresses most feedback points; only minor aspects remain unaddressed.  
- 40–69: Partially addresses feedback; several key issues unresolved or only partially fixed.  
- 10–39: Minimal response to feedback; many issues still present.  
- 0–9: Feedback almost entirely ignored; no meaningful revision.

2. Accuracy  
Description: Measures whether the code revision introduces unintended or incorrect changes beyond the feedback scope.  
Scoring:  
- 90–100: No unintended changes; modifications are precise and fully aligned with the feedback.  
- 70–89: Minor unintended changes that do not affect core functionality.  
- 40–69: Some inaccurate or unnecessary modifications that alter original behavior.  
- 10–39: Many incorrect or irrelevant changes; feedback was misapplied.  
- 0–9: Major deviations or new errors introduced; revision regresses overall quality.

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

# Given Feedback (from Tester/Reviewer):
{feedback}

# Given Revised Code (from Programmer):
{revised_code}


'''