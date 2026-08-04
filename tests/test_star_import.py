"""from rubik import * で使ったときに、ちゃんと動くか確かめるテスト。

    uv run python tests/test_star_import.py

rubik. を省いて書きたい人向けの使いかたを守るためのテスト。
とくに cube は、名前を取りこんだあとも同じキューブを指しつづける必要がある。
"""

import builtins
import copy

# 窓を開かないようにしてから、rubik を取りこむ
from rubik import viewer as _viewer
_viewer._default._attempted = True

import rubik                 # 見くらべ用
from rubik import *          # noqa: F403  これがこのファイルの主役


def test_everything_in_all_really_arrives():
    """__all__ に並べた名前が、ぜんぶ取りこまれている。"""
    here = globals()
    missing = [n for n in rubik.__all__ if n not in here]
    assert not missing, f"取りこまれていない名前がある: {missing}"


def test_no_builtin_is_hidden():
    """組み込みの名前を隠していない。

    たとえば list や open を上書きしてしまうと、
    from rubik import * と書いたとたんに他のコードが壊れる。
    """
    clash = sorted(set(rubik.__all__) & set(dir(builtins)))
    assert not clash, f"組み込みの名前とかぶっている: {clash}"


def test_cube_is_available():
    """cube という名前が取りこまれている。"""
    assert cube is rubik.cube                  # noqa: F405


def test_cube_stays_the_same_object():
    """操作しても、取りこんだ cube が取り残されない。

    ここがこのファイルの一番の目当て。
    rubik.cube を「入れ物ごと」取りかえてしまうと、先に取りこんだ名前は
    古い入れ物を指したままになり、いつまでも完成状態のように見えてしまう。
    """
    solved()                                   # noqa: F405
    assert cube is rubik.cube                  # noqa: F405

    for step in (R, U, Ri, Ui, M, E, S, D2, Bi):   # noqa: F405
        step()
        assert cube is rubik.cube, f"{step.__name__}() のあとで入れ物が変わった"
        assert cube == rubik.cube

    do("RUR'U'")                               # noqa: F405
    assert cube is rubik.cube, "do() のあとで入れ物が変わった"

    shuffle(seed=3)                            # noqa: F405
    assert cube is rubik.cube, "shuffle() のあとで入れ物が変わった"

    solved()                                   # noqa: F405
    assert cube is rubik.cube, "solved() のあとで入れ物が変わった"
    assert is_solved()                         # noqa: F405


def test_cube_shows_the_real_state():
    """取りこんだ cube を読むと、いまの状態がちゃんと出てくる。"""
    solved()                                   # noqa: F405
    before = copy.deepcopy(cube)               # noqa: F405

    R()                                        # noqa: F405
    assert cube != before, "回したのに cube が変わっていない"    # noqa: F405
    assert cube == rubik.moves.R(before)       # noqa: F405

    # 添字でも読める
    solved()                                   # noqa: F405
    R()                                        # noqa: F405
    assert cube[2][0] == ["G", "G", "Y"], cube[2][0]   # noqa: F405


def test_replacing_the_contents_keeps_the_link():
    """cube[:] = x なら、中身を丸ごと入れかえても取り残されない。"""
    target = rubik.moves.shuffle(times=6, seed=8)

    cube[:] = target                           # noqa: F405
    assert cube is rubik.cube                  # noqa: F405
    assert rubik.cube == target

    # そのあとの操作もふつうに続けられる
    R()                                        # noqa: F405
    assert cube is rubik.cube                  # noqa: F405
    assert rubik.cube == rubik.moves.R(target)


def test_all_27_moves_work():
    """27通りの操作がすべて呼べて、キューブが変わる。"""
    for name in rubik.MOVE_NAMES:
        solved()                               # noqa: F405
        globals()[name]()
        assert not is_solved(), f"{name}() でキューブが変わっていない"   # noqa: F405
        assert cube is rubik.cube, f"{name}() のあとで入れ物が変わった"  # noqa: F405


def test_the_other_functions_work():
    """残りの関数も rubik. なしで使える。"""
    import contextlib
    import io

    solved()                                   # noqa: F405
    assert is_solved()                         # noqa: F405
    assert parse("RUR'U'") == ["R", "U", "Ri", "Ui"]     # noqa: F405
    assert check(cube) is None                 # noqa: F405
    assert isinstance(net(cube), str)          # noqa: F405

    with contextlib.redirect_stdout(io.StringIO()) as printed:
        show()                                 # noqa: F405
    assert printed.getvalue().rstrip("\n") == net(cube)  # noqa: F405

    # キューブを渡す形も使える
    fresh = Cube().cube                        # noqa: F405
    assert R(fresh) == rubik.moves.R(fresh)    # noqa: F405
    assert isinstance(do("RU", fresh), list)   # noqa: F405
    assert isinstance(shuffle(fresh, times=2), list)     # noqa: F405


def test_classes_and_constants_work():
    """クラスと定数も取りこまれている。"""
    c = Cube()                                 # noqa: F405
    c.R()
    c.do("M2E'S")
    assert not c.is_solved()

    assert isinstance(Viewer(), rubik.Viewer)  # noqa: F405

    assert (UP, LEFT, FRONT, RIGHT, BACK, DOWN) == (0, 1, 2, 3, 4, 5)   # noqa: F405
    assert set(COLORS) == {"B", "Y", "R", "W", "G", "O"}                # noqa: F405
    assert FACE_NAMES[FRONT] == "F"            # noqa: F405
    assert len(ALL_MOVES) == 27                # noqa: F405
    assert len(FACE_MOVES) == 18               # noqa: F405
    assert len(SLICE_MOVES) == 9               # noqa: F405


def test_window_functions_are_callable():
    """窓むけの関数も呼べる。窓は開かない設定にしてあるので何も起きない。"""
    assert update() is None                    # noqa: F405
    assert reset_UFR() is None                 # noqa: F405
    assert reset_DBL() is None                 # noqa: F405
    assert wait() is None                      # noqa: F405
    assert close() is None                     # noqa: F405


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items())
             if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print(f"\n{len(tests)} 件すべて成功")
