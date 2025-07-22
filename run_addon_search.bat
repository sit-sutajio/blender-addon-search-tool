@echo off
echo Blender アドオン検索ツールを起動しています...
echo.

REM 必要なライブラリをインストール
echo 必要なライブラリをチェック中...
pip install requests > nul 2>&1

REM Pythonアプリを起動
echo アプリを起動中...
echo.
python addon_search_tool.py

REM エラーが発生した場合の処理
if errorlevel 1 (
    echo.
    echo エラーが発生しました。
    echo 以下を確認してください:
    echo 1. Pythonがインストールされているか
    echo 2. addon_search_tool.py が同じフォルダにあるか
    echo 3. インターネットに接続されているか
    echo.
    pause
)