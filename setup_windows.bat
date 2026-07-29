@echo off
chcp 932 >nul 2>&1
setlocal
title rubik Windows 環境構築

echo.
echo ==========================================================
echo    rubik  Windows 環境構築
echo ==========================================================
echo.
echo    git と uv を入れて、Python の環境をそろえます。
echo    途中で「ユーザーアカウント制御」の確認が出たら
echo    「はい」を選んでください。
echo.

REM ==========================================================
REM  取得元。空のままなら、この bat と同じ場所にある
REM  rubik プロジェクトを使います。
REM  git clone させたいときは、ここに URL を書いてください。
REM ==========================================================
set "REPO_URL="

REM ---------------------------------------------------------
echo [1/6] winget を探しています...
where winget >nul 2>&1
if errorlevel 1 goto :no_winget
echo        見つかりました。
echo.

REM ---------------------------------------------------------
echo [2/6] git を確認しています...
where git >nul 2>&1
if not errorlevel 1 goto :git_ready
echo        入っていないので入れます。数分かかります。
winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto :fail_git
:git_ready
set "PATH=%PATH%;C:\Program Files\Git\cmd"
echo        OK
echo.

REM ---------------------------------------------------------
echo [3/6] uv を確認しています...
where uv >nul 2>&1
if not errorlevel 1 goto :uv_ready
echo        入っていないので入れます。数分かかります。
winget install --id astral-sh.uv -e --source winget --accept-package-agreements --accept-source-agreements
if not errorlevel 1 goto :uv_added
echo        winget で入れられなかったので、公式の手順を試します...
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 ^| iex"
if errorlevel 1 goto :fail_uv
:uv_added
set "PATH=%PATH%;%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin"
where uv >nul 2>&1
if errorlevel 1 goto :reopen
:uv_ready
echo        OK
echo.

REM ---------------------------------------------------------
echo [4/6] rubik プロジェクトを探しています...
set "PROJ="
if exist "%~dp0pyproject.toml" set "PROJ=%~dp0."
if not defined PROJ if exist "%~dp0rubik\pyproject.toml" set "PROJ=%~dp0rubik"
if defined PROJ goto :proj_ready
if not defined REPO_URL goto :no_project
echo        手もとに無いので取ってきます...
git clone "%REPO_URL%" "%~dp0rubik"
if errorlevel 1 goto :fail_clone
set "PROJ=%~dp0rubik"
:proj_ready
pushd "%PROJ%"
echo        %CD%
echo.

REM ---------------------------------------------------------
echo [5/6] Python と必要な部品をそろえています。
echo        初回は5分ほどかかることがあります...
uv sync
if errorlevel 1 goto :fail_sync
echo        OK
echo.

REM ---------------------------------------------------------
echo [6/6] ちゃんと動くか確かめています...
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
:no_winget
echo.
echo    [エラー] winget が見つかりませんでした。
echo    Microsoft Store で「アプリ インストーラー」を入れてから、
echo    この画面を閉じて、もう一度実行してください。
goto :abort

:fail_git
echo.
echo    [エラー] git を入れられませんでした。
echo    https://git-scm.com/download/win から手で入れてください。
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

:no_project
echo.
echo    [エラー] rubik プロジェクトが見つかりませんでした。
echo    この bat を rubik フォルダの中に置いて実行するか、
echo    bat の中ほどにある REPO_URL に取得元を書いてください。
goto :abort

:fail_clone
echo.
echo    [エラー] git clone に失敗しました。
echo    REPO_URL が正しいか、ネットにつながっているか確かめてください。
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
