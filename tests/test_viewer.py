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
        child = viewer._default._process

        # しばらく生きていれば窓は出ている。
        # 設定を引きついでしまった場合は、1秒とたたずに終わってしまう。
        for _ in range(6):
            time.sleep(0.5)
            if child.poll() is not None:
                break

        assert child.poll() is None, (
            "Jupyter の設定を引きついでしまい、窓が出ないまま終わっている "
            f"(子プロセスの終了コード {child.poll()})"
        )
    finally:
        rubik.close()
        if before is None:
            os.environ.pop("MPLBACKEND", None)
        else:
            os.environ["MPLBACKEND"] = before


# ----------------------------------------------------------------------
# 窓の右がわのリスト表現パネル
# ----------------------------------------------------------------------

def _new_panel():
    """パネルを1つ作って、升と文字と、それを載せた図を返す。"""
    from rubik._window import _build_list_panel

    fig = plt.figure(figsize=(4, 6))
    ax = fig.add_subplot()
    boxes, letters = _build_list_panel(ax, None)
    return fig, boxes, letters


def test_panel_has_one_box_per_sticker():
    """升は54個で、_STICKERS と同じ順に並んでいる。"""
    fig, boxes, letters = _new_panel()
    assert len(boxes) == 54
    assert len(letters) == 54
    plt.close(fig)


def test_panel_follows_the_cube():
    """升の色と文字が、キューブの中身どおりになる。"""
    from rubik._window import _paint_list_panel
    from rubik.geometry import COLOR_TO_RGB

    fig, boxes, letters = _new_panel()
    cube = rubik.M(rubik.do("RUR'U'", state.solved()))
    _paint_list_panel(boxes, letters, cube)

    for i, (f, r, c) in enumerate(_STICKERS):
        want = cube[f][r][c]
        assert letters[i].get_text() == want, (f, r, c)
        assert boxes[i].get_facecolor()[:3] == COLOR_TO_RGB[want], (f, r, c)

    plt.close(fig)


def test_panel_lays_out_3x3_as_3x3():
    """1つの面の中では、縦横の添字がそのまま升目の位置になる。

    col が増えると右へ、row が増えると下へ。展開図のような
    面ごとの向きの入れかえをしない、というのがこのパネルの約束。
    """
    fig, boxes, _ = _new_panel()
    at = {s: boxes[i].get_xy() for i, s in enumerate(_STICKERS)}

    for face in range(6):
        for row in range(3):
            for col in range(2):
                left = at[(face, row, col)]
                right = at[(face, row, col + 1)]
                assert right[0] > left[0], f"{face}面 col が右に伸びていない"
                assert right[1] == left[1], f"{face}面 同じ段が同じ高さでない"

        for col in range(3):
            for row in range(2):
                upper = at[(face, row, col)]
                lower = at[(face, row + 1, col)]
                assert lower[1] < upper[1], f"{face}面 row が下に伸びていない"
                assert lower[0] == upper[0], f"{face}面 同じ列が同じ横位置でない"

    plt.close(fig)


def test_panel_puts_the_faces_in_order():
    """6面が 0 から順に、左上から2列ずつ並ぶ。"""
    from rubik._window import _PANEL_COLS

    fig, boxes, _ = _new_panel()
    corner = {f: boxes[_STICKERS.index((f, 0, 0))].get_xy() for f in range(6)}

    for face in range(6):
        grid_row, grid_col = divmod(face, _PANEL_COLS)
        # 同じ段の面は同じ高さ、右の面ほど x が大きい
        for other in range(6):
            o_row, o_col = divmod(other, _PANEL_COLS)
            if o_row == grid_row and o_col > grid_col:
                assert corner[other][0] > corner[face][0], (face, other)
            if o_col == grid_col and o_row > grid_row:
                assert corner[other][1] < corner[face][1], (face, other)

    plt.close(fig)


def test_ink_is_readable():
    """明るい色には黒、暗い色には白の字を選ぶ。"""
    from rubik._window import _ink_for
    from rubik.geometry import COLOR_TO_RGB

    assert _ink_for(COLOR_TO_RGB["W"]) == "black"   # 白
    assert _ink_for(COLOR_TO_RGB["Y"]) == "black"   # 黄
    assert _ink_for(COLOR_TO_RGB["O"]) == "black"   # 橙
    assert _ink_for(COLOR_TO_RGB["G"]) == "white"   # 緑
    assert _ink_for(COLOR_TO_RGB["B"]) == "white"   # 青
    assert _ink_for(COLOR_TO_RGB["R"]) == "white"   # 赤


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
