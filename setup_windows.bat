@echo off
chcp 932 >nul 2>&1
setlocal
title rubik Windows 環境構築

echo.
echo ==========================================================
echo    rubik  Windows 環境構築
echo ==========================================================
echo.
echo    uv を入れて、Python の環境をそろえます。
echo    途中で「ユーザーアカウント制御」の確認が出たら
echo    「はい」を選んでください。
echo.

REM ---------- ここが rubik プロジェクトの中か ----------
if not exist "%~dp0pyproject.toml" goto :no_project
pushd "%~dp0."

REM ---------- 1. uv ----------
echo [1/3] uv を確認しています...
where uv >nul 2>&1
if not errorlevel 1 goto :uv_ready
echo        入っていないので入れます。数分かかります。
where winget >nul 2>&1
if errorlevel 1 goto :uv_by_powershell
winget install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements
if not errorlevel 1 goto :uv_added
echo        winget では入りませんでした。公式の手順に切りかえます。
:uv_by_powershell
echo        公式のインストーラで入れます...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
if errorlevel 1 goto :fail_uv
:uv_added
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin"
where uv >nul 2>&1
if errorlevel 1 goto :reopen
:uv_ready
echo        OK
echo.

REM ---------- 2. Python の環境 ----------
echo [2/3] Python と必要な部品をそろえています。
echo        初回は5分ほどかかることがあります...
uv sync
if errorlevel 1 goto :fail_sync
echo        OK
echo.

REM ---------- 3. 動作確認 ----------
echo [3/3] ちゃんと動くか確かめています...
if not exist "tests\test_moves.py" goto :skip_test
uv run python tests\test_moves.py
if errorlevel 1 goto :fail_test
:skip_test
echo.
echo ==========================================================
echo    セットアップが終わりました
echo ==========================================================
echo.
echo    3D の見本を動かす:
echo        uv run python examples\demo.py
echo.
echo    ノートブックを開く:
echo        uv run jupyter notebook
echo.
echo    次からは、この画面で上のコマンドを打つだけで使えます。
echo.
set "ANSWER="
set /p ANSWER="   いま Jupyter Notebook を開きますか? Y か N を入れて Enter: "
if /i "%ANSWER%"=="Y" goto :launch
goto :done

:launch
echo.
echo    ブラウザが開きます。
echo    やめるときは、この画面で Ctrl+C を2回押してください。
echo.
uv run jupyter notebook
goto :done

REM ---------------------------------------------------------
:no_project
echo.
echo    [エラー] rubik プロジェクトの中ではないようです。
echo    clone した rubik フォルダの中にこの bat を置いて、
echo    そこで実行してください。
goto :abort

:fail_uv
echo.
echo    [エラー] uv を入れられませんでした。
echo    https://docs.astral.sh/uv/getting-started/installation/
echo    を見て手で入れてください。
goto :abort

:reopen
echo.
echo    uv は入りましたが、この画面ではまだ使えません。
echo    いったんこの画面を閉じて、もう一度この bat を実行してください。
goto :abort

:fail_sync
echo.
echo    [エラー] uv sync に失敗しました。
echo    ネットにつながっているか確かめて、もう一度実行してください。
goto :abort

:fail_test
echo.
echo    [エラー] 動作確認のテストが通りませんでした。
echo    上に出ているメッセージを控えて、先生に相談してください。
goto :abort

:abort
popd 2>nul
echo.
pause
endlocal
exit /b 1

:done
popd 2>nul
echo.
pause
endlocal
exit /b 0
