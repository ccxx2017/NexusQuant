import os
from pathlib import Path

# --- 配置项 ---
# 要忽略的目录名称 (通常是依赖项、构建产物、版本控制等)
# Directory names to ignore (typically dependencies, build artifacts, VCS, etc.)
IGNORED_DIRS = {
    "node_modules",
    "__pycache__",
    ".git",
    ".vscode",
    ".idea",
    "dist",
    "build",
    "venv",
    ".venv",
    "target",  # Common for Rust/Java
    "out",     # Common for some build systems
    "coverage", # Coverage reports
}

# 要忽略的文件扩展名 (例如编译后的 Python 文件、日志文件)
# File extensions to ignore (e.g., compiled Python files, log files)
IGNORED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".log",
    ".swp", # Vim swap files
    ".DS_Store", # macOS specific
    ".tmp",
    ".bak",
}

# 要忽略的特定文件名
# Specific filenames to ignore
IGNORED_FILES = {
    # "specific_file_to_ignore.ext"
}

# --- 树形结构打印函数 ---
def print_directory_tree(root_dir_path: Path, prefix: str = "", ignored_dirs: set = None, ignored_extensions: set = None, ignored_files: set = None):
    """
    递归打印目录树结构。
    Recursively prints the directory tree structure.

    Args:
        root_dir_path (Path): 要打印的根目录的路径对象。
                              Path object of the root directory to print.
        prefix (str): 当前行打印的前缀，用于绘制树形结构。
                      Prefix for the current line print, used for drawing the tree structure.
        ignored_dirs (set): 要忽略的目录名称集合。
                            Set of directory names to ignore.
        ignored_extensions (set): 要忽略的文件扩展名集合。
                                  Set of file extensions to ignore.
        ignored_files (set): 要忽略的特定文件名集合。
                             Set of specific filenames to ignore.
    """
    if ignored_dirs is None:
        ignored_dirs = IGNORED_DIRS
    if ignored_extensions is None:
        ignored_extensions = IGNORED_EXTENSIONS
    if ignored_files is None:
        ignored_files = IGNORED_FILES

    # 获取目录下所有条目，并过滤掉不希望看到的
    # Get all entries in the directory and filter out unwanted ones
    try:
        entries = sorted(
            [
                entry
                for entry in root_dir_path.iterdir()
                if entry.name not in ignored_dirs and
                   entry.suffix.lower() not in ignored_extensions and
                   entry.name not in ignored_files
            ],
            key=lambda x: (x.is_file(), x.name.lower()) # 目录优先，然后按名称排序
                                                        # Directories first, then sort by name
        )
    except PermissionError:
        print(f"{prefix}└── [权限不足 Permission Denied: {root_dir_path.name}]")
        return
    except FileNotFoundError:
        print(f"{prefix}└── [目录不存在 Directory Not Found: {root_dir_path.name}]")
        return


    for i, entry in enumerate(entries):
        connector = "└── " if i == len(entries) - 1 else "├── "
        print(f"{prefix}{connector}{entry.name}")

        if entry.is_dir():
            extension = "    " if i == len(entries) - 1 else "│   "
            print_directory_tree(entry, prefix + extension, ignored_dirs, ignored_extensions, ignored_files)

# --- 主程序 ---
if __name__ == "__main__":
    project_root = Path(".") # 脚本假定在项目根目录运行
                             # Script assumes it's run from the project root

    while True:
        target_folder_name = input(
            "请输入要打印结构图的文件夹名称 (例如 'frontend', 'backend', 或输入 'exit' 退出):\n"
            "Enter the folder name to visualize (e.g., 'frontend', 'backend', or type 'exit' to quit): "
        ).strip()

        if target_folder_name.lower() == 'exit':
            print("脚本已退出。Exiting script.")
            break

        if not target_folder_name:
            print("输入不能为空，请重新输入。Input cannot be empty, please try again.")
            continue

        target_path = project_root / target_folder_name

        if not target_path.exists():
            print(f"错误: 文件夹 '{target_folder_name}' 在项目根目录下未找到。")
            print(f"Error: Folder '{target_folder_name}' not found in the project root.")
            print(f"当前检查路径: {target_path.resolve()}")
            print("可用的一级子目录有 (Available top-level subdirectories):")
            for item in project_root.iterdir():
                if item.is_dir() and item.name not in IGNORED_DIRS and not item.name.startswith('.'):
                    print(f"  - {item.name}")
            print("-" * 30)
            continue

        if not target_path.is_dir():
            print(f"错误: '{target_folder_name}' 不是一个文件夹。")
            print(f"Error: '{target_folder_name}' is not a directory.")
            print("-" * 30)
            continue

        print(f"\n{target_folder_name}/")
        print_directory_tree(target_path, ignored_dirs=IGNORED_DIRS, ignored_extensions=IGNORED_EXTENSIONS, ignored_files=IGNORED_FILES)
        print("\n" + "=" * 40 + "\n")