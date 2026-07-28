"""ルービックキューブのリスト表現。

キューブは 6 x 3 x 3 の入れ子リストで表す。

    cube[面][縦][横]

要素は 'B'(青) 'Y'(黄) 'R'(赤) 'W'(白) 'G'(緑) 'O'(橙) のいずれか1文字。


面の番号と展開図
----------------

            +-------+
            | 0  U  |          0 = U  上 (Up)
    +-------+-------+-------+-------+
    | 1  L  | 2  F  | 3  R  | 4  B  |
    +-------+-------+-------+-------+
            | 5  D  |
            +-------+

各面は「その面をキューブの外側から見た状態」で、
縦座標 row は 0 が上・2 が下、横座標 col は 0 が左・2 が右。

「上」がどちらを向いているかは面ごとに次のように決めた。

    L, F, R, B ... U 面の側が「上」
    U          ... B 面の側が「上」
    D          ... F 面の側が「上」

これは展開図をそのまま紙に描いて折りたたむと立方体になる、標準的な向きの取り方。
この決め方には利点があって、中段の L, F, R, B をこの順に並べておくと、
U 操作と D 操作が「4つの面の row を順ぐりにずらすだけ」になり、
添字をひっくり返す処理が一切出てこない (moves.py 参照)。
"""

# 面の番号。moves.py から使う。
UP, LEFT, FRONT, RIGHT, BACK, DOWN = 0, 1, 2, 3, 4, 5

# 面の番号 -> 表示用の名前
FACE_NAMES = ["U", "L", "F", "R", "B", "D"]

# ステッカーに使える色。これ以外の値が入っていたら間違い。
COLORS = ("B", "Y", "R", "W", "G", "O")

# 完成状態でそれぞれの面に来る色。
# 白の裏が黄、緑の裏が青、赤の裏が橙、という一般的な配色にしてある。
SOLVED_COLORS = {
    UP: "W",     # 白
    LEFT: "O",   # 橙
    FRONT: "G",  # 緑
    RIGHT: "R",  # 赤
    BACK: "B",   # 青
    DOWN: "Y",   # 黄
}


def check(cube):
    """cube がルービックキューブとして正しい形をしているか確かめる。

    見るのは次の3つ。おかしければ assert で止まる。
    操作の関数はすべて最初にこれを呼ぶ。

        1. そもそもリストか
        2. 6x3x3 のリストか
        3. 中身が 'B' 'Y' 'R' 'W' 'G' 'O' のどれかか
    """
    # 1. そもそもリストか
    assert isinstance(cube, list), "ルービックキューブはリストで渡してください。"

    # 2. 6x3x3 のリストか
    ok = len(cube) == 6
    if ok:
        for face in cube:
            if not isinstance(face, list) or len(face) != 3:
                ok = False
                break
            for row in face:
                if not isinstance(row, list) or len(row) != 3:
                    ok = False
                    break
            if not ok:
                break

    assert ok, "ルービックキューブは 6x3x3 のリストで渡してください。"

    # 3. 中身が使える色か。
    #    54枚すべてを見て、色として使えないものの場所を集める。
    bad = [
        (face, row, col)
        for face in range(6)
        for row in range(3)
        for col in range(3)
        if cube[face][row][col] not in COLORS
    ]

    # assert のうしろのメッセージは、条件が成り立たなかったときだけ作られる。
    # だから普段は _color_error() は呼ばれない。
    assert not bad, _color_error(cube, bad[0])


def _color_error(cube, position):
    """使えない色が入っていたときの、日本語のお知らせを組み立てる。"""
    face, row, col = position
    return (
        "ルービックキューブの中身は "
        + " ".join(repr(c) for c in COLORS)
        + " のどれかにしてください。"
        + f"cube[{face}][{row}][{col}] "
        + f"({FACE_NAMES[face]}面の 縦{row} 横{col}) が "
        + f"{cube[face][row][col]!r} になっています。"
    )


def solved():
    """完成状態のルービックキューブを新しく作って返す。"""
    cube = []
    for face in range(6):
        color = SOLVED_COLORS[face]
        cube.append([[color, color, color] for _ in range(3)])
    return cube


def show(cube):
    """展開図の形でキューブを文字表示する。

    3D ウィンドウの見た目とリストの中身が合っているか確かめたいときに使う。
    """
    check(cube)

    space = "       "  # 面1つぶんの幅 (3文字 + 区切りの空白)

    # 上段: U 面
    for row in range(3):
        print(space + " ".join(cube[UP][row]))

    # 中段: L, F, R, B 面を横に並べる
    for row in range(3):
        parts = []
        for face in (LEFT, FRONT, RIGHT, BACK):
            parts.append(" ".join(cube[face][row]))
        print("  ".join(parts))

    # 下段: D 面
    for row in range(3):
        print(space + " ".join(cube[DOWN][row]))
