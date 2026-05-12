@echo off
cd /d "%~dp0"

echo 영어 단어 암기 앱을 실행합니다.
echo 브라우저가 자동으로 열리지 않으면 아래 주소를 열어주세요.
echo http://localhost:8501
echo.

python -m streamlit run app.py

pause
