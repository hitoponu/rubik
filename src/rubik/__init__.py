"""教育用のルービックキューブ ライブラリ。

キューブは 6 x 3 x 3 のリストで表す。

    cube[面][縦][横]        面 = 0:U(上) 1:F(前) 2:R(右) 3:B(後) 4:L(左) 5:D(下)
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
    rubik.list_view(True)         # 窓の下にリスト表現も出す (ふつうは出ない)
    rubik.cube()                  # いまの 6x3x3 リスト
    rubik.cube(x)                 # 差しかえる

rubik.cube() が返すのは中身そのものなので、書きかえればそのまま状態が
変わる。ただし窓は追随しないので、描き直したければ rubik.update() を呼ぶ。

    from rubik import *           # rubik. を省いて書くこともできる

    R()
    cube()                        # いつでもいまの状態が返る

状態を変える呼び出し (R() や do()、solved()、shuffle()) は値を返さない。
Jupyter Notebook でセルに書いたとき、6x3x3 のリストがだらだら表示される
のを避けるため。いまの状態は cube() で見る。


2. キューブを自分で作る使いかた
-------------------------------

    c = rubik.Cube()              # 完成状態のキューブを1つ作る
    c.R()
    c.do("RUR'U'")
    c.cube()                      # この個体の 6x3x3 リスト

    a = rubik.Cube(show3d=True)   # 3D の窓つき。2つ作れば窓も2つ
    b = rubik.Cube(show3d=True)


3. リストを自分で持ち回る使いかた
---------------------------------

キューブを引数に渡すと、操作は「もらったリストは書きかえず、
操作後の新しいリストを返す」ふつうの関数としてはたらく。窓も触らない。

    cube = rubik.Cube().cube()    # 完成状態のリストを1つもらう
    after = rubik.R(cube)         # cube はそのまま残る


操作は27通り。X を U D L R F B M E S のどれかとして、

    X    時計回りに90度
    Xi   反時計回りに90度  (X' のこと)
    X2   180度

U D L R F B は外側の面を回す18通り。「時計回り」はその面を外から見た向き。
M E S はまん中の層だけを回す9通りで、それぞれ L, D, F と同じ向きに回る。

手順を文字列で渡す do() なら、X' の形もそのまま書ける。
"""

from . import moves as _moves
from . import state as _state
from . import viewer as _viewer

# --- リスト表現 -------------------------------------------------------
from .state import (
    UP, LEFT, FRONT, RIGHT, BACK, DOWN,
    FACE_NAMES, COLORS, SOLVED_COLORS,
    check, net, faces,
)

# --- 操作の部品 -------------------------------------------------------
from .moves import (
    ALL_MOVES, FACE_MOVES, SLICE_MOVES,
    MOVE_NAMES, FACE_MOVE_NAMES,
    parse,
)

# --- キューブを1つのモノとして扱う -----------------------------------
from .interactive import Cube

# --- 3Dグラフィクス ---------------------------------------------------
from .viewer import Viewer, list_view, reset_UFR, reset_DBL, wait, close


# ----------------------------------------------------------------------
# rubik が持っている1つのキューブ。
#
# 中身を取り出すには cube() を呼ぶ。変数ではなく関数にしてあるのは、
#
#     from rubik import *
#
# と書いたときに、いつでもいまの状態が取れるようにするため。
# 変数のままだと、取りこんだ時点の値がそのまま名前に貼りつくので、
# 操作しても古いままになってしまう。
# ----------------------------------------------------------------------

_cube = _state.solved()


def _current():
    """いま rubik が持っているキューブ。

    下の関数はどれも cube という名前の引数を取るので、そのままでは
    cube() が隠れて呼べない。それでこの小さな関数を通す。
    """
    return _cube


def _apply(new_cube):
    """いまのキューブを新しい状態にして、3D の窓も描き直す。

    窓がまだ一度も開いていなければ、ここで開く。
    引数を省いた呼び出し (R() や solved()、shuffle() など) は、
    みなこれを通る。

    値は返さない。Jupyter Notebook はセルの最後に書いた式の値をそのまま
    画面に出すので、ここで値を返すと 6x3x3 のリストがだらだら表示されて
    しまうため。いまの状態がほしいときは cube() を呼ぶ。
    """
    global _cube
    _cube = new_cube
    _viewer.update(_cube)


def cube(new_cube=None):
    """いまのキューブ (6x3x3 のリスト) を返す。

        rubik.cube()             # いまの状態
        rubik.cube()[1][0][0]    # F面 (前) の左上のステッカー

    返ってくるのは写しではなく中身そのものなので、書きかえればそのまま
    状態が変わる。ただし窓は追随しないので、描き直したければ update() を呼ぶ。

    キューブを渡すと、そちらに差しかえて 3D の窓も描き直す。
    このときは値を返さない。

        rubik.cube(x)
    """
    if new_cube is None:
        return _cube
    _apply(new_cube)


# ----------------------------------------------------------------------
# 27通りの操作。
#
# 「引数を省いたらいまのキューブを回す、渡されたらそれを回して返す」という
# 同じ形なので、moves.py の表からまとめて作っている。27個を手で書くと、
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
        _apply(turn(_current()))         # いまのキューブを回して窓も更新

    move.__name__ = name
    move.__doc__ = (
        (turn.__doc__ or "").rstrip()
        + "\n\n    引数を省くといまのキューブを回して、3D の窓も描き直す。"
          "\n    このとき値は返さない。いまの状態は cube() で見る。"
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

        rubik.do("RUR'U'")              # いまのキューブを回して窓も更新
        rubik.do("RUR'U'", times=6)     # 6回くり返すと元に戻る

        after = rubik.do("RU", before)  # 渡せば新しいリストを返すだけ

    引数を省いたときは値を返さない。いまの状態は cube() で見る。
    """
    if cube is not None:
        return _moves.do(sequence, cube, times=times)
    _apply(_moves.do(sequence, _current(), times=times))


def solved():
    """いまのキューブを完成状態にする。

        rubik.solved()
        rubik.cube()          # 完成状態のリスト

    値は返さない。3D の窓も描き直す (まだ開いていなければ、ここで開く)。
    """
    _apply(_state.solved())


def shuffle(cube=None, times=20, seed=None):
    """でたらめに回して、ぐちゃぐちゃにする。

    seed に数を渡すと、何度やってもまったく同じ配置になる。

        rubik.shuffle()                    # いまのキューブがぐちゃぐちゃになる
        rubik.shuffle(seed=42)             # 何度やっても同じ配置
        rubik.cube()                       # 結果のリスト

        after = rubik.shuffle(before, times=5)   # 渡せば新しいリストを返す

    引数を省いたときは値を返さず、3D の窓を描き直す
    (まだ開いていなければ、ここで開く)。
    """
    if cube is not None:
        return _moves.shuffle(cube, times=times, seed=seed)
    _apply(_moves.shuffle(times=times, seed=seed))


def show(cube=None):
    """展開図の形でキューブを文字表示する。

    引数を省くといまのキューブを表示する。
    """
    _state.show(_current() if cube is None else cube)


def is_solved(cube=None):
    """完成しているか。引数を省くといまのキューブを見る。

    solved() はいまのキューブを完成状態にしてしまうので、
    出来ぐあいを調べたいときはこちらを使う。
    """
    return _state.is_solved(_current() if cube is None else cube)


# ----------------------------------------------------------------------
# 3Dグラフィクスの窓
# ----------------------------------------------------------------------

def init(cube=None):
    """3Dグラフィクスの窓を開く。

    引数を省くと、いまのキューブを映す。
    窓を閉じたあと、もう一度出したいときにも使う。
    """
    _viewer.init(_current() if cube is None else cube)


def update(cube=None):
    """窓に映すキューブを更新する。向きは変わらない。

    引数を省くと、いまのキューブを映す。
    rubik.cube() の中身を直接書きかえたあとに使う。
    """
    _viewer.update(_current() if cube is None else cube)


__all__ = [
    # いま rubik が持っているキューブを取り出す
    "cube",
    # リスト表現
    "UP", "LEFT", "FRONT", "RIGHT", "BACK", "DOWN",
    "FACE_NAMES", "COLORS", "SOLVED_COLORS",
    "check", "net", "faces", "show", "solved", "shuffle", "is_solved",
    # 外側の面を回す18通り
    "U", "Ui", "U2",
    "D", "Di", "D2",
    "L", "Li", "L2",
    "R", "Ri", "R2",
    "F", "Fi", "F2",
    "B", "Bi", "B2",
    # 中段 (スライス) の9通り
    "M", "Mi", "M2",
    "E", "Ei", "E2",
    "S", "Si", "S2",
    "ALL_MOVES", "FACE_MOVES", "SLICE_MOVES",
    "MOVE_NAMES", "FACE_MOVE_NAMES", "parse", "do",
    # キューブを1つのモノとして
    "Cube",
    # 3Dグラフィクス
    "Viewer", "init", "update", "list_view",
    "reset_UFR", "reset_DBL", "wait", "close",
]
