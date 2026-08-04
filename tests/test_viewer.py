"""3Dグラフィクスまわりのテスト。

窓は開かずに (Agg という「絵をファイルに描くだけ」の方式で) 確かめる。

    uv run python tests/test_viewer.py
"""

import json

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

import rubik
from rubik import state
from rubik.geometry import FACE_BASIS, cubie_position, sticker_corners
from rubik._window import _STICKERS, _colors_of


def test_sticker_list():
    """54枚ぶん、重複なく並んでいる。"""
    assert len(_STICKERS) == 54
    assert len(set(_STICKERS)) == 54


def test_colors_follow_the_cube():
    """_colors_of がキューブの中身どおりの色を、正しい順番で返す。"""
    cube = state.solved()
    colors = _colors_of(cube)
    assert len(colors) == 54

    from rubik.geometry import COLOR_TO_RGB
    for i, (f, r, c) in enumerate(_STICKERS):
        assert colors[i] == COLOR_TO_RGB[cube[f][r][c]]

    # 回したあとも追随する
    moved = rubik.R(cube)
    moved_colors = _colors_of(moved)
    assert moved_colors != colors
    for i, (f, r, c) in enumerate(_STICKERS):
        assert moved_colors[i] == COLOR_TO_RGB[moved[f][r][c]]


def test_stickers_sit_on_the_cube_surface():
    """どのステッカーも、その面の表面 (中心から1.5) にぴったり乗っている。"""
    for face, row, col in _STICKERS:
        normal = FACE_BASIS[face][0]
        for corner in sticker_corners(face, row, col):
            # 法線方向の成分がちょうど 1.5 であればよい
            depth = sum(corner[i] * normal[i] for i in range(3))
            assert abs(depth - 1.5) < 1e-9, (face, row, col, depth)


def test_stickers_do_not_overlap():
    """ステッカー54枚の中心がすべてばらばらの位置にある。"""
    centers = set()
    for face, row, col in _STICKERS:
        corners = sticker_corners(face, row, col)
        center = tuple(
            round(sum(c[i] for c in corners) / 4, 6) for i in range(3)
        )
        centers.add(center)
    assert len(centers) == 54


def test_geometry_matches_faces():
    """ステッカーの位置が、その面の側にちゃんとある。

    たとえば R 面のステッカーは必ず x = +1 の小立方体に付いている。
    """
    expected_axis = {
        rubik.UP: (1, 1), rubik.DOWN: (1, -1),
        rubik.RIGHT: (0, 1), rubik.LEFT: (0, -1),
        rubik.FRONT: (2, 1), rubik.BACK: (2, -1),
    }
    for face, row, col in _STICKERS:
        axis, value = expected_axis[face]
        assert cubie_position(face, row, col)[axis] == value, (face, row, col)


def test_repaint_does_not_move_the_camera():
    """色を塗りかえても、見ている向きが変わらない。

    update() が姿勢を変えないことの根拠になる部分。
    利用者がマウスで動かした角度 (elev, azim) を真似して設定しておき、
    色を塗りかえて描きなおしても、その角度が保たれることを確かめる。
    """
    cube = state.solved()
    fig = plt.figure(figsize=(4, 4))
    ax = fig.add_subplot(projection="3d")
    stickers = Poly3DCollection(
        [sticker_corners(f, r, c) for f, r, c in _STICKERS],
        facecolors=_colors_of(cube),
        edgecolors="black",
    )
    ax.add_collection3d(stickers)
    ax.view_init(elev=22, azim=45, vertical_axis="y")
    fig.canvas.draw()

    # 利用者がマウスでぐるっと回したつもりになる
    ax.view_init(elev=-13, azim=137, vertical_axis="y")
    fig.canvas.draw()
    before = (ax.elev, ax.azim, ax.roll)

    # _window.py の poll() がやっているのと同じこと
    for _ in range(20):
        cube = rubik.R(cube)
        stickers.set_facecolor(_colors_of(cube))
        fig.canvas.draw()

    assert (ax.elev, ax.azim, ax.roll) == before, "色の塗りかえで向きが変わった"
    plt.close(fig)


def test_json_round_trip():
    """親から子へ送るときの形 (JSON 1行) で、中身が変わらない。"""
    cube = rubik.Fi(rubik.U(state.solved()))
    for message in ({"cube": cube}, {"view": "UFR"}, {"view": "DBL"}):
        line = json.dumps(message)
        assert "\n" not in line, "1行に収まらないと送れない"
        assert json.loads(line) == message


def test_importing_the_window_module_keeps_the_backend():
    """_window を読みこむだけでは、絵の描きかたが変わらない。

    描きかたを選びなおすのは main() の中だけ、という約束を守らせる。
    ここが崩れると、このファイルの他のテスト (窓を出さない Agg 方式で
    描いている) が動かなくなる。
    """
    assert matplotlib.get_backend().lower() == "agg", matplotlib.get_backend()


def test_child_survives_the_notebook_backend():
    """Jupyter Notebook から使っても、窓が落ちない。

    Jupyter は MPLBACKEND という環境変数に「窓を出さずにノートへ絵を貼る方式」
    を入れてくる。それが子プロセスに引きつがれると、plt.show() が何もせずに
    終わって窓が出ないまま消えてしまう。_window.py はそれを選びなおしている。

    このテストだけは、ほんの少しのあいだ本当に窓が開く。
    """
    import os
    import time

    from rubik import viewer

    # Jupyter が設定するのと同じ環境変数を用意して、その状態で窓を開いてみる。
    # ここで指している部品はこのテスト環境には入っていないので、
    # 引きついでしまうと子プロセスは起動の途中で落ちる。
    before = os.environ.get("MPLBACKEND")
    os.environ["MPLBACKEND"] = "module://matplotlib_inline.backend_inline"
    try:
        rubik.init()
        time.sleep(2.0)
        assert viewer._alive(), \
            "Jupyter の設定を引きついでしまい、窓が出ないまま終わっている"
    finally:
        rubik.close()
        if before is None:
            os.environ.pop("MPLBACKEND", None)
        else:
            os.environ["MPLBACKEND"] = before


def _visible_colors(view_name):
    """その向きから見たとき、画面に実際に出ている色の文字を集めて返す。

    完成状態のキューブを本当に描いてみて、点の色を数える。
    背景はキューブに使わない灰色にしておく (白い背景だと W と区別できない)。
    """
    import numpy as np

    from rubik.geometry import COLOR_TO_RGB, VIEWS

    background = (0.35, 0.35, 0.40)
    cube = state.solved()

    fig = plt.figure(figsize=(4, 4), dpi=80)
    fig.patch.set_facecolor(background)
    ax = fig.add_subplot(projection="3d")
    ax.patch.set_facecolor(background)   # 3D軸の下じきも白のままだと困る
    ax.add_collection3d(Poly3DCollection(
        [sticker_corners(f, r, c) for f, r, c in _STICKERS],
        facecolors=_colors_of(cube), edgecolors="black", linewidths=1.0,
    ))
    elev, azim = VIEWS[view_name]
    ax.view_init(elev=elev, azim=azim, vertical_axis="y")
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-2.2, 2.2)
    ax.set_zlim(-2.2, 2.2)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    fig.canvas.draw()

    pixels = np.asarray(fig.canvas.buffer_rgba())[:, :, :3].astype(int)
    plt.close(fig)

    counts = {}
    for letter, rgb in COLOR_TO_RGB.items():
        target = np.array([round(v * 255) for v in rgb])
        counts[letter] = int((np.abs(pixels - target).sum(axis=2) < 12).sum())
    return counts


def test_views_show_the_intended_faces():
    """2つの向きが、ねらいどおりの3面を見せている。

    絵を描いて点の色を数えるので、角度の当てずっぽうではなく本当に確かめられる。
    """
    expected = {
        "UFR": {"W", "G", "R"},   # 上=白 前=緑 右=赤
        "DBL": {"Y", "B", "O"},   # 下=黄 後=青 左=橙
    }
    for view_name, should_see in expected.items():
        counts = _visible_colors(view_name)
        hidden = set(counts) - should_see

        for letter in should_see:
            assert counts[letter] > 1000, \
                f"{view_name} で {letter} が見えていない: {counts}"
        for letter in hidden:
            assert counts[letter] < 100, \
                f"{view_name} で見えないはずの {letter} が見えている: {counts}"


def test_the_two_views_are_opposite():
    """2つの向きを合わせると、6面ぜんぶが見られる。"""
    seen = set()
    for view_name in ("UFR", "DBL"):
        counts = _visible_colors(view_name)
        seen |= {letter for letter, n in counts.items() if n > 1000}
    assert seen == set(rubik.COLORS), seen


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print(f"\n{len(tests)} 件すべて成功")
