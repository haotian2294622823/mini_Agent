"""grep 函数的单元测试。"""

from mini_agent.tools.filesystem import grep

def test_grep_finds_keyword_in_single_file(tmp_path):
    """单文件：能找到关键字，并返回行号与内容。"""
    (tmp_path / "demo.txt").write_text("第一行\n第二行 hello\n第三行\n", encoding="utf-8")

    result = grep(tmp_path, "hello", "demo.txt")

    assert "demo.txt:2:第二行 hello" in result

def test_grep_searches_whole_directory(tmp_path):
    """目录：递归搜索多个文件，命中多个文件。"""
    (tmp_path / "a.txt").write_text("alpha\nTODO fix this\n", encoding="utf-8")
    (tmp_path / "b.txt").write_text("nothing here\n", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_text("TODO another\n", encoding="utf-8")

    result = grep(tmp_path, "TODO", ".")

    assert "a.txt:2:TODO fix this" in result
    assert "sub\\c.txt:1:TODO another" in result or "sub/c.txt:1:TODO another" in result
    assert "b.txt" not in result

def test_grep_no_match(tmp_path):
    """无命中：应返回统一的未找到提示。"""
    (tmp_path / "demo.txt").write_text("hello\n", encoding="utf-8")

    result = grep(tmp_path, "不存在的词", "demo.txt")

    assert "未找到" in result

def test_grep_empty_pattern(tmp_path):
    """空关键字：应被前置校验拦截。"""
    result = grep(tmp_path, "", "demo.txt")

    assert "关键字不能为空" in result

def test_grep_missing_path(tmp_path):
    """路径不存在：应返回找不到路径。"""
    result = grep(tmp_path, "hello", "ghost.txt")

    assert "找不到路径" in result

def test_grep_out_of_bounds(tmp_path):
    """越界访问：应被路径安检拦截。"""
    result = grep(tmp_path, "hello", "../outside.txt")

    assert "越界访问" in result

def test_grep_skips_binary_file(tmp_path):
    """目录搜索时遇到二进制文件应跳过，不影响其他文件命中。"""
    (tmp_path / "ok.txt").write_text("needle\n", encoding="utf-8")
    (tmp_path / "bin.dat").write_bytes(b"\xff\xfe\x00\x01\x80")

    result = grep(tmp_path, "needle", ".")

    assert "ok.txt:1:needle" in result