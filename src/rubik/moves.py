"""ルービックキューブの操作。外側の面が18通り、中段が9通りで、合わせて27通り。

関数はすべて「操作前のキューブをもらって、操作後の新しいキューブを返す」形。
もらったキューブは書き換えないので、安心して使い回せる。

    U   上の面を時計回りに90度
    Ui  上の面を反時計回りに90度  (U' のこと。i は inverse の i)
    U2  上の面を180度

同じものが D, L, R, F, B にもあって、合わせて 6 x 3 = 18 通り。
「時計回り」はいつも「その面を外側から見て時計回り」の意味。

これに加えて、まん中の層だけを回す「中段」が M, E, S の 3 x 3 = 9 通り。
合わせて 27 通りになる。


どうやって回しているか
----------------------

1回の90度回転で動くステッカーは、4枚ずつの組に分けられる。
たとえば U を回すと、F 面の上の段は L 面の上の段へ、L 面の上の段は B 面へ……
というように、4枚がぐるぐると席を交換していく。この4枚組を「巡回」と呼ぶ。

そこで、6つの基本操作 (時計回り90度) それぞれについて巡回の一覧を表として書き
下しておき、あとはその通りにステッカーを移すだけにした。
反時計回りと180度は、時計回りを3回・2回と繰り返して作る。
遠回りだが、覚えることが増えないので間違えにくい。
"""

import copy
import random

from .state import UP, LEFT, FRONT, RIGHT, BACK, DOWN, check, solved


def _face_cycles(face):
    """face 番の面それ自身を時計回りに回すための巡回。

    真ん中のステッカーはその場から動かないので、角の4枚と辺の4枚だけ。
    どの面も「外側から見た向き」で座標を決めてあるので、6面とも全く同じ形になる。

        (0,0) -> (0,2) -> (2,2) -> (2,0) -> もどる     角
        (0,1) -> (1,2) -> (2,1) -> (1,0) -> もどる     辺
    """
    return [
        [(face, 0, 0), (face, 0, 2), (face, 2, 2), (face, 2, 0)],
        [(face, 0, 1), (face, 1, 2), (face, 2, 1), (face, 1, 0)],
    ]


# 基本操作ごとの「まわりの4面をまたぐ」巡回の一覧。
# i は 0, 1, 2 と動いて、3枚ぶんの巡回をまとめて作っている。
#
# U と D は添字がそのまま (2-i のようなひっくり返しが出てこない)。
# まわりの4面 (F, R, B, L) の座標が、ぐるっと一周そろっているおかげ。
_SIDE_CYCLES = {
    "U": [[(FRONT, 0, i), (LEFT, 0, i), (BACK, 0, i), (RIGHT, 0, i)] for i in range(3)],
    "D": [[(FRONT, 2, i), (RIGHT, 2, i), (BACK, 2, i), (LEFT, 2, i)] for i in range(3)],
    # R, L, F, B は、隣り合う面どうしで上下や左右の向きが逆になる場所があるため、
    # 2-i というひっくり返しが出てくる。これは避けようがない。
    "R": [[(UP, i, 2), (BACK, 2 - i, 0), (DOWN, i, 2), (FRONT, i, 2)] for i in range(3)],
    "L": [[(UP, i, 0), (FRONT, i, 0), (DOWN, i, 0), (BACK, 2 - i, 2)] for i in range(3)],
    "F": [[(UP, 2, i), (RIGHT, i, 0), (DOWN, 0, 2 - i), (LEFT, 2 - i, 2)] for i in range(3)],
    "B": [[(UP, 0, i), (LEFT, 2 - i, 0), (DOWN, 2, 2 - i), (RIGHT, i, 2)] for i in range(3)],

    # --- 中段 (スライス) の3つ -----------------------------------------
    #
    # まん中の層だけを回す。外側の面はどれも回らないので、動くのは
    # まわりの4面の中央の列 (または段) の12枚だけ。真ん中のステッカーも動く。
    #
    # 向きは、隣り合う外側の面に合わせるのが決まりごと。
    #   M ... L (左) と同じ向き
    #   E ... D (下) と同じ向き
    #   S ... F (前) と同じ向き
    #
    # 表の中身は、L / D / F の行の添字をまん中にずらしたものになっている。
    "M": [[(UP, i, 1), (FRONT, i, 1), (DOWN, i, 1), (BACK, 2 - i, 1)] for i in range(3)],
    "E": [[(FRONT, 1, i), (RIGHT, 1, i), (BACK, 1, i), (LEFT, 1, i)] for i in range(3)],
    "S": [[(UP, 1, i), (RIGHT, i, 1), (DOWN, 1, 2 - i), (LEFT, 2 - i, 1)] for i in range(3)],
}

# 基本操作の名前 -> 回す面の番号。
# 中段の M / E / S はどの面も回さないので、ここには載せない。
_TURNED_FACE = {"U": UP, "D": DOWN, "L": LEFT, "R": RIGHT, "F": FRONT, "B": BACK}


def _turn(cube, name):
    """name ('U' や 'M' など) を時計回りに90度回した、新しいキューブを返す。"""
    check(cube)

    new = copy.deepcopy(cube)
    cycles = list(_SIDE_CYCLES[name])
    if name in _TURNED_FACE:
        # 外側の面を回す操作は、その面そのものもまわる
        cycles += _face_cycles(_TURNED_FACE[name])

    for cycle in cycles:
        for i in range(4):
            face, row, col = cycle[i]                  # 移動もとの席
            to_face, to_row, to_col = cycle[(i + 1) % 4]  # 移動さきの席
            new[to_face][to_row][to_col] = cube[face][row][col]

    return new


# ----------------------------------------------------------------------
# 18通りの操作
#
# 反時計回り (Ui) は時計回りを3回、180度 (U2) は2回。
# 同じことを3回するのは無駄だが、新しい表を作らなくてよいぶん間違いが起きない。
# ----------------------------------------------------------------------

def U(cube):
    """上の面 (U) を時計回りに90度。"""
    return _turn(cube, "U")


def Ui(cube):
    """上の面 (U) を反時計回りに90度。時計回りを3回まわすのと同じ。"""
    return U(U(U(cube)))


def U2(cube):
    """上の面 (U) を180度。"""
    return U(U(cube))


def D(cube):
    """下の面 (D) を時計回りに90度。下から見て時計回り。"""
    return _turn(cube, "D")


def Di(cube):
    """下の面 (D) を反時計回りに90度。"""
    return D(D(D(cube)))


def D2(cube):
    """下の面 (D) を180度。"""
    return D(D(cube))


def L(cube):
    """左の面 (L) を時計回りに90度。左から見て時計回り。"""
    return _turn(cube, "L")


def Li(cube):
    """左の面 (L) を反時計回りに90度。"""
    return L(L(L(cube)))


def L2(cube):
    """左の面 (L) を180度。"""
    return L(L(cube))


def R(cube):
    """右の面 (R) を時計回りに90度。右から見て時計回り。"""
    return _turn(cube, "R")


def Ri(cube):
    """右の面 (R) を反時計回りに90度。"""
    return R(R(R(cube)))


def R2(cube):
    """右の面 (R) を180度。"""
    return R(R(cube))


def F(cube):
    """手前の面 (F) を時計回りに90度。"""
    return _turn(cube, "F")


def Fi(cube):
    """手前の面 (F) を反時計回りに90度。"""
    return F(F(F(cube)))


def F2(cube):
    """手前の面 (F) を180度。"""
    return F(F(cube))


def B(cube):
    """奥の面 (B) を時計回りに90度。奥から見て時計回り。"""
    return _turn(cube, "B")


def Bi(cube):
    """奥の面 (B) を反時計回りに90度。"""
    return B(B(B(cube)))


def B2(cube):
    """奥の面 (B) を180度。"""
    return B(B(cube))


# ----------------------------------------------------------------------
# 中段 (スライス) の操作
#
# 外側の面ではなく、まん中の層だけを回す。
#
#   M  L 面と R 面のあいだの層。L と同じ向きに回る (Middle)
#   E  U 面と D 面のあいだの層。D と同じ向きに回る (Equator)
#   S  F 面と B 面のあいだの層。F と同じ向きに回る (Standing)
#
# 中段には角の小立方体が無いので、この3つを回しても角は動かない。
# 中心のステッカーが動くので、回すと「面の色」がずれることがある。
# ----------------------------------------------------------------------

def M(cube):
    """まん中の縦の層 (M) を回す。L (左の面) と同じ向き。"""
    return _turn(cube, "M")


def Mi(cube):
    """まん中の縦の層 (M) を逆向きに回す。"""
    return M(M(M(cube)))


def M2(cube):
    """まん中の縦の層 (M) を180度。"""
    return M(M(cube))


def E(cube):
    """まん中の横の層 (E) を回す。D (下の面) と同じ向き。"""
    return _turn(cube, "E")


def Ei(cube):
    """まん中の横の層 (E) を逆向きに回す。"""
    return E(E(E(cube)))


def E2(cube):
    """まん中の横の層 (E) を180度。"""
    return E(E(cube))


def S(cube):
    """まん中の奥ゆきの層 (S) を回す。F (手前の面) と同じ向き。"""
    return _turn(cube, "S")


def Si(cube):
    """まん中の奥ゆきの層 (S) を逆向きに回す。"""
    return S(S(S(cube)))


def S2(cube):
    """まん中の奥ゆきの層 (S) を180度。"""
    return S(S(cube))


# ----------------------------------------------------------------------
# 操作を名前で引ける表。
#
# FACE_MOVES  外側の面を回す18通り。shuffle() はここからだけ選ぶ
# SLICE_MOVES 中段を回す9通り
# ALL_MOVES   合わせて27通り
# ----------------------------------------------------------------------

FACE_MOVES = {
    "U": U, "Ui": Ui, "U2": U2,
    "D": D, "Di": Di, "D2": D2,
    "L": L, "Li": Li, "L2": L2,
    "R": R, "Ri": Ri, "R2": R2,
    "F": F, "Fi": Fi, "F2": F2,
    "B": B, "Bi": Bi, "B2": B2,
}

SLICE_MOVES = {
    "M": M, "Mi": Mi, "M2": M2,
    "E": E, "Ei": Ei, "E2": E2,
    "S": S, "Si": Si, "S2": S2,
}

ALL_MOVES = {**FACE_MOVES, **SLICE_MOVES}

# 名前を書いた順に並べたもの。
MOVE_NAMES = list(ALL_MOVES)
FACE_MOVE_NAMES = list(FACE_MOVES)


# ----------------------------------------------------------------------
# 手順の文字列
#
# ルービックキューブの手順は、ふつう R U R' U' のように書く。
# ' (プライム) は Python の関数名に使えないので関数のほうは Ri としたが、
# 文字列でならそのまま書ける。本や Web の手順をそのまま貼れるようにしておく。
# ----------------------------------------------------------------------

# 面の文字のうしろに付けられる文字 -> 関数名につける文字
#   ' も i も反時計回り。2 は180度。
_SUFFIXES = {"'": "i", "i": "i", "2": "2"}


def parse(sequence):
    """手順の文字列を、操作の名前のリストに直す。

        parse("RUR'U'")     ->  ['R', 'U', 'Ri', 'Ui']
        parse("R U R' U'")  ->  ['R', 'U', 'Ri', 'Ui']
        parse("RUR2Ui")     ->  ['R', 'U', 'R2', 'Ui']
        parse("MES")        ->  ['M', 'E', 'S']       中段も書ける

    空白はあってもなくてもよい。反時計回りは ' でも i でも書ける。
    """
    assert isinstance(sequence, str), "手順は文字列で渡してください。"

    names = []
    i = 0
    while i < len(sequence):
        letter = sequence[i]

        if letter.isspace():
            i += 1
            continue

        assert letter in _SIDE_CYCLES, (
            f"手順の {i + 1} 文字目 {letter!r} が読めません。"
            "使えるのは U D L R F B (外側の面) と M E S (中段)、"
            "そのあとの ' か 2 です。"
        )

        # 面の文字のうしろに ' や 2 が続いていれば、それも取りこむ
        name = letter
        if i + 1 < len(sequence) and sequence[i + 1] in _SUFFIXES:
            name += _SUFFIXES[sequence[i + 1]]
            i += 1

        names.append(name)
        i += 1

    return names


def do(sequence, cube=None, times=1):
    """手順をまとめて実行した、新しいキューブを返す。

    cube を渡すとそのキューブから、渡さなければ完成状態から始める。
    times はくり返す回数。

        cube = do("RUR'U'", cube)
        cube = do("RUR'U'", cube, times=6)   # 6回くり返すと元に戻る

    これは中身のほうの関数で、いつでも新しいリストを返す。
    rubik.do() のほうは、キューブを省くと rubik.cube を回して何も返さない。
    """
    assert isinstance(times, int) and not isinstance(times, bool) and times >= 0, \
        "do の times は 0 以上の整数にしてください。"

    names = parse(sequence)

    if cube is None:
        cube = solved()
    else:
        check(cube)

    for _ in range(times):
        for name in names:
            cube = ALL_MOVES[name](cube)

    return cube


def shuffle(cube=None, times=20, seed=None):
    """でたらめに回して、ぐちゃぐちゃにしたキューブを返す。

    cube を渡すとそのキューブから、渡さなければ完成状態から回しはじめる。
    times は回す回数。seed に数を渡すと、毎回まったく同じ回しかたになる
    (授業で全員に同じ配置を配りたいときなどに使う)。

        cube = shuffle()             # 20手でぐちゃぐちゃに
        cube = shuffle(times=5)      # 5手だけ
        cube = shuffle(seed=42)      # 何度やっても同じ配置

    これは中身のほうの関数で、いつでも新しいリストを返す。
    rubik.shuffle() のほうは、キューブを省くと rubik.cube を差しかえて
    何も返さない。

    選ぶのは外側の面を回す18通りだけで、中段 (M E S) は混ぜない。
    中段を回すと中心のステッカーが動いて、面の色そのものがずれてしまうため。

    18通りの中からその都度1つを選ぶだけなので、R のすぐあとに Ri が来て
    打ち消しあうこともある。それでも times が20もあればじゅうぶん混ざる。
    """
    assert isinstance(times, int) and not isinstance(times, bool) and times >= 0, \
        "shuffle の times は 0 以上の整数にしてください。"

    if cube is None:
        cube = solved()
    else:
        check(cube)

    # seed をもとにサイコロを1つ用意する。seed が None なら毎回ちがう出目になる。
    dice = random.Random(seed)

    for _ in range(times):
        name = dice.choice(FACE_MOVE_NAMES)   # 中段は混ぜない
        cube = ALL_MOVES[name](cube)

    return cube
