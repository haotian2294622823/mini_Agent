import pytest
from mini_agent.tools.filesystem import read_file, list_files

# --- 测试 read_file ---

def test_read_normal_and_chinese_file(tmp_path):
    """测试：正常文件和中文文件"""
    # 1. 在临时工作区准备数据（用代码自动创建文件）
    # tmp_path 就是我们的安全沙盒，我们在里面新建一个叫 "中文测试.txt" 的文件
    test_file = tmp_path / "中文测试.txt"
    test_file.write_text("Hello, 世界！", encoding="utf-8")
    
    # 2. 调用我们要测试的函数
    result = read_file(tmp_path, "中文测试.txt")
    
    # 3. 断言 (assert)：检查结果是否符合预期
    assert result == "Hello, 世界！"

def test_read_non_existent_file(tmp_path):
    """测试：不存在的文件"""
    # 我们不创建任何文件，直接读
    result = read_file(tmp_path, "ghost.txt")
    
    # 检查返回的报错信息里，是否包含了我们写的提示语
    assert "找不到路径" in result

def test_read_directory_as_file(tmp_path):
    """测试：把目录当做文件来读"""
    # 在沙盒里创建一个真实的文件夹
    sub_dir = tmp_path / "my_folder"
    sub_dir.mkdir()
    
    # 试图用 read_file 去读这个文件夹
    result = read_file(tmp_path, "my_folder")
    
    # 检查是否成功拦截
    assert "是一个目录" in result
    assert "不能当做文本读取" in result

def test_read_out_of_bounds(tmp_path):
    """测试：恶意越界访问"""
    # 试图用 ../ 跳出 tmp_path 所在的沙盒
    result = read_file(tmp_path, "../outside_secret.txt")
    
    # 检查安检门是否生效
    assert "越界访问" in result

# --- 顺便测试一下 list_files ---

def test_list_files_normal(tmp_path):
    """测试：正常列出目录"""
    # 在临时沙盒里制造一点内容：2个文件，1个文件夹
    (tmp_path / "a_file.txt").write_text("123")
    (tmp_path / "b_file.txt").write_text("456")
    (tmp_path / "c_folder").mkdir()
    
    # 调用列出函数
    # list_files 需要工作区和目录路径；"." 表示工作区根目录。
    result = list_files(tmp_path, ".")
    
    # 验证输出格式
    assert "[文件夹]" in result
    assert "c_folder/" in result
    assert "[文件]" in result
    assert "a_file.txt" in result
    assert "b_file.txt" in result
