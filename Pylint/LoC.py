import os


def count_code_lines(dir_path):
    results = []

    for item in sorted(os.listdir(dir_path)):
        item_path = os.path.join(dir_path, item)
        if os.path.isdir(item_path) and item.startswith('instruction'):
            code_file = os.path.join(item_path, 'code.txt')
            if os.path.exists(code_file):
                with open(code_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    line_count = len(lines)
                results.append((item, line_count))

    for name, count in results:
        print(f"{name} {count}")


if __name__ == "__main__":
    # logs path
    dir_path = ""
    count_code_lines(dir_path)