"""教育用のルービックキューブ ライブラリ。

キューブは 6 x 3 x 3 のリストで表す。

    cube[面][縦][横]        面 = 0:U(上) 1:L(左) 2:F(前) 3:R(右) 4:B(後) 5:D(下)
                            縦 = 0:上 1:中 2:下     横 = 0:左 1:中 2:右
                            中身 = 'B' 'Y' 'R' 'W' 'G' 'O' の1文字


使いかたは3通りある。どれも同じ名前の操作が使える。


1. いちばん手軽な使いかた
-------------------------

引数を省くと、rubik が持っている1つのキューブを回す。
3D の窓もひとりでに開いて、回すたびに描き直す。

    import rubik

    rubik.R()                     # 窓が開いて、右の面が回る
    rubik.U()
    rubik.do("RUR'U'", times=6)   # 手順をまとめて。6回で元に戻る
    rubik.show()                  # 展開図を文字で見る
    rubik.cube                    # いまの 6x3x3 リスト。直接読み書きできる

rubik.cube を直接書きかえたときは窓が追随しない。
描き直したければ rubik.update() を呼ぶ。

状態を変える呼び出し (R() や do()、solved()、shuffle()) は値を返さない。
Jupyter Notebook でセルに書いたとき、6x3x3 のリストがだらだら表示される
のを避けるため。いまの状態は rubik.cube で見る。


2. キューブを自分で作る使いかた
-------------------------------

    c = rubik.Cube()              # 完成状態のキューブを1つ作る
    c.R()
    c.do("RUR'U'")
    c.cube

    a = rubik.Cube(show3d=True)   # 3D の窓つき。2つ作れば窓も2つ
    b = rubik.Cube(show3d=True)


3. リストを自分で持ち回る使いかた
---------------------------------

キューブを引数に渡すと、操作は「もらったリストは書きかえず、
操作後の新しいリストを返す」ふつうの関数としてはたらく。窓も触らない。

    cube = rubik.Cube().cube      # 完成状態のリストを1つもらう
    after = rubik.R(cube)         # cube はそのまま残る


操作は18通り。X を U D L R F B のどれかとして、

    X    その面を時計回りに90度   (その面を外から見て時計回り)
    Xi   その面を反時計回りに90度  (X' のこと)
    X2   その面を180度

手順を文字列で渡す do() なら、X' の形もそのまま書ける。
"""

from . import moves as _moves
from . import state as _state
from . import viewer as _viewer

# --- リスト表現 -------------------------------------------------------
from .state import (
    UP, LEFT, FRONT, RIGHT, BACK, DOWN,
    FACE_NAMES, COLORS, SOLVED_COLORS,
    check, net,
)

# --- 操作の部品 -------------------------------------------------------
from .moves import ALL_MOVES, MOVE_NAMES, parse

# --- キューブを1つのモノとして扱う -----------------------------------
from .interactive import Cube

# --- 3Dグラフィクス ---------------------------------------------------
from .viewer import Viewer, reset_UFR, reset_DBL, wait, close


# ----------------------------------------------------------------------
# rubik が持っている1つのキューブ。
#
# 直接読んでよいし、書きかえてもよい。
# ただし書きかえても窓は追随しないので、描き直したければ update() を呼ぶ。
# ----------------------------------------------------------------------

cube = _state.solved()


def _current():
    """いま rubik が持っているキューブを返す。

    下の関数はどれも cube という名前の引数を取るので、そのままでは
    上の rubik.cube が隠れて読めない。それでこの小さな関数を通す。
    """
    return cube


# 下の2つはどちらも値を返さない。
#
# Jupyter Notebook はセルの最後に書いた式の値をそのまま画面に出すので、
# rubik.R() が値を返すと 6x3x3 のリストがだらだら表示されてしまう。
# 状態を変える呼び出しは、そろって何も返さないことにした。
# いまの状態がほしいときは rubik.cube を見る。

def _turned(new_cube):
    """回したあとの後始末。状態を進めて、窓を開いて描き直す。"""
    global cube
    cube = new_cube
    _viewer.update(cube)      # 窓がまだ一度も開いていなければ、ここで開く


def _prepared(new_cube):
    """キューブを用意しただけのときの後始末。

    状態は差しかえるが、窓はひとりでには開かない。
    すでに開いていれば描き直す。
    """
    global cube
    cube = new_cube
    if _viewer._alive():
        _viewer.update(cube)


# ----------------------------------------------------------------------
# 18通りの操作。
#
# 「引数を省いたら rubik.cube を回す、渡されたらそれを回して返す」という
# 同じ形なので、moves.py の表からまとめて作っている。18個を手で書くと、
# moves.py を直したときに必ずどこかがずれるため。
# 標準ライブラリの turtle も同じ理由で、モジュールの関数を Turtle クラスの
# メソッドから機械的に作っている。
# ----------------------------------------------------------------------

def _make_move(name):
    """名前 ('R' や 'Ui' など) から、モジュールの関数を1つ作る。"""
    turn = _moves.ALL_MOVES[name]

    def move(cube=None):
        if cube is not None:
            return turn(cube)            # 渡されたキューブを回して、返す
        _turned(turn(_current()))        # rubik.cube を回して窓も更新。何も返さない

    move.__name__ = name
    move.__doc__ = (
        (turn.__doc__ or "").rstrip()
        + "\n\n    引数を省くと rubik.cube を回して、3D の窓も描き直す。"
          "\n    このとき値は返さない。いまの状態は rubik.cube で見る。"
          "\n\n    キューブを渡すと、それを回した新しいリストを返す (窓は触らない)。"
    )
    return move


for _name in _moves.MOVE_NAMES:
    globals()[_name] = _make_move(_name)

del _name


# ----------------------------------------------------------------------
# 手順・キューブの用意・表示
# ----------------------------------------------------------------------

def do(sequence, cube=None, times=1):
    """手順をまとめて実行する。

    手順は R U R' U' のような、ふつうの書きかたの文字列。空白は無くてよい。

        rubik.do("RUR'U'")              # rubik.cube を回して窓も更新
        rubik.do("RUR'U'", times=6)     # 6回くり返すと元に戻る

        after = rubik.do("RU", before)  # 渡せば新しいリストを返すだけ

    引数を省いたときは値を返さない。いまの状態は rubik.cube で見る。
    """
    if cube is not None:
        return _moves.do(sequence, cube, times=times)
    _turned(_moves.do(sequence, _current(), times=times))


def solved():
    """rubik.cube を完成状態にする。

        rubik.solved()
        rubik.cube            # 完成状態のリスト

    値は返さない。窓が開いていれば描き直すが、
    窓がまだ無いときに、これだけで開くことはしない。
    """
    _prepared(_state.solved())


def shuffle(cube=None, times=20, seed=None):
    """でたらめに回して、ぐちゃぐちゃにする。

    seed に数を渡すと、何度やってもまったく同じ配置になる。

        rubik.shuffle()                    # rubik.cube がぐちゃぐちゃになる
        rubik.shuffle(seed=42)             # 何度やっても同じ配置
        rubik.cube                         # 結果のリスト

        after = rubik.shuffle(before, times=5)   # 渡せば新しいリストを返す

    引数を省いたときは値を返さない。
    """
    if cube is not None:
        return _moves.shuffle(cube, times=times, seed=seed)
    _prepared(_moves.shuffle(times=times, seed=seed))


def show(cube=None):
    """展開図の形でキューブを文字表示する。

    引数を省くと rubik.cube を表示する。
    """
    _state.show(_current() if cube is None else cube)


def is_solved(cube=None):
    """完成しているか。引数を省くと rubik.cube を見る。

    solved() は rubik.cube を完成状態にしてしまうので、
    出来ぐあいを調べたいときはこちらを使う。
    """
    return _state.is_solved(_current() if cube is None else cube)


# ----------------------------------------------------------------------
# 3Dグラフィクスの窓
# ----------------------------------------------------------------------

def init(cube=None):
    """3Dグラフィクスの窓を開く。

    引数を省くと、いまの rubik.cube を映す。
    窓を閉じたあと、もう一度出したいときにも使う。
    """
    _viewer.init(_current() if cube is None else cube)


def update(cube=None):
    """窓に映すキューブを更新する。向きは変わらない。

    引数を省くと、いまの rubik.cube を映す。
    rubik.cube を直接書きかえたあとに使う。
    """
    _viewer.update(_current() if cube is None else cube)


__all__ = [
    # リスト表現
    "UP", "LEFT", "FRONT", "RIGHT", "BACK", "DOWN",
    "FACE_NAMES", "COLORS", "SOLVED_COLORS",
    "check", "net", "show", "solved", "shuffle", "is_solved",
    # 18通りの操作
    "U", "Ui", "U2",
    "D", "Di", "D2",
    "L", "Li", "L2",
    "R", "Ri", "R2",
    "F", "Fi", "F2",
    "B", "Bi", "B2",
    "ALL_MOVES", "MOVE_NAMES", "parse", "do",
    # キューブを1つのモノとして
    "Cube",
    # 3Dグラフィクス
    "Viewer", "init", "update", "reset_UFR", "reset_DBL", "wait", "close",
]
