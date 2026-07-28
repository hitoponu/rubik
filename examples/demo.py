"""rubik ライブラリの使いかたの見本。

    uv run python examples/demo.py

3Dの窓が開く。マウスでドラッグするとぐるぐる回せる。
回しているあいだも 0.7 秒ごとに1手ずつ進んでいくが、
見ている向きは変わらないことが確かめられる。
"""

import time

import rubik

# 完成状態から始める
cube = rubik.solved()

print("--- 完成状態 ---")
rubik.show(cube)

# 3Dの窓を開く
rubik.init(cube)

# 「セクシームーブ」と呼ばれる手順 R U R' U' をくり返す。
# 6回くり返すと完成状態に戻る、という性質がある。
sequence = [rubik.R, rubik.U, rubik.Ri, rubik.Ui]

for lap in range(6):
    for turn in sequence:
        cube = turn(cube)      # 操作後のキューブが返ってくる
        rubik.update(cube)     # 窓に映すものを差しかえる
        time.sleep(0.7)
    print(f"{lap + 1} 周目おわり")

print("\n--- R U R' U' を6回くり返したあと ---")
rubik.show(cube)
print("\n完成状態に戻った:", cube == rubik.solved())

# マウスで回しすぎて分からなくなったら、決まった向きに戻せる。
print("\n裏がわ (D,B,L) を見せます")
rubik.reset_DBL()
time.sleep(2.0)

print("最初の向き (U,F,R) に戻します")
rubik.reset_UFR()

# 窓が閉じられるまで待つ。
# これが無いと、プログラムの終わりと同時に窓も消えてしまう。
rubik.wait()
