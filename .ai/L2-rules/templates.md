# 新建文件模板

> 本仓库主要新增 3 类文件：抓取脚本、pytest、Markdown 生成器辅助函数。

## Python CLI 脚本模板

```python
import argparse
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output" / "source-name"


def render_markdown(payload: dict) -> str:
  lines = [f"# {payload['title']}", "", payload.get("summary", "")]
  return "\n".join(lines)


def save_result(payload: dict, output_dir: Path) -> Path:
  output_dir.mkdir(parents=True, exist_ok=True)
  target = output_dir / "result.md"
  target.write_text(render_markdown(payload), encoding="utf-8")
  return target


def main() -> None:
  parser = argparse.ArgumentParser(description="Describe the CLI clearly")
  parser.add_argument("target")
  parser.add_argument("-o", "--output", type=Path, default=OUTPUT_DIR)
  args = parser.parse_args()
  payload = {"title": args.target, "summary": "..."}
  saved = save_result(payload, args.output)
  print(f"Saved: {saved}")


if __name__ == "__main__":
  main()
```

## pytest 单元测试模板

```python
from pathlib import Path

from module_under_test import render_markdown, save_result


def test_render_markdown_includes_title() -> None:
  payload = {"title": "Example", "summary": "Body"}

  result = render_markdown(payload)

  assert result.startswith("# Example")
  assert "Body" in result


def test_save_result_writes_utf8_file(tmp_path: Path) -> None:
  payload = {"title": "Example", "summary": "Body"}

  target = save_result(payload, tmp_path)

  assert target.exists()
  assert target.read_text(encoding="utf-8").startswith("# Example")
```

## Markdown 组装模板

```python
def build_markdown(meta: dict, body: str) -> str:
  return "\n".join(
    [
      f"# {meta['title']}",
      "",
      f"> Source: {meta['source_url']}",
      "",
      body,
      "",
    ]
  )
```
