from app.services.format_service import FormatService


def test_build_markdown_uses_layout_and_heading_signals():
    formatter = FormatService()

    markdown = formatter.build_markdown(
        [
            {"text": "年度报告", "layout_type": "title"},
            ("执行摘要", "Heading 1"),
            ("1.1 业务进展", ""),
            ("• 新增客户 120 家", ""),
            ("普通正文第一行", ""),
            ("普通正文第二行", ""),
        ],
        [],
    )

    assert "# 年度报告" in markdown
    assert "## 执行摘要" in markdown
    assert "### 1.1 业务进展" in markdown
    assert "- 新增客户 120 家" in markdown
    assert "普通正文第一行" in markdown
    assert "普通正文第二行" in markdown


def test_build_markdown_keeps_existing_markdown():
    formatter = FormatService()

    markdown = formatter.build_markdown(
        [
            ("# Existing title", ""),
            ("- Existing item", ""),
        ],
        [],
    )

    assert "# Existing title" in markdown
    assert "- Existing item" in markdown


def test_build_markdown_fences_consecutive_code_lines():
    formatter = FormatService()

    markdown = formatter.build_markdown(
        [
            ("示例代码：", ""),
            ("def hello(name):", ""),
            ("    return f'hello {name}'", ""),
            ("print(hello('deepdoc'))", ""),
            ("后续说明", ""),
        ],
        [],
    )

    assert "```python\n" in markdown
    assert "def hello(name):" in markdown
    assert "    return f'hello {name}'" in markdown
    assert "\n```\n" in markdown
    assert "后续说明" in markdown


def test_build_markdown_cleans_deepdoc_table_artifacts():
    class FakeImage:
        size = (100, 100)
        mode = "RGB"

    formatter = FormatService()

    markdown = formatter.build_markdown(
        [],
        [
            (
                FakeImage(),
                "<table><tr><td>工具版本</td><td>发布日期</td></tr><tr><td>2.1.2.3</td><td>2024-01-15</td></tr></table>",
                [(0, 1.0, 2.0, 3.0, 4.0)],
            )
        ],
    )

    assert "PIL.Image" not in markdown
    assert "(0, 1.0" not in markdown
    assert "| 工具版本 | 发布日期 |" in markdown
    assert "| 2.1.2.3 | 2024-01-15 |" in markdown


def test_build_markdown_detects_inline_go_code_block():
    formatter = FormatService()

    markdown = formatter.build_markdown(
        [
            (
                '连接示例 package main import ( "database/sql" "fmt" ) var db *sql.DB func sqlOpen(){ db, err :=sql.Open("uxdb", "host=127.0.0.1 port=5432") if err !=nil { fmt.Println(err.Error()) } }',
                "",
            )
        ],
        [],
    )

    assert "连接示例" in markdown
    assert "```go\n" in markdown
    assert "package main" in markdown
    assert "func sqlOpen()" in markdown
