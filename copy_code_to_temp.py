import os
from pathlib import Path
# datetime is not used for filename generation

# --- 配置项 ---
IGNORED_DIRS = {
    "node_modules", "__pycache__", ".git", ".vscode", ".idea",
    "dist", "build", "venv", ".venv", "target", "out", "coverage", "temp",
}
IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".log", ".swp", ".DS_Store", ".tmp", ".bak",
}
IGNORED_FILES = {}

# 最多在文件名中包含的词干数量，超过此数量则采用简化命名法
MAX_STEMS_FOR_DETAILED_FILENAME = 5

def list_files_for_selection(base_folder: Path) -> list[Path]:
    eligible_files = []
    for item in base_folder.rglob("*"):
        if item.is_file():
            in_ignored_dir = False
            try: # 检查路径的每一部分是否在忽略目录中
                relative_path_parts = item.relative_to(base_folder).parent.parts
                for part in relative_path_parts:
                    if part in IGNORED_DIRS:
                        in_ignored_dir = True
                        break
            except ValueError: # 如果 base_folder 就是 item.parent，relative_to 会是 "."
                pass 
            
            if in_ignored_dir:
                continue
            # 再次检查直接父目录，以防 base_folder 本身就是个被忽略的名字 (虽然不常见)
            if item.parent.name in IGNORED_DIRS and item.parent != base_folder:
                 continue

            if (item.name not in IGNORED_FILES and
                    item.suffix.lower() not in IGNORED_EXTENSIONS):
                eligible_files.append(item)
    eligible_files.sort()
    return eligible_files

def parse_selection_input(selection_str: str, max_index: int) -> set[int] | None:
    selected_indices = set()
    parts = selection_str.split(',')
    for part in parts:
        part = part.strip()
        if not part: continue
        if '-' in part:
            try:
                start_str, end_str = part.split('-', 1)
                start, end = int(start_str), int(end_str)
                if not (1 <= start <= end <= max_index):
                    print(f"错误：范围 '{part}' 无效。数字必须在 1 到 {max_index} 之间。")
                    return None
                selected_indices.update(range(start - 1, end))
            except ValueError:
                print(f"错误：范围格式 '{part}' 无效。")
                return None
        else:
            try:
                num = int(part)
                if not (1 <= num <= max_index):
                    print(f"错误：数字 '{num}' 超出范围 (1-{max_index})。")
                    return None
                selected_indices.add(num - 1)
            except ValueError:
                print(f"错误：输入 '{part}' 不是有效的数字或范围。")
                return None
    return selected_indices

def sanitize_stem(stem: str) -> str:
    """清理词干，替换非字母数字为下划线，合并连续下划线。"""
    sanitized = "".join(c if c.isalnum() else '_' for c in stem)
    sanitized = '_'.join(filter(None, sanitized.split('_')))
    return sanitized

def copy_selected_files_to_temp():
    project_root = Path(".")
    temp_dir = project_root / "temp"
    try:
        temp_dir.mkdir(parents=True, exist_ok=True)
        print(f"临时文件夹 '{temp_dir.resolve()}' 已准备好。")
    except OSError as e:
        print(f"错误：无法创建临时文件夹 '{temp_dir}': {e}")
        return

    while True:
        target_folder_name = input(
            "\n请输入要从中复制文件的主要文件夹名称 (例如 'frontend', 'backend', 或输入 'exit' 退出):\n"
        ).strip()

        if target_folder_name.lower() == 'exit':
            print("脚本已退出。")
            return
        if not target_folder_name:
            print("文件夹名称不能为空，请重新输入。")
            continue

        target_folder_path = project_root / target_folder_name
        if not target_folder_path.is_dir():
            print(f"错误：文件夹 '{target_folder_name}' 在项目根目录下未找到或不是一个目录。")
            print("可用的一级子目录有:")
            for item in project_root.iterdir():
                if item.is_dir() and item.name not in IGNORED_DIRS and not item.name.startswith('.'):
                    print(f"  - {item.name}")
            continue

        available_files = list_files_for_selection(target_folder_path)
        if not available_files:
            print(f"在 '{target_folder_name}' 中未找到符合条件的可选文件。")
            continue

        while True:
            print(f"\n在 '{target_folder_name}' 中可供选择的文件:")
            print("-" * 50)
            for i, file_p in enumerate(available_files):
                print(f"  {i+1}: {file_p.relative_to(target_folder_path)}")
            print("-" * 50)
            print(f"输入文件编号 (例如: 1, 3-5, 8), 'a' (全部选择), 'b' (返回上一级), 或 'q' (退出)。")
            
            selection_input = input("请选择要复制的文件: ").strip().lower()

            if selection_input == 'q': print("脚本已退出。"); return
            if selection_input == 'b': break 
            
            selected_file_paths = []
            if selection_input == 'a':
                selected_file_paths = available_files
            else:
                selected_indices = parse_selection_input(selection_input, len(available_files))
                if selected_indices is None: continue
                for index in sorted(list(selected_indices)):
                    selected_file_paths.append(available_files[index])
            
            if not selected_file_paths:
                print("未选择任何文件。请重新选择。")
                continue

            output_content_parts = []
            copied_count = 0
            print("\n正在准备复制以下文件:")
            for file_p in selected_file_paths:
                try:
                    relative_path_to_root = file_p.relative_to(project_root)
                    print(f"  - {relative_path_to_root}")
                    file_content = file_p.read_text(encoding='utf-8', errors='replace')
                    output_content_parts.append(f"--- BEGIN FILE: {relative_path_to_root} ---\n")
                    output_content_parts.append(file_content)
                    output_content_parts.append(f"\n--- END FILE: {relative_path_to_root} ---\n\n")
                    copied_count += 1
                except Exception as e:
                    print(f"  ! 错误：无法读取文件 '{file_p}': {e}")
            
            if copied_count == 0:
                print("\n没有文件被成功读取和准备复制。")
                continue

            # --- 更新后的文件名生成逻辑 ---
            stems_part = ""
            total_selected_count = len(selected_file_paths)

            if total_selected_count <= MAX_STEMS_FOR_DETAILED_FILENAME:
                # 文件较少时，拼接词干
                file_stems_for_name = []
                unique_stems_added = set()
                for p in selected_file_paths:
                    stem = sanitize_stem(p.stem.lower())
                    if stem and stem not in unique_stems_added:
                        file_stems_for_name.append(stem)
                        unique_stems_added.add(stem)
                        if len(file_stems_for_name) >= MAX_STEMS_FOR_DETAILED_FILENAME: # 确保不超过此处的限制
                            break 
                if file_stems_for_name:
                    stems_part = "_".join(file_stems_for_name)
                else:
                    stems_part = "selected_files" # Fallback
            else:
                # 文件较多时，采用 文件夹_第一个文件名_etc_总数.txt 格式
                first_file_stem_sanitized = "unknown_file" # Fallback
                if selected_file_paths: # 确保列表不为空
                    first_file_stem_sanitized = sanitize_stem(selected_file_paths[0].stem.lower())
                    if not first_file_stem_sanitized : # 如果清理后为空
                        first_file_stem_sanitized = "file" # 进一步回退

                stems_part = f"{first_file_stem_sanitized}_etc_{total_selected_count}"
            
            sanitized_target_folder_name = target_folder_name.replace(os.sep, '_')
            base_filename_stem = f"{sanitized_target_folder_name}_{stems_part}"
            # --- 文件名生成逻辑结束 ---
            
            output_filename = f"{base_filename_stem}.txt"
            output_filepath = temp_dir / output_filename
            
            counter = 1
            while output_filepath.exists(): # 处理文件名冲突
                output_filename = f"{base_filename_stem}_{counter}.txt"
                output_filepath = temp_dir / output_filename
                counter += 1

            try:
                with output_filepath.open('w', encoding='utf-8') as f_out:
                    f_out.write("".join(output_content_parts))
                print(f"\n成功！已将 {copied_count} 个文件的内容复制到:")
                print(f"{output_filepath.resolve()}")
            except Exception as e:
                print(f"\n错误：无法写入输出文件 '{output_filepath}': {e}")
            
            print("\n操作完成。")
            break # 返回主文件夹选择

if __name__ == "__main__":
    copy_selected_files_to_temp()