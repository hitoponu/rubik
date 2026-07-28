"""3Dグラフィクスの窓を操作する4つの関数。

    rubik.init()          窓を開く
    rubik.update(cube)    映すキューブを更新する (向きは変わらない)
    rubik.wait()          窓が閉じられるまで待つ
    rubik.close()         窓を閉じる

窓は別のプロセス (_window.py) で動いていて、ここではそのプロセスに
キューブを1行の JSON にして送りつけているだけ。
"""

import atexit
import importlib.util
import json
import os
import subprocess
import sys

from .cube import check, solved

# 窓のプロセス。まだ開いていなければ None。
_process = None


def _alive():
    """窓のプロセスが生きているか。"""
    return _process is not None and _process.poll() is None


def _send(message):
    """指示を1行の JSON にして窓のプロセスに送る。窓が無ければ何もしない。

    message は {"cube": [...]} か {"view": "UFR"} のどちらか。
    """
    if not _alive():
        return
    try:
        _process.stdin.write(json.dumps(message) + "\n")
        _process.stdin.flush()
    except (BrokenPipeError, ValueError, OSError):
        # 窓が閉じられた直後などに起きる。特に困らないので黙って見送る。
        pass


def init(cube=None):
    """3Dグラフィクスの窓を開く。

    cube を渡すとその状態で、渡さなければ完成状態で開く。
    すでに開いていれば何もしない。
    """
    global _process

    if _alive():
        if cube is not None:
            update(cube)
        return

    if importlib.util.find_spec("matplotlib") is None:
        raise RuntimeError(
            "3Dグラフィクスには matplotlib が必要です。"
            "「uv add matplotlib」または「pip install matplotlib」で入れてください。"
        )

    if cube is None:
        cube = solved()
    else:
        check(cube)

    # 子プロセスに渡す環境をととのえる。
    #
    # Jupyter Notebook は MPLBACKEND という環境変数に「窓を出さずにノートへ
    # 絵を貼る方式」を書きこむ。これをそのまま引きつぐと、子プロセスは
    # 窓を出さずに終わってしまう。しかも、その方式を実現する部品が子の側に
    # 入っていないと、絵を描く準備の途中でエラーになって落ちる。
    # そこで、この1つだけ取りのぞいて渡す。
    child_env = dict(os.environ)
    child_env.pop("MPLBACKEND", None)

    # 別プロセスとして窓を立ち上げる。標準入力をパイプにしておいて、
    # そこにキューブを流しこむ。
    _process = subprocess.Popen(
        [sys.executable, "-m", "rubik._window"],
        stdin=subprocess.PIPE,
        text=True,
        env=child_env,
    )
    atexit.register(close)

    _send({"cube": cube})


def update(cube):
    """窓に映すキューブを更新する。

    窓をマウスで回して見ている向きは、この更新では変わらない。
    まだ窓が開いていなければ、開いてから映す。
    """
    check(cube)

    if not _alive():
        init(cube)
        return

    _send({"cube": cube})


def reset_UFR():
    """見る向きを、U面・F面・R面が見える向きに戻す。

    窓を開いたときの、最初の向きと同じ。
    マウスで回しすぎて分からなくなったときに使う。
    """
    _send({"view": "UFR"})


def reset_DBL():
    """見る向きを、D面・B面・L面が見える向きに戻す。

    reset_UFR() のちょうど裏がわから見た向き。
    2つを行き来すれば、6面すべてを確かめられる。
    """
    _send({"view": "DBL"})


def wait():
    """窓が閉じられるまで待つ。

    プログラムの一番最後に置く。これが無いとプログラムの終わりと同時に
    窓も消えてしまう。
    """
    if _process is None:
        return
    try:
        _process.wait()
    except KeyboardInterrupt:
        close()


def close():
    """窓を閉じる。"""
    global _process

    if _process is None:
        return

    if _process.poll() is None:
        try:
            _process.stdin.close()      # パイプを閉じると窓が自分で終わる
        except (BrokenPipeError, ValueError, OSError):
            pass
        try:
            _process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            _process.kill()

    _process = None
