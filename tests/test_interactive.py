"""対話的な使いかた (rubik.R() や rubik.Cube) を確かめるテスト。

    uv run python tests/test_interactive.py

窓は開かない。rubik.R() はふつう窓を開こうとするが、
「ひとりでに開こうとするのは1回きり」という印を先に立てておく
(viewer._default._attempted = True) ので、テスト中に窓は出ない。
"""

import copy

import rubik
from rubik import moves, state, viewer

# テスト中に3Dの窓が開かないようにする
viewer._default._attempted = True


ALL = ["U", "D", "L", "R", "F", "B"]


# ----------------------------------------------------------------------
# 手順の文字列
# ----------------------------------------------------------------------

def test_parse():
    """手順の文字列を操作の名前に直せる。空白はあってもなくてもよい。"""
    expected = ["R", "U", "Ri", "Ui"]
    assert moves.parse("RUR'U'") == expected
    assert moves.parse("R U R' U'") == expected
    assert moves.parse("  R U  R'  U' ") == expected
    assert moves.parse("RURiUi") == expected          # i でも書ける

    assert moves.parse("RUR2Ui") == ["R", "U", "R2", "Ui"]
    assert moves.parse("R") == ["R"]
    assert moves.parse("") == []
    assert moves.parse("   ") == []

    # 18通りすべてが読める
    for name in moves.MOVE_NAMES:
        assert moves.parse(name) == [name], name
        # Xi は X' と書いても同じ
        if name.endswith("i"):
            assert moves.parse(name[0] + "'") == [name], name


def test_parse_errors():
    """読めない手順は、何文字目が悪いのかまで教えてくれる。"""
    for bad, position, letter in [("X", 1, "X"), ("RUX'", 3, "X"), ("R U ?", 5, "?")]:
        try:
            moves.parse(bad)
        except AssertionError as e:
            message = str(e)
            assert f"{position} 文字目" in message, message
            assert repr(letter) in message, message
            assert "U D L R F B" in message, message
        else:
            raise AssertionError(f"assert が出なかった: {bad!r}")

    for bad in (123, None, ["R"]):
        try:
            moves.parse(bad)
        except AssertionError as e:
            assert "文字列で渡してください" in str(e), str(e)
        else:
            raise AssertionError(f"assert が出なかった: {bad!r}")


def test_do_is_the_same_as_one_by_one():
    """do() でまとめて回すのと、1手ずつ回すのは同じ結果になる。"""
    start = state.solved()

    one_by_one = start
    for name in ["R", "U", "Ri", "Ui"]:
        one_by_one = moves.ALL_MOVES[name](one_by_one)

    assert moves.do("RUR'U'", start) == one_by_one
    assert start == state.solved(), "渡したキューブが書きかわっている"


def test_do_times():
    """times でくり返せる。R U R' U' は6回で元に戻る。"""
    start = state.solved()
    assert moves.do("RUR'U'", start, times=0) == start
    assert moves.do("RUR'U'", start, times=6) == start
    assert moves.do("RUR'U'", start, times=3) != start

    for bad in (-1, 2.5, "3", None, True):
        try:
            moves.do("R", start, times=bad)
        except AssertionError as e:
            assert "0 以上の整数" in str(e), str(e)
        else:
            raise AssertionError(f"assert が出なかった: {bad!r}")


# ----------------------------------------------------------------------
# cube() (rubik が持っている1つのキューブ)
# ----------------------------------------------------------------------

def test_module_functions_exist():
    """18通りの操作がモジュールの関数としてそろっている。"""
    for name in moves.MOVE_NAMES:
        assert name in rubik.__all__, name
        assert callable(getattr(rubik, name)), name
        assert getattr(rubik, name).__name__ == name, name


def test_no_argument_moves_the_module_cube():
    """引数を省くと、いまのキューブが進む。"""
    rubik.cube(state.solved())
    rubik.R()
    assert rubik.cube() == moves.R(state.solved())

    rubik.U()
    assert rubik.cube() == moves.U(moves.R(state.solved()))

    # 値は返さない
    assert rubik.Ui() is None
    assert rubik.cube() == moves.Ui(moves.U(moves.R(state.solved())))


def test_argument_form_stays_pure():
    """キューブを渡したときは、いまのキューブを触らない。"""
    rubik.cube(moves.shuffle(times=7, seed=3))
    snapshot = copy.deepcopy(rubik.cube())

    other = state.solved()
    rubik.R(other)
    rubik.Ui(other)
    rubik.B2(other)
    rubik.do("RUR'U'", other, times=2)
    rubik.shuffle(other, times=5)

    assert rubik.cube() == snapshot, "いまのキューブが書きかわっている"
    assert other == state.solved(), "渡したキューブが書きかわっている"


def test_module_do():
    """rubik.do() はいまのキューブを進める。"""
    rubik.cube(state.solved())
    rubik.do("RUR'U'", times=6)
    assert rubik.cube() == state.solved(), "6回くり返しても戻らない"

    rubik.do("RUR'U'")
    assert rubik.cube() != state.solved()


def test_solved_and_shuffle_set_the_module_cube():
    """solved() と shuffle() はいまのキューブを差しかえる。"""
    rubik.cube(moves.shuffle(times=5, seed=1))
    assert rubik.solved() is None
    assert rubik.cube() == state.solved()

    assert rubik.shuffle(seed=42) is None
    got = copy.deepcopy(rubik.cube())
    assert got != state.solved()
    # seed が同じなら何度でも同じ配置
    rubik.shuffle(seed=42)
    assert rubik.cube() == got


def test_cube_gets_and_sets():
    """cube() は取り出しと差しかえの両方をする。

    引数なしなら、いまのキューブを返す。
    キューブを渡すと、そちらに差しかえて何も返さない。
    """
    # 取り出す
    rubik.solved()
    assert rubik.cube() == state.solved()

    # 差しかえる。値は返さない
    target = moves.shuffle(times=6, seed=8)
    assert rubik.cube(target) is None
    assert rubik.cube() == target

    # 差しかえたあとも、ふつうに回せる
    rubik.R()
    assert rubik.cube() == moves.R(target)

    # 返ってくるのは中身そのものなので、書きかえると状態が変わる
    rubik.solved()
    rubik.cube()[2][0][0] = "R"
    assert rubik.cube()[2][0][0] == "R"
    assert not rubik.is_solved()
    rubik.solved()


def test_cube_survives_being_imported():
    """cube を名前で取りこんでも、いつでもいまの状態が返る。

    変数ではなく関数にしてあるのは、これができるようにするため。
    詳しくは tests/test_star_import.py。
    """
    from rubik import cube          # from rubik import * と同じこと

    rubik.solved()
    assert cube() == state.solved()

    rubik.R()
    assert cube() == rubik.cube(), "取りこんだ cube() が古い状態を返している"
    assert cube() == moves.R(state.solved())


def test_list_view_is_off_by_default():
    """窓の下のリスト表現は、ふつう出さない。"""
    from rubik.viewer import Viewer

    assert Viewer().list_view() is False, "作ったばかりの窓で表示になっている"
    assert rubik.Cube().list_view() is False
    assert rubik.list_view() is False


def test_list_view_switches():
    """list_view() は取り出しと切りかえの両方をする。"""
    from rubik.viewer import Viewer

    v = Viewer()
    assert v.list_view(True) is None       # 設定したときは値を返さない
    assert v.list_view() is True
    v.list_view(False)
    assert v.list_view() is False

    # 1 や 0 のような値でも True / False になる
    v.list_view(1)
    assert v.list_view() is True
    v.list_view(0)
    assert v.list_view() is False


def test_cube_remembers_list_view_until_the_window_opens():
    """窓を持たない Cube でも、設定は覚えておける。"""
    c = rubik.Cube()
    assert c._viewer is None
    c.list_view(True)
    assert c.list_view() is True, "窓が無いと設定が消えてしまう"
    assert c._viewer is None, "設定しただけで窓が開いてしまっている"


def test_state_changing_calls_return_nothing():
    """状態を変える呼び出しは、そろって何も返さない。

    Jupyter Notebook はセルの最後に書いた式の値を画面に出すので、
    ここで値を返すと 6x3x3 のリストがだらだら表示されてしまう。
    """
    import contextlib
    import io

    rubik.cube(state.solved())
    c = rubik.Cube()

    with contextlib.redirect_stdout(io.StringIO()):   # show() の表示は捨てる
        # モジュールの18通り
        for name in moves.MOVE_NAMES:
            assert getattr(rubik, name)() is None, f"rubik.{name}() が値を返している"

        # モジュールのその他
        assert rubik.do("RUR'U'") is None
        assert rubik.solved() is None
        assert rubik.shuffle(seed=1) is None
        assert rubik.show() is None
        assert rubik.update() is None
        assert rubik.reset_UFR() is None
        assert rubik.reset_DBL() is None
        assert rubik.close() is None

        # Cube のメソッド
        for name in moves.MOVE_NAMES:
            assert getattr(c, name)() is None, f"Cube.{name}() が値を返している"

        assert c.do("RUR'U'") is None
        assert c.solved() is None
        assert c.shuffle(seed=1) is None
        assert c.cube(state.solved()) is None
        assert c.show() is None
        assert c.update() is None
        assert c.reset_UFR() is None
        assert c.reset_DBL() is None
        assert c.wait() is None
        assert c.close() is None


def test_value_returning_calls_still_return():
    """値を取り出すための呼び出しは、これまでどおり値を返す。

    キューブを渡した形は「新しいリストを受け取る」のが目的なので、
    そこは変えない。
    """
    before = state.solved()

    for name in moves.MOVE_NAMES:
        got = getattr(rubik, name)(before)
        assert isinstance(got, list), f"rubik.{name}(cube) が値を返していない"
        rubik.check(got)

    assert isinstance(rubik.do("RUR'U'", before), list)
    assert isinstance(rubik.shuffle(before, times=3), list)

    # 調べるだけの関数
    assert rubik.is_solved(before) is True
    assert isinstance(rubik.net(before), str)
    assert isinstance(rubik.parse("RUR'U'"), list)
    assert isinstance(rubik.Cube().is_solved(), bool)
    assert isinstance(repr(rubik.Cube()), str)


def test_is_solved():
    """is_solved() は状態を変えずに、完成しているかだけを見る。

    solved() のほうはいまのキューブを完成状態にしてしまうので、
    「戻ったか」を調べるのに使うと、いつでも True になってしまう。
    """
    rubik.cube(state.solved())
    assert rubik.is_solved()

    rubik.cube(moves.shuffle(times=5, seed=4))
    snapshot = copy.deepcopy(rubik.cube())
    assert not rubik.is_solved()
    assert rubik.cube() == snapshot, "is_solved() が状態を変えている"

    # 引数を渡せばそちらを見る。いまのキューブは触らない
    assert rubik.is_solved(state.solved())
    assert rubik.cube() == snapshot

    # do() で戻したあとを、正しく判定できる
    rubik.cube(state.solved())
    rubik.do("RUR'U'", times=6)
    assert rubik.is_solved()
    rubik.do("RUR'U'")
    assert not rubik.is_solved()


def test_show_uses_the_module_cube():
    """引数を省いた show() は、いまのキューブを表示する。"""
    import contextlib
    import io

    rubik.cube(moves.shuffle(times=4, seed=2))

    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        rubik.show()
    assert printed.getvalue().rstrip("\n") == state.net(rubik.cube())

    # 引数を渡せば、そちらを表示する
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        rubik.show(state.solved())
    assert printed.getvalue().rstrip("\n") == state.net(state.solved())


# ----------------------------------------------------------------------
# Cube クラス
# ----------------------------------------------------------------------

def test_cube_starts_solved():
    c = rubik.Cube()
    assert c.cube() == state.solved()
    assert c.is_solved()


def test_cube_has_all_moves():
    """18通りの操作がメソッドとしてそろっている。"""
    c = rubik.Cube()
    for name in moves.MOVE_NAMES:
        assert hasattr(c, name), name
        assert callable(getattr(c, name)), name


def test_cube_moves_change_itself():
    """メソッドを呼ぶと、そのキューブ自身が変わる。"""
    c = rubik.Cube()
    assert c.R() is None
    assert c.cube() == moves.R(state.solved())

    c.do("RUR'U'", times=6)
    assert c.cube() == moves.R(state.solved()), "do のあと状態がずれている"


def test_cubes_are_independent():
    """Cube を2つ作ると、互いに影響しない。"""
    a = rubik.Cube()
    b = rubik.Cube()
    a.do("RUR'U'")
    assert b.is_solved(), "もう一方まで変わっている"
    assert a.cube() != b.cube


def test_cube_does_not_share_the_given_list():
    """渡したリストは写しを取る。あとから書きかえても影響しない。"""
    start = state.solved()
    c = rubik.Cube(start)

    # 渡した側を書きかえても、Cube は影響を受けない
    start[0][0][0] = "R"
    assert c.cube()[0][0][0] == "W", "渡したリストをそのまま抱えている"

    # 逆に Cube を回しても、渡した側は変わらない
    before = copy.deepcopy(start)
    c.R()
    c.do("RUR'U'")
    assert start == before, "Cube の操作が、渡したリストにまで及んでいる"


def test_cube_solved_and_shuffle():
    c = rubik.Cube()
    c.shuffle(seed=7)
    assert not c.is_solved()

    other = rubik.Cube()
    other.shuffle(seed=7)
    assert other.cube() == c.cube(), "seed が同じなら同じ配置になるはず"

    c.solved()
    assert c.is_solved()


def test_cube_set():
    c = rubik.Cube()
    target = moves.shuffle(times=6, seed=5)
    assert c.cube(target) is None
    assert c.cube() == target
    target[1][1][1] = "R"
    assert c.cube()[1][1][1] != "R", "渡したリストをそのまま抱えている"


def test_cube_repr_is_the_net():
    """Jupyter でセルに c と書くと展開図が出る。"""
    c = rubik.Cube()
    assert repr(c) == state.net(c.cube())
    c.R()
    assert repr(c) == state.net(c.cube())


def test_cube_without_3d_has_no_process():
    """show3d を指定しなければ、子プロセスは立ち上がらない。"""
    c = rubik.Cube()
    assert c._viewer is None
    c.R()
    c.do("RUR'U'")
    c.shuffle(seed=1)
    assert c._viewer is None, "窓を持たないはずが持っている"

    # 窓むけのメソッドを呼んでも、何も起きずに素通りする
    c.update()
    c.reset_UFR()
    c.reset_DBL()
    c.wait()
    c.close()
    assert c._viewer is None


def test_cube_rejects_bad_input():
    for bad in ("リストではない", [[[0] * 3] * 3] * 6):
        try:
            rubik.Cube(bad)
        except AssertionError:
            pass
        else:
            raise AssertionError(f"assert が出なかった: {bad!r}")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print(f"\n{len(tests)} 件すべて成功")
