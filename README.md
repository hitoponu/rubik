# rubik

教育用のルービックキューブ Python ライブラリ。

機能は3つだけ。**リストでの表現**、**18通りの操作**、**マウスで回せる3D表示**。
速さより読みやすさを優先していて、わざと遠回りな書き方をしているところがある。

```python
import rubik

cube = rubik.solved()      # 完成状態
cube = rubik.shuffle()     # でたらめに回してぐちゃぐちゃに
cube = rubik.R(cube)       # 右の面を時計回りに90度
cube = rubik.Ui(cube)      # 上の面を反時計回りに90度

rubik.show(cube)           # 展開図を文字で表示

rubik.init(cube)           # 3Dの窓を開く
rubik.update(cube)         # 映すキューブを更新
rubik.wait()               # 窓が閉じられるまで待つ
```

## 準備

```
uv sync
uv run python examples/demo.py          # スクリプトで動かす
uv run jupyter notebook                 # ノートブックで対話的に動かす
```

見本は `examples/demo.py`（スクリプト）と `examples/demo.ipynb`
（ノートブック）の2つ。

## 動作環境

| 使いかた | 3Dの窓 | 備考 |
|---|---|---|
| 手もとの Python スクリプト | ○ | 最後に `rubik.wait()` を置く |
| 手もとの Jupyter Notebook / JupyterLab | ○ | 対話的に使うならこれが一番向いている |
| 手もとの IPython | ○ | 同上 |
| Google Colab | ✗ | 画面のないクラウド上で動くため窓を開けない |
| 画面なしのサーバ、SSH 先 | ✗ | 同上 |

窓が開けない場所では、日本語のメッセージが出る。
リスト表現と18通りの操作、`show()` による展開図表示は**どこでも動く**ので、
Colab でも3D以外はそのまま使える。

### Jupyter Notebook を動かす手順

初回だけ、ノートブックを開発用の依存に加える。

```
uv add --dev notebook
```

あとは毎回これで起動する。

```
uv run jupyter notebook
```

ブラウザが開いたら `examples/demo.ipynb` を選ぶ。カーネルは `Python 3`
をそのまま使えばよい。これはプロジェクトの `.venv` を指しているので、
`import rubik` がそのまま通る。

**かならず `uv run` を通すこと。** 素の `jupyter notebook` で起動すると
別の Python が使われてしまい、`import rubik` に失敗する。

プロジェクトに手を加えたくなければ、その場かぎりの起動もできる。

```
uv run --with notebook jupyter notebook
```

### Jupyter Notebook での使いかた

セルごとに1手ずつ進められる。窓は開いたままで、向きも保たれる。

```python
# セル1
import rubik
cube = rubik.shuffle(seed=1)
rubik.init(cube)          # 窓が開く。ここでマウスで好きな向きにしておく

# セル2 (何度でも実行できる)
cube = rubik.R(cube)
rubik.update(cube)        # 窓の中身だけが変わる。向きはさわったまま

# セル3
rubik.close()             # 窓を閉じる
```

**`rubik.wait()` は呼ばないこと。** カーネルが窓を閉じるまで止まってしまう。
ノートブックでは `close()` を使うか、そのままにしておけばよい
(カーネルを終了すると窓も閉じる)。

`%matplotlib inline` などを使っていても影響を受けない。
窓は別プロセスで動いていて、`import rubik` した側は matplotlib を
いっさい読み込まないため。

### 環境構築スクリプト

まず rubik を `git clone` して、**そのフォルダの中で**次を実行する。

| OS | 実行のしかた |
|---|---|
| macOS | `bash setup_mac.sh` |
| Windows | `setup_windows.bat` をダブルクリック |

やっていることは3段階で、途中で失敗したらどこで止まったか日本語で出る。

1. `uv` を入れる（すでにあれば飛ばす）
2. `uv sync` で Python と部品をそろえる
3. テストを流して動作を確かめる

最後に「Jupyter Notebook を開きますか」と聞いてくる。

補足。

- `git` は入れない。clone できている時点で入っているため
- uv の入れかたは、macOS は Homebrew があれば `brew install uv`、
  無ければ公式のインストーラ。Windows は `winget` があれば winget、
  無ければ公式のインストーラ。`winget` は必須ではない
- uv を入れた直後は PATH が反映されないことがある。そのときは
  「いったん画面を閉じて、もう一度実行してください」と出るので従う
- macOS で Finder からダブルクリックして使いたいときは、名前を
  `setup_mac.command` に変えて、一度だけ `chmod +x setup_mac.command` しておく

### Windows での動きかた

プラットフォームごとの分岐は書いていない。絵の描きかたは
`macosx` → `tkagg` → `qtagg` の順に試すので、Windows では `tkagg`
(Python に同梱の tkinter) が使われる。日本語の表示も
`Yu Gothic` / `MS Gothic` を探すようにしてある。

ただし**手もとに Windows 機がなく、実機での確認はできていない**。
bat ファイルは日本語が化けないよう cp932 と CRLF で書き、
ラベルの対応や echo 行の特殊文字は機械的に検査してある。

## 1. キューブのリスト表現

`6 x 3 x 3` の入れ子リスト。中身は `'B' 'Y' 'R' 'W' 'G' 'O'` の1文字。

```
cube[面][縦][横]
```

面の番号は展開図の並びで決めてある。

```
            +-------+
            | 0  U  |          0 = U  上
    +-------+-------+-------+-------+
    | 1  L  | 2  F  | 3  R  | 4  B  |
    +-------+-------+-------+-------+
            | 5  D  |
            +-------+
```

各面は**その面をキューブの外側から見た状態**で、縦座標は `0` が上・`2` が下、
横座標は `0` が左・`2` が右。どちらが「上」かは面ごとに次のとおり。

| 面 | 「上」の向き |
|---|---|
| L, F, R, B | U 面の側 |
| U | B 面の側 |
| D | F 面の側 |

展開図をそのまま紙に描いて折りたたむと立方体になる、という取り方。
中段を `L, F, R, B` の順に並べたおかげで、`U` と `D` の操作が
「4つの面の段を順ぐりにずらすだけ」になり、添字をひっくり返す処理が出てこない。

`rubik.solved()` で完成状態が作れる。配色は白の裏が黄、緑の裏が青、赤の裏が橙。

| 面 | U | L | F | R | B | D |
|---|---|---|---|---|---|---|
| 色 | W 白 | O 橙 | G 緑 | R 赤 | B 青 | Y 黄 |

ぐちゃぐちゃの状態は `rubik.shuffle()` で作れる。

```python
cube = rubik.shuffle()              # 完成状態から20手、でたらめに回す
cube = rubik.shuffle(times=5)       # 5手だけ
cube = rubik.shuffle(seed=42)       # 何度やっても同じ配置になる
cube = rubik.shuffle(cube, times=3) # 今のキューブからさらに3手
```

| 引数 | 既定値 | 意味 |
|---|---|---|
| `cube` | `None` | 回しはじめるキューブ。省くと完成状態から |
| `times` | `20` | 回す回数 |
| `seed` | `None` | 数を渡すと毎回まったく同じ回しかたになる |

`seed` を決めておくと配置を再現できるので、授業で全員に同じ問題を配るときに使える。

18通りの中からその都度1つを選ぶだけなので、`R` のすぐあとに `Ri` が来て
打ち消しあうこともある。それでも `times` が20もあればじゅうぶん混ざる。

## 2. 18通りの操作

`X` を `U D L R F B` のどれかとして、

| 関数 | 意味 |
|---|---|
| `X(cube)` | その面を時計回りに90度 |
| `Xi(cube)` | その面を反時計回りに90度（`X'` のこと。i は inverse） |
| `X2(cube)` | その面を180度 |

合わせて `U Ui U2 D Di D2 L Li L2 R Ri R2 F Fi F2 B Bi B2` の18個。
「時計回り」はいつも**その面を外側から見て**時計回りの意味。

どの関数も**操作前のキューブをもらって、操作後の新しいキューブを返す**。
もらったキューブは書きかえないので、こう書ける。

```python
after = rubik.R(before)    # before はそのまま残っている
```

渡されたキューブがおかしいときは、日本語の assert で止まる。見るのは3つ。

```python
rubik.U("リストじゃない")
# AssertionError: ルービックキューブはリストで渡してください。

rubik.U([[1, 2, 3]] * 6)
# AssertionError: ルービックキューブは 6x3x3 のリストで渡してください。

cube = rubik.solved()
cube[2][1][0] = "X"
rubik.U(cube)
# AssertionError: ルービックキューブの中身は 'B' 'Y' 'R' 'W' 'G' 'O' のどれかに
# してください。cube[2][1][0] (F面の 縦1 横0) が 'X' になっています。
```

3つめは**どこが**おかしいのかまで教えてくれる。
この検査は `rubik.check(cube)` として単体でも呼べる。

### どうやって回しているか

90度回すと、ステッカーは4枚ずつの組になって席を交換していく（巡回）。
6つの基本操作（時計回り90度）ぶんの巡回だけを表として `moves.py` に書き下し、
**反時計回りは時計回りを3回、180度は2回**くり返して作っている。
3回まわすのは無駄だが、覚える表が6つで済むので間違えにくい。

## 3. 3Dグラフィクス

| 関数 | 意味 |
|---|---|
| `rubik.init(cube=None)` | 窓を開く。`cube` を省くと完成状態 |
| `rubik.update(cube)` | 映すキューブを更新する |
| `rubik.reset_UFR()` | 見る向きを U・F・R が見える向きに戻す |
| `rubik.reset_DBL()` | 見る向きを D・B・L が見える向きに戻す |
| `rubik.wait()` | 窓が閉じられるまで待つ |
| `rubik.close()` | 窓を閉じる |

窓はマウスのドラッグでぐるぐる回せる。**`update()` しても見ている向きは変わらない。**

`rubik.wait()` を最後に置かないと、プログラムが終わると同時に窓も消える。

### 向きのリセット

窓を開いたときは `reset_UFR()` と同じ向き、つまり **U（上）・F（前）・R（右）の
3面が見える向き**から始まる。`reset_DBL()` はそのちょうど裏がわで、
**D（下）・B（後）・L（左）の3面が見える**。

2つを行き来すれば6面すべてを確かめられる。マウスで回しすぎて
どこを見ているか分からなくなったときにも使う。

```python
rubik.reset_DBL()    # 裏がわを見る
rubik.reset_UFR()    # 最初の向きに戻す
```

角度は `geometry.py` の `VIEWS` にまとめてある。

| 名前 | elev | azim | 見える面 |
|---|---|---|---|
| `UFR` | 22 | 45 | U 白 / F 緑 / R 赤 |
| `DBL` | -22 | 225 | D 黄 / B 青 / L 橙 |

向きが動くのはこの2つの関数を呼んだときだけで、`update()` では動かない。

### なぜ窓は別プロセスなのか

macOS では、窓を持つプログラムは「メインの流れ」を窓の番人にずっと明け渡して
おかないとマウスを受けつけない。しかし利用者のプログラムは自分のメインの流れで
計算をしたいので、同じプロセスの中では両立しない。そこで窓だけを
別のプロセス（`_window.py`）に追い出し、キューブを1行の JSON にして送っている。

こうすると次の3つが同時に成り立つ。

- 窓はいつでもなめらかに動く（自分のメインの流れを持っているので）
- 利用者のプログラムは `update()` のあとすぐ次の行に進める
- `update()` は**色を塗りかえるだけ**なので、見ている向きは原理的に変わらない

## ファイル

| ファイル | 中身 |
|---|---|
| `src/rubik/cube.py` | リスト表現、`solved()`、`show()`、形の検査 |
| `src/rubik/moves.py` | 18通りの操作、`shuffle()` |
| `src/rubik/geometry.py` | リストの添字と3次元空間の位置の対応表 |
| `src/rubik/viewer.py` | `init` `update` `wait` `close` |
| `src/rubik/_window.py` | 窓そのもの（別プロセスで動く） |
| `setup_mac.sh` | macOS の環境構築（git と uv を入れる） |
| `setup_windows.bat` | Windows の環境構築（git と uv を入れる） |
| `examples/demo.py` | スクリプトの見本 |
| `examples/demo.ipynb` | Jupyter Notebook の見本 |

## テスト

```
uv run python tests/test_moves.py
uv run python tests/test_viewer.py
```

操作の正しさは、よく知られた「手順の周期」と突き合わせて確かめている。
たとえば `R U` をくり返すと105回で、`R U R' U'` なら6回で完成状態に戻る。
