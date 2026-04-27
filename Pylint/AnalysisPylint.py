import subprocess
import json
import shutil
import pathlib
import re

# logs path
SOURCE_DIR = pathlib.Path(r"")
# report path
REPORT_DIR = pathlib.Path(r"")
# temp path
PYLINTRC   = pathlib.Path(r"")

REPORT_DIR.mkdir(exist_ok=True)
summary = []


def parse_radon_cc(output: str) -> dict:
    avg_match = re.search(r"Average complexity:\s*([A-F])\s*\(([\d.]+)\)", output)
    all_scores = re.findall(r"\((\d+)\)", output)

    if not avg_match:
        return {"cc_avg": None, "cc_worst": None, "cc_grade": None}

    scores = [int(s) for s in all_scores]
    return {
        "cc_avg": float(avg_match.group(2)),
        "cc_worst": max(scores) if scores else None,
        "cc_grade": avg_match.group(1)
    }


def parse_radon_mi(output: str) -> dict:
    match = re.search(r"-\s*([A-C])\s*\(([\d.]+)\)", output)
    if match:
        return {
            "mi_score": float(match.group(2)),
            "mi_grade": match.group(1)
        }
    return {"mi_score": None, "mi_grade": None}

for instruction_dir in sorted(
    SOURCE_DIR.iterdir(),
    key=lambda p: int(re.search(r'\d+', p.name).group()) if re.search(r'\d+', p.name) else 0
):
    if not instruction_dir.is_dir():
        continue

    code_txt = instruction_dir / "code.txt"
    if not code_txt.exists():
        print(f"[跳过] {instruction_dir.name}：No code.txt")
        continue

    tmp_py = instruction_dir / "code_tmp.py"
    shutil.copy(code_txt, tmp_py)

    try:
        result_json = subprocess.run(
            ["pylint", str(tmp_py), "--output-format=json", f"--rcfile={PYLINTRC}"],
            capture_output=True, text=True, encoding='utf-8'
        )
        issues = json.loads(result_json.stdout) if result_json.stdout.strip() else []


        result_text = subprocess.run(
            ["pylint", str(tmp_py), "--output-format=text", f"--rcfile={PYLINTRC}"],
            capture_output=True, text=True, encoding='utf-8'
        )
        match = re.search(r"rated at ([\d.]+/10)", result_text.stdout)
        pylint_score = match.group(1) if match else "N/A"


        result_cc = subprocess.run(
            ["radon", "cc", str(tmp_py), "-s", "-a"],
            capture_output=True, text=True, encoding='utf-8'
        )
        cc_data = parse_radon_cc(result_cc.stdout)


        result_mi = subprocess.run(
            ["radon", "mi", str(tmp_py), "-s"], 
            capture_output=True, text=True, encoding='utf-8'
        )
        mi_data = parse_radon_mi(result_mi.stdout)


        report = {
            "project": instruction_dir.name,
            "pylint_score": pylint_score,
            "cyclomatic_complexity": cc_data,  
            "maintainability_index": mi_data,   
            "issue_count": len(issues),
            "issues": issues,
        }
        report_path = REPORT_DIR / f"{instruction_dir.name}.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),encoding='utf-8')

        print(
            f"[完成] {instruction_dir.name} | "
            f"pylint: {pylint_score} | "
            f"CC: {cc_data['cc_avg']}({cc_data['cc_grade']}) | "
            f"MI: {mi_data['mi_score']}({mi_data['mi_grade']})"
        )
        summary.append({
            "project": instruction_dir.name,
            "pylint_score": pylint_score,
            **cc_data,
            **mi_data,
            "issue_count": len(issues)
        })

    finally:
        tmp_py.unlink(missing_ok=True)

summary_path = REPORT_DIR / "_summary.json"
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
