#!/bin/bash
#
# rubik  macOS 環境構築
#
#   bash setup_mac.sh
#
# git と uv を入れて、Python の環境をそろえ、動作確認まで済ませる。
#
# Finder でダブルクリックして使いたいときは、名前を setup_mac.command に
# 変えてから、一度だけ次を実行して実行権限をつけておく。
#
#   chmod +x setup_mac.command
#

# 取得元。空のままなら、この sh と同じ場所にある rubik プロジェクトを使う。
# git clone させたいときは、ここに URL を書く。
REPO_URL=""

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
say "   git と uv を入れて、Python の環境をそろえます。"
say "   途中でパスワードを聞かれたら、Mac のログインパスワードを入れてください。"
say ""

# --- 1. git (Xcode コマンドラインツール) ------------------------------
say "[1/5] git を確認しています..."

if xcode-select -p >/dev/null 2>&1; then
    say "       すでに入っています。"
else
    say "       入っていないので入れます。"
    say "       別のウィンドウが開くので、案内にしたがって進めてください。"
    xcode-select --install >/dev/null 2>&1

    printf "       終わるのを待っています"
    waited=0
    while ! xcode-select -p >/dev/null 2>&1; do
        printf "."
        sleep 5
        waited=$((waited + 5))
        if [ "$waited" -ge 1800 ]; then
            echo ""
            die "Xcode コマンドラインツールが入りませんでした。" \
                "もう一度このスクリプトを実行してみてください。"
        fi
    done
    echo ""
fi

if ! have git; then
    die "git が見つかりません。" \
        "https://git-scm.com/download/mac から手で入れてください。"
fi
say "       OK  $(git --version)"
say ""

# --- 2. uv ------------------------------------------------------------
say "[2/5] uv を確認しています..."

if have uv; then
    say "       すでに入っています。"
else
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
        # uv 公式の入れかた (https://docs.astral.sh/uv/getting-started/installation/)
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

# --- 3. プロジェクトを探す --------------------------------------------
say "[3/5] rubik プロジェクトを探しています..."

PROJ=""
if [ -f "$SCRIPT_DIR/pyproject.toml" ]; then
    PROJ="$SCRIPT_DIR"
elif [ -f "$SCRIPT_DIR/rubik/pyproject.toml" ]; then
    PROJ="$SCRIPT_DIR/rubik"
elif [ -n "$REPO_URL" ]; then
    say "       手もとに無いので取ってきます..."
    if ! git clone "$REPO_URL" "$SCRIPT_DIR/rubik"; then
        die "git clone に失敗しました。" \
            "REPO_URL が正しいか、ネットにつながっているか確かめてください。"
    fi
    PROJ="$SCRIPT_DIR/rubik"
else
    die "rubik プロジェクトが見つかりませんでした。" \
        "このスクリプトを rubik フォルダの中に置いて実行するか、" \
        "スクリプトの先頭にある REPO_URL に取得元を書いてください。"
fi

cd "$PROJ" || die "$PROJ に移動できませんでした。"
say "       $PROJ"
say ""

# --- 4. Python の環境 -------------------------------------------------
say "[4/5] Python と必要な部品をそろえています。"
say "       初回は5分ほどかかることがあります..."

if ! uv sync; then
    die "uv sync に失敗しました。" \
        "ネットにつながっているか確かめて、もう一度実行してください。"
fi
say "       OK"
say ""

# --- 5. 動作確認 ------------------------------------------------------
say "[5/5] ちゃんと動くか確かめています..."

if [ -f "tests/test_moves.py" ]; then
    if ! uv run python tests/test_moves.py; then
        die "動作確認のテストが通りませんでした。" \
            "上に出ているメッセージを控えて、先生に相談してください。"
    fi
fi

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
