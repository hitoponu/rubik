"""操作 (moves.py) が正しいか確かめるテスト。

    uv run python tests/test_moves.py

で実行できる。
"""

import copy

from rubik import cube as cube_mod
from rubik import moves
from rubik.geometry import cubie_position

ALL = ["U", "D", "L", "R", "F", "B"]


def turn(name):
    return getattr(moves, name)


def test_solved_shape():
    c = cube_mod.solved()
    cube_mod.check(c)
    assert len(c) == 6
    for face in c:
        assert len(face) == 3
        for row in face:
            assert len(row) == 3
    # 各色ちょうど9枚
    counts = {}
    for face in c:
        for row in face:
            for s in row:
                counts[s] = counts.get(s, 0) + 1
    assert counts == {"W": 9, "O": 9, "G": 9, "R": 9, "B": 9, "Y": 9}, counts


def test_assert_messages():
    for bad in ("リストではない", 123, None, {"a": 1}):
        try:
            moves.U(bad)
        except AssertionError as e:
            assert "リストで渡してください" in str(e), str(e)
        else:
            raise AssertionError(f"assert が出なかった: {bad!r}")

    bad_shapes = [
        [],                                   # 面が0枚
        [[[0] * 3] * 3] * 5,                  # 面が5枚
        [[[0] * 3] * 3] * 7,                  # 面が7枚
        [[[0] * 3] * 2] * 6,                  # 縦が2
        [[[0] * 4] * 3] * 6,                  # 横が4
        [[0, 0, 0]] * 6,                      # 入れ子が浅い
    ]
    for bad in bad_shapes:
        try:
            moves.U(bad)
        except AssertionError as e:
            assert "6x3x3" in str(e), str(e)
        else:
            raise AssertionError(f"assert が出なかった: {bad!r}")

    # 形は合っているが、中身が色になっていない
    for wrong in (0, "X", "WW", "", None, ["W"], "w"):
        c = cube_mod.solved()
        c[2][1][0] = wrong               # F面 の 縦1 横0 を壊す
        try:
            moves.U(c)
        except AssertionError as e:
            message = str(e)
            assert "どれかにしてください" in message, message
            assert "cube[2][1][0]" in message, message   # 場所を教えてくれる
            assert "F面" in message, message
            assert repr(wrong) in message, message       # 実際の値も教えてくれる
        else:
            raise AssertionError(f"assert が出なかった: {wrong!r}")

    # 6x3x3 だが全部が数字、というとき
    try:
        moves.U([[[0] * 3] * 3] * 6)
    except AssertionError as e:
        assert "どれかにしてください" in str(e), str(e)
    else:
        raise AssertionError("assert が出なかった")


def test_four_turns_is_identity():
    """どの操作も4回まわすと元に戻る。"""
    start = cube_mod.solved()
    for name in ALL:
        f = turn(name)
        c = start
        for _ in range(4):
            c = f(c)
        assert c == start, f"{name} を4回まわしても戻らない"


def test_inverse_and_double():
    """Xi は X の逆、X2 は X を2回。"""
    start = scrambled()
    for name in ALL:
        f, fi, f2 = turn(name), turn(name + "i"), turn(name + "2")
        assert fi(f(start)) == start, f"{name}i が {name} の逆になっていない"
        assert f(fi(start)) == start, f"{name} が {name}i の逆になっていない"
        assert f2(start) == f(f(start)), f"{name}2 が {name} 2回と違う"
        assert f2(f2(start)) == start, f"{name}2 を2回で戻らない"


def test_does_not_modify_input():
    """もらったキューブを書き換えない。"""
    start = cube_mod.solved()
    before = copy.deepcopy(start)
    for name in ALL:
        turn(name)(start)
        turn(name + "i")(start)
        turn(name + "2")(start)
    assert start == before, "入力のキューブが書き換えられている"


def test_opposite_face_untouched():
    """ある面を回しても、その裏の面は動かない。"""
    pairs = {"U": cube_mod.DOWN, "D": cube_mod.UP,
             "L": cube_mod.RIGHT, "R": cube_mod.LEFT,
             "F": cube_mod.BACK, "B": cube_mod.FRONT}
    start = scrambled()
    for name, opposite in pairs.items():
        after = turn(name)(start)
        assert after[opposite] == start[opposite], f"{name} が裏の面を動かしている"


def test_opposite_faces_commute():
    """裏どうしの面は、回す順番を入れかえても結果が同じ。"""
    start = scrambled()
    for a, b in (("U", "D"), ("L", "R"), ("F", "B")):
        fa, fb = turn(a), turn(b)
        assert fa(fb(start)) == fb(fa(start)), f"{a} と {b} が交換しない"


def test_U_from_solved():
    """完成状態から U を1回まわした結果を、手で書いた答えと比べる。"""
    after = moves.U(cube_mod.solved())
    # 上の段だけが動く。F の上段には、もとの R の上段 (赤) が来る。
    assert after[cube_mod.FRONT][0] == ["R", "R", "R"]
    assert after[cube_mod.LEFT][0] == ["G", "G", "G"]   # もとの F (緑)
    assert after[cube_mod.BACK][0] == ["O", "O", "O"]   # もとの L (橙)
    assert after[cube_mod.RIGHT][0] == ["B", "B", "B"]  # もとの B (青)
    # 中段と下段は動かない
    for face in (cube_mod.FRONT, cube_mod.LEFT, cube_mod.BACK, cube_mod.RIGHT):
        assert after[face][1] == cube_mod.solved()[face][1]
        assert after[face][2] == cube_mod.solved()[face][2]
    # U 面は白のまま、D 面もそのまま
    assert after[cube_mod.UP] == [["W"] * 3] * 3
    assert after[cube_mod.DOWN] == [["Y"] * 3] * 3


def test_cycle_tables():
    """操作の「巡回の表」そのものを調べる。

    1回まわして動くステッカーは、その面の8枚 (真ん中はその場) と、
    まわりの4面の3枚ずつ12枚の、あわせて20枚。
    表がこの20枚を、4枚ずつ5つの組にすきまなく・重なりなく分けていれば、
    ステッカーが消えたり増えたりすることはありえない。
    """
    from rubik.geometry import FACE_BASIS
    from rubik.moves import _SIDE_CYCLES, _TURNED_FACE, _face_cycles

    for name in ALL:
        turned = _TURNED_FACE[name]
        cycles = _face_cycles(turned) + _SIDE_CYCLES[name]
        assert len(cycles) == 5, name

        positions = []
        for cycle in cycles:
            assert len(cycle) == 4, (name, cycle)
            assert len(set(cycle)) == 4, f"{name} の組の中で席がぶつかっている"
            positions.extend(cycle)

        assert len(positions) == 20, name
        assert len(set(positions)) == 20, f"{name} の表で席がぶつかっている"

        # 動く20枚はすべて、回している層に乗っている。
        # 層は、その面が外を向いている方向 (法線) で決まる。
        normal = FACE_BASIS[turned][0]
        axis = [i for i in range(3) if normal[i] != 0][0]
        for face, row, col in positions:
            assert cubie_position(face, row, col)[axis] == normal[axis], \
                f"{name} が別の層のステッカーを動かしている: {(face, row, col)}"

        # 回している面そのものからは、真ん中をのぞく8枚
        own = [p for p in positions if p[0] == turned]
        assert len(own) == 8, name
        assert (turned, 1, 1) not in own, f"{name} が真ん中を動かしている"


def test_cubie_integrity():
    """小立方体としてのつじつまが合っているか。

    ばらばらに回しても、キューブは 8個の角 (色3つ)、12個の辺 (色2つ)、
    6個の中心 (色1つ) でできている。その色の組み合わせの顔ぶれは、
    完成状態のときと変わらないはず。
    """
    def cubies(c):
        table = {}
        for f in range(6):
            for r in range(3):
                for cc in range(3):
                    table.setdefault(cubie_position(f, r, cc), []).append(c[f][r][cc])
        return sorted(tuple(sorted(v)) for v in table.values())

    expected = cubies(cube_mod.solved())
    assert len(expected) == 26, len(expected)          # 中の見えない1個を除いて26個
    assert sum(1 for v in expected if len(v) == 3) == 8   # 角
    assert sum(1 for v in expected if len(v) == 2) == 12  # 辺
    assert sum(1 for v in expected if len(v) == 1) == 6   # 中心

    assert cubies(scrambled()) == expected, "ありえない小立方体ができている"


def test_move_table():
    """18通りの操作の表が、そろっていて中身も合っている。"""
    assert len(moves.ALL_MOVES) == 18
    assert len(moves.MOVE_NAMES) == 18
    assert set(moves.MOVE_NAMES) == set(moves.ALL_MOVES)
    for name in moves.MOVE_NAMES:
        assert moves.ALL_MOVES[name] is getattr(moves, name), name


def test_shuffle_makes_a_proper_cube():
    """shuffle が返すのは、ちゃんとしたキューブ。"""
    c = moves.shuffle()
    cube_mod.check(c)                       # 形も中身も正しい

    counts = {}
    for face in c:
        for row in face:
            for s in row:
                counts[s] = counts.get(s, 0) + 1
    assert counts == {"W": 9, "O": 9, "G": 9, "R": 9, "B": 9, "Y": 9}, counts


def test_shuffle_is_reachable():
    """shuffle の結果は、本物のキューブとしてありえる配置になっている。"""
    def cubies(c):
        table = {}
        for f in range(6):
            for r in range(3):
                for cc in range(3):
                    table.setdefault(cubie_position(f, r, cc), []).append(c[f][r][cc])
        return sorted(tuple(sorted(v)) for v in table.values())

    expected = cubies(cube_mod.solved())
    for seed in range(20):
        assert cubies(moves.shuffle(seed=seed)) == expected, seed


def test_shuffle_times():
    """times で回す回数が変わる。"""
    assert moves.shuffle(times=0) == cube_mod.solved()   # 0回なら完成状態のまま

    # 1回だけなら、18通りのどれか1手を回したものと一致する
    one = moves.shuffle(times=1, seed=7)
    candidates = [moves.ALL_MOVES[n](cube_mod.solved()) for n in moves.MOVE_NAMES]
    assert one in candidates

    # 20手も回せば、まず完成状態には戻らない
    for seed in range(20):
        assert moves.shuffle(seed=seed) != cube_mod.solved(), seed


def test_shuffle_seed():
    """seed が同じなら同じ結果、ちがえばちがう結果になる。"""
    assert moves.shuffle(seed=42) == moves.shuffle(seed=42)
    assert moves.shuffle(seed=42) == moves.shuffle(seed=42)   # 何度でも

    results = [moves.shuffle(seed=s) for s in range(10)]
    assert len(results) == len({str(r) for r in results}), "seed を変えても同じになる"

    # seed なしだと毎回ちがう (同じになる確率は無視できる)
    assert moves.shuffle() != moves.shuffle()


def test_shuffle_from_a_given_cube():
    """キューブを渡すと、そこから回しはじめる。もらったものは書きかえない。"""
    start = scrambled()
    before = copy.deepcopy(start)

    after = moves.shuffle(start, times=5, seed=1)
    assert start == before, "渡したキューブが書きかえられている"
    assert after != start

    # 同じ seed なら、同じ出発点から同じところへ着く
    assert moves.shuffle(start, times=5, seed=1) == after
    # 出発点がちがえば着く先もちがう
    assert moves.shuffle(cube_mod.solved(), times=5, seed=1) != after


def test_shuffle_rejects_bad_times():
    """times がおかしいときは日本語の assert で止まる。"""
    for bad in (-1, 2.5, "3", None, True):
        try:
            moves.shuffle(times=bad)
        except AssertionError as e:
            assert "0 以上の整数" in str(e), str(e)
        else:
            raise AssertionError(f"assert が出なかった: {bad!r}")


def test_shuffle_checks_the_given_cube():
    """渡されたキューブがおかしければ、いつもの assert が出る。"""
    try:
        moves.shuffle("リストじゃない")
    except AssertionError as e:
        assert "リストで渡してください" in str(e), str(e)
    else:
        raise AssertionError("assert が出なかった")


def order_of(sequence):
    """手順をくり返して完成状態に戻るまでの回数を数える。"""
    start = cube_mod.solved()
    c = start
    for n in range(1, 2000):
        for name in sequence:
            c = turn(name)(c)
        if c == start:
            return n
    raise AssertionError(f"{sequence} が戻らない")


def test_known_orders():
    """よく知られた「手順の周期」と合っているか。

    これが合えば、操作の実装はまず正しい。
    """
    assert order_of(["U"]) == 4
    assert order_of(["R", "U", "Ri", "Ui"]) == 6     # 通称「セクシームーブ」
    assert order_of(["R", "U"]) == 105
    assert order_of(["F", "R"]) == 105               # 隣り合う2面ならどれでも105
    assert order_of(["U", "F"]) == 105
    assert order_of(["R2", "U2"]) == 6
    # 裏どうしの面は互いに干渉しないので、周期は4のまま
    assert order_of(["R", "L"]) == 4
    assert order_of(["U", "Di"]) == 4


def scrambled():
    """決まった手順でぐちゃぐちゃにしたキューブ。テスト用。"""
    c = cube_mod.solved()
    for name in ("R", "U", "Fi", "L2", "B", "Di", "F2", "Ui", "R", "Bi",
                 "D", "L", "F", "U2", "Ri"):
        c = turn(name)(c)
    return c


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print(f"\n{len(tests)} 件すべて成功")
