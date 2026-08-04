"""3Dグラフィクスの窓を操作する。

    rubik.init()          窓を開く
    rubik.update(cube)    映すキューブを更新する (向きは変わらない)
    rubik.list_view(True) キューブの下にリスト表現を出す
    rubik.reset_UFR()     見る向きを U・F・R が見える向きに戻す
    rubik.reset_DBL()     見る向きを D・B・L が見える向きに戻す
    rubik.wait()          窓が閉じられるまで待つ
    rubik.close()         窓を閉じる

窓は別のプロセス (_window.py) で動いていて、ここではそのプロセスに
指示を1行の JSON にして送りつけているだけ。

窓 1 つぶんの世話は Viewer クラスにまとめてある。
上に並べた関数は、このファイルの下のほうで作る「既定の Viewer」1 つに
用事を頼んでいるだけ。自分だけの窓がほしいときは Viewer をもう1つ作る
(Cube(show3d=True) がそうしている)。
"""

import atexit
import importlib.util
import json
import os
import subprocess
import sys

from .state import check, solved


class Viewer:
    """3Dグラフィクスの窓 1 つ。"""

    def __init__(self):
        # 窓のプロセス。まだ開いていなければ None。
        self._process = None

        # キューブの下にリスト表現の文字を出すか。ふつうは出さない。
        self._list_view = False

        # 一度でも窓を開こうとしたか。
        # 画面の無い場所 (Google Colab など) では窓を開けないので、操作の
        # たびに開こうとするとプロセスが無駄に増えてしまう。だから
        # 「ひとりでに開こうとするのは1回きり」にしてある。
        self._attempted = False

    # ------------------------------------------------------------------

    def alive(self):
        """窓のプロセスが生きているか。"""
        return self._process is not None and self._process.poll() is None

    def _send(self, message):
        """指示を1行の JSON にして窓のプロセスに送る。窓が無ければ何もしない。

        message は {"cube": [...]}、{"view": "UFR"}、{"list": True} のどれか。
        """
        if not self.alive():
            return
        try:
            self._process.stdin.write(json.dumps(message) + "\n")
            self._process.stdin.flush()
        except (BrokenPipeError, ValueError, OSError):
            # 窓が閉じられた直後などに起きる。特に困らないので黙って見送る。
            pass

    # ------------------------------------------------------------------

    def init(self, cube=None):
        """窓を開く。

        cube を渡すとその状態で、渡さなければ完成状態で開く。
        すでに開いていれば何もしない。
        窓を閉じたあとにもう一度呼べば、開きなおす。
        """
        if self.alive():
            if cube is not None:
                self.update(cube)
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

        self._attempted = True

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
        self._process = subprocess.Popen(
            [sys.executable, "-m", "rubik._window"],
            stdin=subprocess.PIPE,
            text=True,
            env=child_env,
        )
        atexit.register(self.close)

        self._send({"cube": cube, "list": self._list_view})

    def update(self, cube):
        """窓に映すキューブを更新する。

        窓をマウスで回して見ている向きは、この更新では変わらない。
        まだ一度も窓を開いていなければ、ここで開く。

        窓を閉じたあとは黙って何もしない。もう一度出したいときは init() を呼ぶ。
        """
        check(cube)

        if self.alive():
            self._send({"cube": cube})
        elif not self._attempted:
            self.init(cube)

    def list_view(self, on=None):
        """キューブの下にリスト表現の文字を出すかどうか。

            v.list_view()        # いまの設定 (True か False)
            v.list_view(True)    # 出す
            v.list_view(False)   # 消す

        ふつうは出さない。出すとそのぶんキューブが小さくなる。
        設定を渡したときは値を返さない。
        """
        if on is None:
            return self._list_view
        self._list_view = bool(on)
        self._send({"list": self._list_view})

    def reset_UFR(self):
        """見る向きを、U面・F面・R面が見える向きに戻す。

        窓を開いたときの、最初の向きと同じ。
        マウスで回しすぎて分からなくなったときに使う。
        """
        self._send({"view": "UFR"})

    def reset_DBL(self):
        """見る向きを、D面・B面・L面が見える向きに戻す。

        reset_UFR() のちょうど裏がわから見た向き。
        2つを行き来すれば、6面すべてを確かめられる。
        """
        self._send({"view": "DBL"})

    def wait(self):
        """窓が閉じられるまで待つ。

        プログラムの一番最後に置く。これが無いとプログラムの終わりと同時に
        窓も消えてしまう。

        Jupyter Notebook では呼ばないこと。閉じるまでカーネルが止まる。
        """
        if self._process is None:
            return
        try:
            self._process.wait()
        except KeyboardInterrupt:
            self.close()

    def close(self):
        """窓を閉じる。"""
        if self._process is None:
            return

        if self._process.poll() is None:
            try:
                self._process.stdin.close()   # パイプを閉じると窓が自分で終わる
            except (BrokenPipeError, ValueError, OSError):
                pass
            try:
                self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()

        self._process = None


# ----------------------------------------------------------------------
# ふだん使う窓 1 つ。下の関数はここに用事を頼む。
# ----------------------------------------------------------------------

_default = Viewer()


def init(cube=None):
    """3Dグラフィクスの窓を開く。"""
    _default.init(cube)


def update(cube):
    """窓に映すキューブを更新する。向きは変わらない。"""
    _default.update(cube)


def list_view(on=None):
    """キューブの下にリスト表現を出すかどうか。引数なしならいまの設定を返す。"""
    return _default.list_view(on)


def reset_UFR():
    """見る向きを、U面・F面・R面が見える向きに戻す。"""
    _default.reset_UFR()


def reset_DBL():
    """見る向きを、D面・B面・L面が見える向きに戻す。"""
    _default.reset_DBL()


def wait():
    """窓が閉じられるまで待つ。"""
    _default.wait()


def close():
    """窓を閉じる。"""
    _default.close()


def _alive():
    """既定の窓が生きているか。"""
    return _default.alive()
