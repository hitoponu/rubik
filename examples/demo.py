"""rubik ライブラリの使いかたの見本。

    uv run python examples/demo.py

3Dの窓が開く。マウスでドラッグするとぐるぐる回せる。
回しているあいだも 0.7 秒ごとに1手ずつ進んでいくが、
見ている向きは変わらないことが確かめられる。
"""

import time

import rubik

print("--- 完成状態 ---")
rubik.show()                    # 引数を省くと rubik.cube を表示する

# 「セクシームーブ」と呼ばれる手順 R U R' U' をくり返す。
# 6回くり返すと完成状態に戻る、という性質がある。
sequence = [rubik.R, rubik.U, rubik.Ri, rubik.Ui]

for lap in range(6):
    for turn in sequence:
        turn()                  # 引数なし。rubik.cube が回って、窓も描き直される
        time.sleep(0.7)         # 最初の1手のところで窓が開く
    print(f"{lap + 1} 周目おわり")

print("\n--- R U R' U' を6回くり返したあと ---")
rubik.show()
print("\n完成状態に戻った:", rubik.is_solved())

# 同じことは、手順の文字列でも書ける。
#
#     rubik.do("RUR'U'", times=6)
#
# ' (プライム) は関数名には使えないが、文字列でならそのまま書ける。
# 本や Web に載っている手順を、書きかえずに貼りつけられる。

# マウスで回しすぎて分からなくなったら、決まった向きに戻せる。
print("\n裏がわ (D,B,L) を見せます")
rubik.reset_DBL()
time.sleep(2.0)

print("最初の向き (U,F,R) に戻します")
rubik.reset_UFR()
time.sleep(2.0)

# キューブを自分で作ることもできる。show3d=True にすると、
# そのキューブ専用の窓がもう1つ開く。
print("\nもう1つキューブを作って、ぐちゃぐちゃにしてみます")
another = rubik.Cube(show3d=True)
another.shuffle(seed=1)
time.sleep(2.0)
another.show()

# 窓が閉じられるまで待つ。
# これが無いと、プログラムの終わりと同時に窓も消えてしまう。
rubik.wait()
