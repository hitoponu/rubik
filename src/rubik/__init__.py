"""教育用のルービックキューブ ライブラリ。

キューブは 6 x 3 x 3 のリストで表す。

    cube[面][縦][横]        面 = 0:U(上) 1:L(左) 2:F(前) 3:R(右) 4:B(後) 5:D(下)
                            縦 = 0:上 1:中 2:下     横 = 0:左 1:中 2:右
                            中身 = 'B' 'Y' 'R' 'W' 'G' 'O' の1文字

使いかた

    import rubik

    cube = rubik.solved()          # 完成状態を作る
    cube = rubik.shuffle()         # でたらめに回してぐちゃぐちゃにする
    cube = rubik.R(cube)           # 右の面を時計回りに90度
    cube = rubik.Ui(cube)          # 上の面を反時計回りに90度
    rubik.show(cube)               # 展開図を文字で表示

    rubik.init()                   # 3Dの窓を開く
    rubik.update(cube)             # 窓に映すキューブを更新
    rubik.reset_UFR()              # 見る向きを U,F,R が見える向きに戻す
    rubik.reset_DBL()              # 見る向きを D,B,L が見える向きに戻す
    rubik.wait()                   # 窓が閉じられるまで待つ

操作の関数は18通り。X を U D L R F B のどれかとして、

    X    その面を時計回りに90度   (その面を外から見て時計回り)
    Xi   その面を反時計回りに90度  (X' のこと)
    X2   その面を180度

どれも「操作前のキューブをもらって、操作後の新しいキューブを返す」。
もらったキューブは書きかえない。
"""

# --- リスト表現 -------------------------------------------------------
from .cube import (
    UP, LEFT, FRONT, RIGHT, BACK, DOWN,
    FACE_NAMES, COLORS, SOLVED_COLORS,
    check, solved, show,
)

# --- 18通りの操作 -----------------------------------------------------
from .moves import (
    U, Ui, U2,
    D, Di, D2,
    L, Li, L2,
    R, Ri, R2,
    F, Fi, F2,
    B, Bi, B2,
    ALL_MOVES, MOVE_NAMES, shuffle,
)

# --- 3Dグラフィクス ---------------------------------------------------
from .viewer import init, update, reset_UFR, reset_DBL, wait, close

__all__ = [
    "UP", "LEFT", "FRONT", "RIGHT", "BACK", "DOWN",
    "FACE_NAMES", "COLORS", "SOLVED_COLORS",
    "check", "solved", "show",
    "U", "Ui", "U2",
    "D", "Di", "D2",
    "L", "Li", "L2",
    "R", "Ri", "R2",
    "F", "Fi", "F2",
    "B", "Bi", "B2",
    "ALL_MOVES", "MOVE_NAMES", "shuffle",
    "init", "update", "reset_UFR", "reset_DBL", "wait", "close",
]
