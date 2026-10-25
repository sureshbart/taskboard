import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "taskboard.py"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def make_board() -> Path:
    path = HERE / "_board.txt"
    path.write_text(
        "# 看板\n"
        "[todo] 写接口文档 @me #doc\n"
        "[doing] 修登录超时 @ana #bug\n"
        "[done] 初始化仓库\n",
        encoding="utf-8",
    )
    return path


def test_show_groups():
    path = make_board()
    result = run("show", str(path))
    assert result.returncode == 0, result.stderr
    assert "TODO  (1)" in result.stdout, result.stdout
    assert "DOING  (1)" in result.stdout, result.stdout
    assert "共 3 个任务" in result.stdout, result.stdout
    path.unlink()


def test_show_json():
    path = make_board()
    result = run("show", str(path), "--json")
    payload = json.loads(result.stdout)
    assert len(payload) == 3, payload
    assert payload[0]["owner"] == "me", payload[0]
    assert payload[0]["tags"] == ["doc"], payload[0]
    assert payload[1]["status"] == "doing", payload[1]
    path.unlink()


def test_move():
    path = make_board()
    result = run("move", str(path), "3", "done")
    assert result.returncode == 0, result.stderr
    content = path.read_text(encoding="utf-8")
    assert "[done] 修登录超时 @ana #bug" in content, content
    path.unlink()


def test_add():
    path = make_board()
    result = run("add", str(path), "新任务 @bob #x", "--status", "doing")
    assert result.returncode == 0, result.stderr
    content = path.read_text(encoding="utf-8")
    assert "[doing] 新任务 @bob #x" in content, content
    path.unlink()


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"ok  {name}")
    print("all tests passed")
