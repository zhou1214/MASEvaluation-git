import json
from pathlib import Path
import pandas as pd


def collect_metrics_from_dir(dir_path: str, output_excel: str = "metrics_summary.xlsx") -> pd.DataFrame:

    dir_path = Path(dir_path)

    if not dir_path.exists():
        raise FileNotFoundError(f"None: {dir_path}")

    if not dir_path.is_dir():
        raise NotADirectoryError(f"None path: {dir_path}")

    rows = []

    json_files = sorted(dir_path.glob("*.json"))
    if not json_files:
        print(f"None {dir_path} JSON")
        return pd.DataFrame()

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[skip] failed: {json_file.name} | error: {e}")
            continue

        metrics_summary = data.get("metrics_summary", {})
        task_id = data.get("task_id", "")
        graph_name = data.get("graph_name", "")
        model_name = data.get("model_name", "")
        saved_at = data.get("saved_at", "")

        if not isinstance(metrics_summary, dict) or not metrics_summary:
            continue

        for agent_name, metrics in metrics_summary.items():
            if not isinstance(metrics, dict):
                continue

            row = {
                "file_name": json_file.name,
                "task_id": task_id,
                "graph_name": graph_name,
                "model_name": model_name,
                "saved_at": saved_at,
                "agent": agent_name,
                "calls": metrics.get("calls", 0),
                "total_tokens": metrics.get("total_tokens", 0),
                "wall_time_s": metrics.get("wall_time_s", 0),
            }
            rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        print("no data")
        return df


    summary_df = (
        df.groupby("agent", as_index=False)[["calls", "total_tokens", "wall_time_s"]]
        .sum()
        .sort_values(by="total_tokens", ascending=False)
    )


    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="details")
        summary_df.to_excel(writer, index=False, sheet_name="summary")

    return df


if __name__ == "__main__":
    # results path
    input_dir = ""
    # output path
    output_file = ""

    collect_metrics_from_dir(input_dir, output_file)