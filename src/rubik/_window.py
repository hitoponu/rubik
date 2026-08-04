"""3Dグラフィクスの窓そのもの。別プロセスとして動く。

窓は左右に分かれていて、左が 3D のキューブ、右がリスト表現の升目。

    python -m rubik._window

親プロセス (viewer.py) が標準入力に1行ずつ JSON を流してきて、
このプログラムがそれを受け取って絵を描きかえる。直接使うことはない。

なぜ別プロセスにするのか
------------------------

macOS では、窓を持つプログラムは「メインの流れ」を窓の番人にずっと明け渡して
おかないと、マウスを受けつけてくれない。しかし利用者のプログラムは自分の
メインの流れで計算をしたいので、同じプロセスの中では両立しない。
そこで窓だけを別のプロセスに追い出した。こうすると、

  * 窓はいつでもぬるぬる動く (自分のメインの流れを持っているので)
  * 利用者のプログラムは update() を呼んだあとすぐ次の行に進める
  * update() は色を塗りかえるだけなので、見ている向きは絶対に変わらない

という3つが同時に成り立つ。
"""

import json
import queue
import sys
import threading

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .geometry import COLOR_TO_RGB, VIEWS, sticker_corners
from .state import FACE_NAMES

# 親から届いた指示を置いておく場所。
# 標準入力を読む係と、絵を描く係の受けわたしに使う。
#
# 指示は次の2種類。どちらも JSON の辞書1個で、1行に1つ届く。
#
#   {"cube": [...]}    映すキューブを差しかえる
#   {"view": "UFR"}    見る向きを決まった角度に戻す
_inbox = queue.Queue()

# 親との連絡が切れたことを知らせる合図
_CLOSED = "__closed__"

# ステッカーを並べる順番。色を塗りかえるときも必ずこの順で並べる。
_STICKERS = [(f, r, c) for f in range(6) for r in range(3) for c in range(3)]


def _read_stdin():
    """親から届く JSON を、ひたすら読んで _inbox に入れる係。"""
    for line in sys.stdin:
        line = line.strip()
        if line:
            _inbox.put(json.loads(line))
    # 親が終わった (パイプが閉じた)
    _inbox.put(_CLOSED)


def _use_window_backend():
    """絵の描きかたを「別の窓を出す方式」に切りかえる。うまくいけばその名前を返す。

    matplotlib には絵の出しかたが何通りかあり、環境変数 MPLBACKEND などで
    決まる。ここで選びなおすのには理由がある。

    Jupyter Notebook から使うと、ノートを動かしている側が
    MPLBACKEND に「窓を出さずにノートへ絵を貼る方式」を設定していて、
    それがこの子プロセスにも引きつがれてしまう。そのままだと
    plt.show() が何もせずに終わり、窓が出ないまま子プロセスが消える。

    そこで、窓を出せる方式を順に試して、最初に使えたものを採用する。
    """
    for name in ("macosx", "tkagg", "qtagg"):
        try:
            plt.switch_backend(name)
            return name
        except Exception:
            continue        # この方式は使えない。次を試す
    return None


def _japanese_font():
    """日本語が出せるフォントを探す。見つからなければ None。

    matplotlib がふつうに使うフォントには日本語が入っていないので、
    そのまま日本語を描くと文字が全部四角 (豆腐) になってしまう。
    """
    from matplotlib import font_manager

    candidates = [
        "Hiragino Sans",            # macOS
        "Hiragino Maru Gothic Pro",
        "Yu Gothic",                # Windows
        "MS Gothic",
        "Noto Sans CJK JP",         # Linux
        "IPAexGothic",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            return name
    return None


def _colors_of(cube):
    """キューブから、ステッカー54枚ぶんの色を _STICKERS の順に並べて返す。"""
    colors = []
    for face, row, col in _STICKERS:
        colors.append(COLOR_TO_RGB.get(cube[face][row][col], (0.5, 0.5, 0.5)))
    return colors


def _ink_for(rgb):
    """その色の上に字を書くとき、黒と白のどちらが読みやすいかを返す。"""
    brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return "black" if brightness > 0.5 else "white"


# リスト表現のパネルの寸法。1マス = 1 として数える。
_CELL = 1.0
_GAP_X = 1.1          # 面と面の横のすきま
_GAP_Y = 1.4          # 縦のすきま (面の名前を書くぶん広め)
_PANEL_COLS = 2       # 横に2面ずつ並べる。0,1 / 2,3 / 4,5 の順


def _build_list_panel(ax, font):
    """リスト表現を升目で描く。

    展開図ではなく、面を 0 から順に並べる。3x3 はそのまま 3x3 なので、

        cube[面][縦][横]

    の添字が、そのまま升目の位置になる。画面と添字を見くらべやすい。

    あとから色と文字を差しかえられるように、升と文字を _STICKERS と
    同じ順に並べて返す。
    """
    boxes, letters = [], []

    for face in range(6):
        grid_row, grid_col = divmod(face, _PANEL_COLS)
        x0 = grid_col * (3 * _CELL + _GAP_X)
        y0 = -grid_row * (3 * _CELL + _GAP_Y)

        # 面の見出し (0 U など)
        ax.text(x0 + 1.5 * _CELL, y0 + 0.3, f"{face}   {FACE_NAMES[face]}",
                ha="center", va="bottom", fontsize=12, color="0.35",
                **({"fontname": font} if font else {}))

        for row in range(3):
            for col in range(3):
                x = x0 + col * _CELL
                y = y0 - (row + 1) * _CELL
                box = Rectangle((x, y), _CELL, _CELL,
                                edgecolor="0.25", linewidth=1.0)
                ax.add_patch(box)
                letter = ax.text(x + _CELL / 2, y + _CELL / 2, "",
                                 ha="center", va="center", fontsize=11)
                boxes.append(box)
                letters.append(letter)

    width = _PANEL_COLS * 3 * _CELL + (_PANEL_COLS - 1) * _GAP_X
    height = 3 * (3 * _CELL) + 2 * _GAP_Y

    ax.set_xlim(-0.4, width + 0.4)
    ax.set_ylim(-height - 0.4, 1.1)
    ax.set_aspect("equal")
    ax.set_axis_off()

    return boxes, letters


def _paint_list_panel(boxes, letters, cube):
    """リスト表現のパネルを、いまのキューブの色と文字に塗りかえる。"""
    for i, (face, row, col) in enumerate(_STICKERS):
        letter = cube[face][row][col]
        rgb = COLOR_TO_RGB.get(letter, (0.5, 0.5, 0.5))
        boxes[i].set_facecolor(rgb)
        letters[i].set_text(letter)
        letters[i].set_color(_ink_for(rgb))


def main():
    # まず、窓を出せる描きかたを確保する。これができないと何も始まらない。
    if _use_window_backend() is None:
        print(
            "3Dの窓を出せませんでした。画面のない場所 (Google Colab などの"
            "クラウド上のノートブックや、画面なしのサーバ) では窓を開けません。"
            "手もとの Python か Jupyter Notebook で試してください。",
            file=sys.stderr,
        )
        return

    # 最初の1つが届くまで待つ。これが最初に映るキューブになる。
    threading.Thread(target=_read_stdin, daemon=True).start()
    first = _inbox.get()
    if first is _CLOSED:
        return

    font = _japanese_font()

    # 左に 3D、右にリスト表現を並べる。
    fig = plt.figure("ルービックキューブ", figsize=(10, 6.5))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.2, 1], wspace=0.0)
    ax = fig.add_subplot(grid[0], projection="3d")
    list_ax = fig.add_subplot(grid[1])

    boxes, letters = _build_list_panel(list_ax, font)
    _paint_list_panel(boxes, letters, first["cube"])

    # 54枚のステッカーを、四角形の集まりとして1回だけ作る。
    # あとはこの入れ物の色を塗りかえるだけにする。
    quads = [sticker_corners(f, r, c) for f, r, c in _STICKERS]
    stickers = Poly3DCollection(
        quads,
        facecolors=_colors_of(first["cube"]),
        edgecolors="black",
        linewidths=1.2,
    )
    ax.add_collection3d(stickers)

    def look(name):
        """決まった向きからキューブを見る。

        y 軸 (U 面の側) を画面の上にしておく。
        これを呼ぶのは、最初の1回と、リセットを頼まれたときだけ。
        """
        elev, azim = VIEWS[name]
        ax.view_init(elev=elev, azim=azim, vertical_axis="y")

    # 最初は U 面・F 面・R 面の3つが見える向きから始める。
    # ここから先の向きの変更はマウスにまかせ、プログラムからは触らない。
    look("UFR")

    # 見た目の調整。目盛りや枠は消して、キューブだけが浮かぶようにする。
    ax.set_xlim(-1.85, 1.85)
    ax.set_ylim(-1.85, 1.85)
    ax.set_zlim(-1.85, 1.85)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()
    fig.subplots_adjust(left=0.0, right=0.98, bottom=0.04, top=1.0)

    # 3D のほうの下に、操作の案内を出す
    caption = "ドラッグで回せます" if font else "drag to rotate"
    ax.text2D(0.5, 0.02, caption, transform=ax.transAxes,
              ha="center", fontsize=10, color="gray",
              **({"fontname": font} if font else {}))

    def poll(*_args):
        """ときどき呼ばれて、親から指示が届いていないか確かめる係。

        キューブの差しかえでやるのは色の塗りかえだけで、カメラの向き
        (ax.elev, ax.azim) には触らない。だから update() をいくら呼んでも
        見ている向きはそのまま保たれる。
        向きが動くのは、リセットを頼まれたときだけ。
        """
        new_cube = None
        new_view = None

        # 溜まっているぶんをぜんぶ取り出す。
        # 同じ種類が何度も来ていたら、最後のものだけが効く。
        while True:
            try:
                item = _inbox.get_nowait()
            except queue.Empty:
                break
            if item is _CLOSED:
                plt.close(fig)
                return
            if "cube" in item:
                new_cube = item["cube"]
            if "view" in item:
                new_view = item["view"]

        if new_cube is not None:
            stickers.set_facecolor(_colors_of(new_cube))
            _paint_list_panel(boxes, letters, new_cube)
        if new_view is not None:
            look(new_view)

        if new_cube is not None or new_view is not None:
            fig.canvas.draw_idle()

    timer = fig.canvas.new_timer(interval=50)
    timer.add_callback(poll)
    timer.start()

    plt.show()   # 窓が閉じられるまでここで待つ


if __name__ == "__main__":
    main()
