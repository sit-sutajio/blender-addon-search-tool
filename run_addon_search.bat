@echo off
echo Blender �A�h�I�������c�[�����N�����Ă��܂�...
echo.

REM �K�v�ȃ��C�u�������C���X�g�[��
echo �K�v�ȃ��C�u�������`�F�b�N��...
pip install requests > nul 2>&1

REM Python�A�v�����N��
echo �A�v�����N����...
echo.
python addon_search_tool.py

REM �G���[�����������ꍇ�̏���
if errorlevel 1 (
    echo.
    echo �G���[���������܂����B
    echo �ȉ����m�F���Ă�������:
    echo 1. Python���C���X�g�[������Ă��邩
    echo 2. addon_search_tool.py �������t�H���_�ɂ��邩
    echo 3. �C���^�[�l�b�g�ɐڑ�����Ă��邩
    echo.
    pause
)