"""キューブを「1つのモノ」として扱う層。

標準ライブラリの turtle でいう Turtle クラスにあたる。

    c = rubik.Cube()          # 完成状態のキューブを1つ作る
    c.R()                     # 右の面を回す。c 自身が変わる
    c.do("RUR'U'")            # 手順をまとめて
    c.show()                  # 展開図を見る
    c.cube                    # この個体の 6x3x3 リスト

3D の窓がほしいときは show3d=True を渡す。Cube ごとに別の窓が開くので、
2つ作って並べて見くらべることもできる。

    a = rubik.Cube(show3d=True)
    b = rubik.Cube(show3d=True)   # 2つめの窓

18通りの操作のメソッドは、moves.py の表からまとめて作っている
(このファイルの一番下)。1つずつ手で書くと、moves.py を直したときに
必ずどこかがずれるため。turtle も同じ理由で、モジュールの関数を
Turtle クラスのメソッドから機械的に作っている。
"""

import copy

from . import moves as _moves
from . import state as _state
from .viewer import Viewer


class Cube:
    """1つのルービックキューブ。"""

    def __init__(self, cube=None, show3d=False):
        """完成状態のキューブを作る。

        cube に 6x3x3 のリストを渡すと、その状態から始める。
        渡したリストは写しを取るので、あとから書きかえても影響しない。

        show3d=True にすると、このキューブ専用の3Dの窓が開く。
        """
        if cube is None:
            self.cube = _state.solved()
        else:
            _state.check(cube)
            self.cube = copy.deepcopy(cube)

        self._viewer = None
        if show3d:
            self.init()

    def __repr__(self):
        # Jupyter Notebook でセルに c と書くだけで展開図が出る
        return _state.net(self.cube)

    # --- 状態をあつかう ------------------------------------------------

    def set(self, cube):
        """状態を丸ごと差しかえる。"""
        _state.check(cube)
        self.cube = copy.deepcopy(cube)
        self._draw()
        return self.cube

    def solved(self):
        """完成状態に戻す。"""
        self.cube = _state.solved()
        self._draw()
        return self.cube

    def shuffle(self, times=20, seed=None):
        """完成状態からでたらめに回して、ぐちゃぐちゃにする。

        seed に数を渡すと、何度やってもまったく同じ配置になる。
        """
        self.cube = _moves.shuffle(times=times, seed=seed)
        self._draw()
        return self.cube

    def do(self, sequence, times=1):
        """手順をまとめて実行する。

            c.do("RUR'U'")
            c.do("RUR'U'", times=6)   # 6回くり返すと元に戻る
        """
        self.cube = _moves.do(sequence, self.cube, times=times)
        self._draw()
        return self.cube

    def show(self):
        """展開図を文字で表示する。"""
        _state.show(self.cube)

    def is_solved(self):
        """完成しているか。"""
        return _state.is_solved(self.cube)

    # --- 3D の窓 --------------------------------------------------------

    def init(self):
        """このキューブ専用の3Dの窓を開く。

        show3d=True で作ったときは、もう開いている。
        あとから窓がほしくなったときや、閉じた窓をもう一度出すときに呼ぶ。
        """
        if self._viewer is None:
            self._viewer = Viewer()
        self._viewer.init(self.cube)

    def update(self):
        """窓を今の状態に描き直す。

        c.cube を直接いじったあとに使う。回すメソッドは自分で描き直すので、
        ふだんは呼ばなくてよい。
        """
        self._draw()

    def _draw(self):
        """窓を持っていれば描き直す。持っていなければ何もしない。"""
        if self._viewer is not None:
            self._viewer.update(self.cube)

    def reset_UFR(self):
        """見る向きを、U面・F面・R面が見える向きに戻す。"""
        if self._viewer is not None:
            self._viewer.reset_UFR()

    def reset_DBL(self):
        """見る向きを、D面・B面・L面が見える向きに戻す。"""
        if self._viewer is not None:
            self._viewer.reset_DBL()

    def wait(self):
        """窓が閉じられるまで待つ。

        Jupyter Notebook では呼ばないこと。閉じるまでカーネルが止まる。
        """
        if self._viewer is not None:
            self._viewer.wait()

    def close(self):
        """窓を閉じる。"""
        if self._viewer is not None:
            self._viewer.close()


# ----------------------------------------------------------------------
# 18通りの操作を、Cube のメソッドとしてまとめて作る。
# ----------------------------------------------------------------------

def _make_move_method(name):
    """名前 ('R' や 'Ui' など) から、Cube のメソッドを1つ作る。"""
    turn = _moves.ALL_MOVES[name]

    def method(self):
        self.cube = turn(self.cube)
        self._draw()
        return self.cube

    method.__name__ = name
    method.__qualname__ = f"Cube.{name}"
    method.__doc__ = (
        (turn.__doc__ or "").rstrip()
        + "\n\n        このキューブ自身が変わる。窓があれば描き直す。"
    )
    return method


for _name in _moves.MOVE_NAMES:
    setattr(Cube, _name, _make_move_method(_name))

del _name
