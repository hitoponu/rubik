#!/bin/bash
#
# rubik  macOS 環境構築
#
# Finder でこのファイルをダブルクリックすれば動く。
# ターミナルからなら、rubik フォルダの中で
#
#   ./setup_mac.command
#
# uv を入れて、Python の環境をそろえ、動作確認まで済ませる。
# clone した rubik フォルダの中に置いて、そこで実行すること。
#
# 拡張子が .sh ではなく .command なのは、macOS では .command だけが
# 「ダブルクリックしたら Terminal が実行するもの」として登録されているため。
# .sh は .bashrc などと同じ「ただの文字ファイル」あつかいなので、
# ダブルクリックしてもエディタで開くだけで実行されない。
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ----------------------------------------------------------------------

say() {
    echo "$@"
}

die() {
    echo ""
    echo "  [エラー] $1"
    shift
    while [ $# -gt 0 ]; do
        echo "  $1"
        shift
    done
    echo ""
    exit 1
}

have() {
    command -v "$1" >/dev/null 2>&1
}

# ----------------------------------------------------------------------

say ""
say "=========================================================="
say "   rubik  macOS 環境構築"
say "=========================================================="
say ""
say "   uv を入れて、Python の環境をそろえます。"
say ""

# --- ここが rubik プロジェクトの中か ----------------------------------
if [ ! -f "$SCRIPT_DIR/pyproject.toml" ]; then
    die "rubik プロジェクトの中ではないようです。" \
        "clone した rubik フォルダの中にこのスクリプトを置いて、" \
        "そこで実行してください。"
fi

cd "$SCRIPT_DIR" || die "$SCRIPT_DIR に移動できませんでした。"

# --- 1. uv ------------------------------------------------------------
say "[1/3] uv を確認しています..."

if have uv; then
    say "       すでに入っています。"
else
    say "       入っていないので入れます。"
    installed=0

    # Homebrew を使っている人は、そちらに合わせる
    if have brew; then
        say "       Homebrew があるので brew で入れます..."
        if brew install uv; then
            installed=1
        else
            say "       brew では入りませんでした。公式の手順に切りかえます。"
        fi
    fi

    if [ "$installed" -eq 0 ]; then
        say "       公式のインストーラで入れます..."
        # uv 公式の入れかた
        # https://docs.astral.sh/uv/getting-started/installation/
        if ! curl -LsSf https://astral.sh/uv/install.sh | sh; then
            die "uv を入れられませんでした。" \
                "https://docs.astral.sh/uv/getting-started/installation/" \
                "を見て手で入れてください。"
        fi
    fi
fi

# 入れた直後は、今のターミナルから見えないことがあるので足しておく
PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH

if ! have uv; then
    die "uv は入りましたが、このターミナルからはまだ使えません。" \
        "いったんターミナルを閉じて、もう一度このスクリプトを実行してください。"
fi
say "       OK  $(uv --version)"
say ""

# --- 2. Python の環境 -------------------------------------------------
say "[2/3] Python、ライブラリ、Jupyter Notebook をそろえています。"
say "       初回は5分ほどかかることがあります..."
say ""
say "       Jupyter Notebook は pyproject.toml の dependency-groups に"
say "       書いてあるので、この uv sync で一緒に入ります。"
say ""

if ! uv sync; then
    die "uv sync に失敗しました。" \
        "ネットにつながっているか確かめて、もう一度実行してください。"
fi
say "       OK"
say ""

# --- 3. 動作確認 ------------------------------------------------------
say "[3/3] ちゃんと動くか確かめています..."

if [ -f "tests/test_moves.py" ]; then
    if ! uv run python tests/test_moves.py; then
        die "動作確認のテストが通りませんでした。" \
            "上に出ているメッセージを控えて、先生に相談してください。"
    fi
fi

# Jupyter Notebook がちゃんと入ったか
if ! uv run python -c "import notebook" >/dev/null 2>&1; then
    die "Jupyter Notebook が入っていません。" \
        "pyproject.toml の dependency-groups に notebook があるか確かめて、" \
        "もう一度このスクリプトを実行してください。"
fi
say ""
say "       Jupyter Notebook も入っています。"

say ""
say "=========================================================="
say "   セットアップが終わりました"
say "=========================================================="
say ""
say "   3D の見本を動かす:"
say "       uv run python examples/demo.py"
say ""
say "   ノートブックを開く:"
say "       uv run jupyter notebook"
say ""
say "   次からは、このフォルダで上のコマンドを打つだけで使えます。"
say ""

# 画面から実行しているときだけ聞く
if [ -t 0 ]; then
    ANSWER=""
    printf "   いま Jupyter Notebook を開きますか? y か n を入れて Enter: "
    read -r ANSWER
    case "$ANSWER" in
        [yY]*)
            say ""
            say "   ブラウザが開きます。"
            say "   やめるときは、この画面で Ctrl+C を2回押してください。"
            say ""
            uv run jupyter notebook
            ;;
    esac
fi

exit 0
