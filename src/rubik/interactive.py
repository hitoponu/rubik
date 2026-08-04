"""キューブを「1つのモノ」として扱う層。

標準ライブラリの turtle でいう Turtle クラスにあたる。

    c = rubik.Cube()          # 完成状態のキューブを1つ作る
    c.R()                     # 右の面を回す。c 自身が変わる
    c.do("RUR'U'")            # 手順をまとめて
    c.show()                  # 展開図を見る
    c.cube()                  # この個体の 6x3x3 リスト

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
    """1つのルービックキューブ。

    状態を変えるメソッド (回す、solved、shuffle、do、cube(x)) は値を返さない。
    Jupyter Notebook のセルで c.R() と書いたときに、6x3x3 のリストが
    だらだら表示されるのを避けるため。いまの状態は c.cube() で見る。
    """

    def __init__(self, cube=None, show3d=False):
        """完成状態のキューブを作る。

        cube に 6x3x3 のリストを渡すと、その状態から始める。
        渡したリストは写しを取るので、あとから書きかえても影響しない。

        show3d=True にすると、このキューブ専用の3Dの窓が開く。
        """
        if cube is None:
            self._cube = _state.solved()
        else:
            _state.check(cube)
            self._cube = copy.deepcopy(cube)

        self._viewer = None
        self._list_view = False
        if show3d:
            self.init()

    def __repr__(self):
        # Jupyter Notebook でセルに c と書くだけで展開図が出る
        return _state.net(self._cube)

    # --- 状態をあつかう ------------------------------------------------

    def cube(self, new_cube=None):
        """このキューブの中身 (6x3x3 のリスト) を返す。

            c.cube()             # いまの状態
            c.cube()[1][0][0]    # F面 (前) の左上のステッカー

        返ってくるのは写しではなく中身そのものなので、書きかえれば
        そのまま状態が変わる。窓は追随しないので update() を呼ぶ。

        リストを渡すと、そちらに差しかえる。このときは値を返さない。

            c.cube(x)
        """
        if new_cube is None:
            return self._cube
        _state.check(new_cube)
        self._cube = copy.deepcopy(new_cube)
        self._draw()

    def solved(self):
        """完成状態に戻す。"""
        self._cube = _state.solved()
        self._draw()

    def shuffle(self, times=20, seed=None):
        """完成状態からでたらめに回して、ぐちゃぐちゃにする。

        seed に数を渡すと、何度やってもまったく同じ配置になる。
        """
        self._cube = _moves.shuffle(times=times, seed=seed)
        self._draw()

    def do(self, sequence, times=1):
        """手順をまとめて実行する。

            c.do("RUR'U'")
            c.do("RUR'U'", times=6)   # 6回くり返すと元に戻る
        """
        self._cube = _moves.do(sequence, self._cube, times=times)
        self._draw()

    def show(self):
        """展開図を文字で表示する。"""
        _state.show(self._cube)

    def is_solved(self):
        """完成しているか。"""
        return _state.is_solved(self._cube)

    # --- 3D の窓 --------------------------------------------------------

    def init(self):
        """このキューブ専用の3Dの窓を開く。

        show3d=True で作ったときは、もう開いている。
        あとから窓がほしくなったときや、閉じた窓をもう一度出すときに呼ぶ。
        """
        if self._viewer is None:
            self._viewer = Viewer()
            self._viewer.list_view(self._list_view)
        self._viewer.init(self._cube)

    def update(self):
        """窓を今の状態に描き直す。

        c.cube() の中身を直接いじったあとに使う。回すメソッドは自分で描き直すので、
        ふだんは呼ばなくてよい。
        """
        self._draw()

    def _draw(self):
        """窓を持っていれば描き直す。持っていなければ何もしない。"""
        if self._viewer is not None:
            self._viewer.update(self._cube)

    def list_view(self, on=None):
        """このキューブの窓に、下のリスト表現を出すかどうか。

            c.list_view()        # いまの設定
            c.list_view(True)    # 出す

        窓をまだ持っていないときは、覚えておいて開いたときに反映する。
        """
        if on is None:
            return self._list_view
        self._list_view = bool(on)
        if self._viewer is not None:
            self._viewer.list_view(self._list_view)

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
        self._cube = turn(self._cube)
        self._draw()

    method.__name__ = name
    method.__qualname__ = f"Cube.{name}"
    method.__doc__ = (
        (turn.__doc__ or "").rstrip()
        + "\n\n        このキューブ自身が変わる。窓があれば描き直す。"
          "\n        値は返さない。いまの状態は c.cube() で見る。"
    )
    return method


for _name in _moves.MOVE_NAMES:
    setattr(Cube, _name, _make_move_method(_name))

del _name
