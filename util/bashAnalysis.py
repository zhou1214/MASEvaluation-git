# utils/batch_analyzer.py
import glob
import os

import pandas as pd
from pathlib import Path


def get_log_groups(dir_path: str) -> dict:
    base_path = Path(dir_path)
    if not base_path.is_dir():
        return {}

    log_groups = {}
    # dir_path/instructionX/runY/log.txt
    for log_path in base_path.rglob("log.txt"):
        try:
            instruction_dir = log_path.parent.parent.name
            if 'instruction' not in instruction_dir:
                instruction_dir = log_path.parent.name
                if 'instruction' not in instruction_dir:
                    continue

            if instruction_dir not in log_groups:
                log_groups[instruction_dir] = []
            log_groups[instruction_dir].append(log_path)
        except IndexError:
            print(IndexError)

    return log_groups


def process_and_average_generic(dir_path: str, analysis_func) -> pd.DataFrame | None:
    log_groups = get_log_groups(dir_path)
    if not log_groups:
        return None

    all_results = []
    sorted_instructions = sorted(log_groups.keys(), key=lambda x: int(x.replace('instruction', '')))

    for instruction in sorted_instructions:
        log_paths = log_groups[instruction]

        group_scores = {}
        valid_logs_count = 0

        for log_path in log_paths:
            try:
                result_dict = analysis_func(log_path)
                if result_dict:
                    valid_logs_count += 1
                    for key, value in result_dict.items():
                        if isinstance(value, (int, float)):
                            group_scores[key] = group_scores.get(key, 0) + value
            except Exception as e:
                print(e)

        if valid_logs_count > 0:
            avg_scores = {key: val / valid_logs_count for key, val in group_scores.items()}
            avg_scores['instruction'] = instruction
            all_results.append(avg_scores)


    if not all_results:
        return None

    df = pd.DataFrame(all_results).fillna(0)
    if 'instruction' in df.columns:
        df = df[['instruction'] + [col for col in df.columns if col != 'instruction']]
    return df


def get_log_files(dir_path: str) -> dict[str, str]:

    log_files_map = {}
    search_pattern = os.path.join(dir_path, 'instruction*', 'log.txt')
    found_files = glob.glob(search_pattern)

    for log_path in found_files:
        instruction_name = os.path.basename(os.path.dirname(log_path))
        if instruction_name.startswith('instruction'):
            log_files_map[instruction_name] = log_path

    return log_files_map


def process_and_report_generic(dir_path: str, analysis_func) -> pd.DataFrame | None:
    log_files_map = get_log_files(dir_path)
    if not log_files_map:
        return None

    all_results = []
    sorted_instructions = sorted(log_files_map.keys(), key=lambda x: int(x.replace('instruction', '')))

    for instruction in sorted_instructions:
        log_path = log_files_map[instruction]
        try:
            result_dict = analysis_func(log_path)

            if result_dict:
                result_dict['instruction'] = instruction
                all_results.append(result_dict)

        except Exception as e:
            print(e)

    if not all_results:
        return None

    df = pd.DataFrame(all_results).fillna(0)

    if 'instruction' in df.columns:
        cols = ['instruction'] + [col for col in df.columns if col != 'instruction']
        df = df[cols]

    return df
