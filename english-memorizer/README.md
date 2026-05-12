# 영어 단어 암기 앱

Python과 Streamlit으로 만든 간단한 영어 단어 암기 웹앱입니다. 초급, 중급, 고급 단어를 학습하고, 학습 완료한 단어로 복습 퀴즈를 풀 수 있습니다. 학습 기록, 퀴즈 결과, 복습 예정일은 `study_data.json` 파일에 저장되어 앱을 껐다 켜도 유지됩니다.

## 설치 방법

1. Python이 설치되어 있는지 확인합니다.

```powershell
python --version
```

2. Streamlit을 설치합니다.

```powershell
pip install streamlit
```

## 실행 방법

이 폴더에서 아래 명령을 실행합니다.

```powershell
streamlit run app.py
```

또는 `run_english_memorizer.bat` 파일을 더블클릭하면 앱이 실행됩니다.

실행 후 브라우저에서 아래 주소가 열립니다.

```text
http://localhost:8501
```

## 바탕화면 바로가기 만드는 방법

1. `run_english_memorizer.bat` 파일을 마우스 오른쪽 버튼으로 클릭합니다.
2. `바로 가기 만들기`를 선택합니다.
3. 만들어진 바로가기를 바탕화면으로 옮깁니다.
4. 바탕화면의 바로가기를 더블클릭하면 앱이 실행됩니다.

## 파일별 역할

- `app.py`: Streamlit 웹앱의 메인 실행 파일입니다.
- `words.json`: 초급, 중급, 고급 단어 데이터가 저장된 파일입니다.
- `study_data.json`: 학습 완료 단어, 퀴즈 결과, 복습 예정일이 저장되는 파일입니다.
- `run_english_memorizer.bat`: Windows에서 더블클릭으로 앱을 실행하는 배치 파일입니다.
- `README.md`: 설치, 실행, 파일 설명, 문제 해결 방법을 정리한 문서입니다.

## 단어 추가 방법

`words.json` 파일을 열고 원하는 난이도 배열에 아래와 같은 형식으로 단어를 추가합니다.

```json
{
  "word": "example",
  "meaning": "예시",
  "example": "This is an example sentence."
}
```

쉼표 위치가 올바른지 확인한 뒤 앱을 다시 실행하면 새 단어가 표시됩니다.

## 문제가 생겼을 때 확인할 명령어

Python 설치 확인:

```powershell
python --version
```

Streamlit 설치 확인:

```powershell
python -m streamlit --version
```

Streamlit 설치:

```powershell
pip install streamlit
```

앱 직접 실행:

```powershell
python -m streamlit run app.py
```

현재 폴더 파일 확인:

```powershell
Get-ChildItem
```
