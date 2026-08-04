#!/bin/bash
#
# rubik  Jupyter Notebook を起動する
#
# Finder でこのファイルをダブルクリックすれば、ブラウザで
# Jupyter Notebook が開く。
# ターミナルからなら、rubik フォルダの中で
#
#   ./start_jupyter.command
#
# 先に setup_mac.command で環境を作っておくこと。
#
# 拡張子が .sh ではなく .command なのは、macOS では .command だけが
# 「ダブルクリックしたら Terminal が実行するもの」として登録されているため。
#

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ----------------------------------------------------------------------

die() {
    echo ""
    echo "  [エラー] $1"
    shift
    while [ $# -gt 0 ]; do
        echo "  $1"
        shift
    done
    echo ""
    echo "  何かキーを押すと閉じます。"
    read -r _
    exit 1
}

# ----------------------------------------------------------------------

cd "$SCRIPT_DIR" || die "$SCRIPT_DIR に移動できませんでした。"

if [ ! -f "pyproject.toml" ]; then
    die "rubik プロジェクトの中ではないようです。" \
        "clone した rubik フォルダの中にこのファイルを置いて、" \
        "そこで実行してください。"
fi

# uv を入れた直後は、今の画面から見えないことがあるので足しておく
PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
export PATH

if ! command -v uv >/dev/null 2>&1; then
    die "uv が見つかりません。" \
        "先に setup_mac.command をダブルクリックして、" \
        "環境を作ってください。"
fi

echo ""
echo "=========================================================="
echo "   rubik  Jupyter Notebook"
echo "=========================================================="
echo ""
echo "   ブラウザで Jupyter Notebook が開きます。"
echo "   examples フォルダの demo.ipynb を選んでみてください。"
echo ""
echo "   終わるときは、この画面で Ctrl+C を2回押してください。"
echo ""

# 足りない部品があれば uv がここで入れてくれる
uv run jupyter notebook

echo ""
echo "   Jupyter Notebook を終了しました。"
echo ""
