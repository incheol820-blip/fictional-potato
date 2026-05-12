import json
from datetime import date, datetime, timedelta
from pathlib import Path

import streamlit as st


APP_TITLE = "영어 단어 암기 앱"
BASE_DIR = Path(__file__).resolve().parent
WORDS_FILE = BASE_DIR / "words.json"
STUDY_FILE = BASE_DIR / "study_data.json"
REVIEW_INTERVALS = {
    "1일 후": 1,
    "3일 후": 3,
    "7일 후": 7,
    "14일 후": 14,
}


def today_text():
    return date.today().isoformat()


def load_json(path, default):
    if not path.exists():
        save_json(path, default)
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        st.error(f"{path.name} 파일을 읽을 수 없습니다. JSON 형식을 확인해 주세요.")
        st.stop()


def save_json(path, data):
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_words():
    return load_json(WORDS_FILE, {"초급": [], "중급": [], "고급": []})


def load_study_data():
    data = load_json(
        STUDY_FILE,
        {
            "learned_words": {},
            "quiz_results": [],
        },
    )
    data.setdefault("learned_words", {})
    data.setdefault("quiz_results", [])
    return data


def word_id(level, word):
    return f"{level}:{word}"


def find_word(words, word_key):
    try:
        level, english = word_key.split(":", 1)
    except ValueError:
        return None

    for item in words.get(level, []):
        if item.get("word") == english:
            return level, item
    return None


def mark_learned(study_data, level, item):
    key = word_id(level, item["word"])
    learned = study_data["learned_words"].setdefault(
        key,
        {
            "level": level,
            "word": item["word"],
            "meaning": item["meaning"],
            "example": item["example"],
            "learned_at": today_text(),
            "review_due": today_text(),
            "review_interval_days": 1,
            "correct_count": 0,
            "wrong_count": 0,
        },
    )
    learned.update(
        {
            "level": level,
            "word": item["word"],
            "meaning": item["meaning"],
            "example": item["example"],
            "learned_at": learned.get("learned_at", today_text()),
        }
    )
    save_json(STUDY_FILE, study_data)


def set_review_date(study_data, key, interval_label):
    days = REVIEW_INTERVALS[interval_label]
    learned = study_data["learned_words"][key]
    learned["review_interval_days"] = days
    learned["review_due"] = (date.today() + timedelta(days=days)).isoformat()
    save_json(STUDY_FILE, study_data)


def record_quiz_result(study_data, key, user_answer, is_correct):
    learned = study_data["learned_words"][key]
    if is_correct:
        learned["correct_count"] = learned.get("correct_count", 0) + 1
    else:
        learned["wrong_count"] = learned.get("wrong_count", 0) + 1

    study_data["quiz_results"].append(
        {
            "word_key": key,
            "word": learned["word"],
            "user_answer": user_answer,
            "correct_answer": learned["meaning"],
            "is_correct": is_correct,
            "checked_at": datetime.now().isoformat(timespec="seconds"),
        }
    )
    save_json(STUDY_FILE, study_data)


def is_due(learned):
    review_due = learned.get("review_due", today_text())
    return review_due <= today_text()


def render_word_card(study_data, level, item):
    key = word_id(level, item["word"])
    learned = key in study_data["learned_words"]

    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.subheader(item["word"])
            st.write(f"뜻: {item['meaning']}")
            st.caption(f"예문: {item['example']}")
        with right:
            if learned:
                st.success("학습 완료")
                due = study_data["learned_words"][key].get("review_due", "-")
                st.caption(f"복습 예정일: {due}")
            else:
                if st.button("학습 완료", key=f"learn_{key}"):
                    mark_learned(study_data, level, item)
                    st.rerun()


def render_review_settings(study_data):
    st.header("반복 학습 설정")
    learned_words = study_data["learned_words"]

    if not learned_words:
        st.info("학습 완료한 단어가 아직 없습니다.")
        return

    for key, learned in sorted(learned_words.items()):
        with st.container(border=True):
            cols = st.columns([2, 2, 2])
            cols[0].write(f"**{learned['word']}**")
            cols[0].caption(learned["meaning"])
            cols[1].write(f"복습 예정일: {learned.get('review_due', '-')}")
            selected = cols[2].selectbox(
                "반복일",
                list(REVIEW_INTERVALS.keys()),
                key=f"interval_{key}",
                label_visibility="collapsed",
            )
            if cols[2].button("반복일 저장", key=f"save_interval_{key}"):
                set_review_date(study_data, key, selected)
                st.rerun()


def render_today_review(study_data):
    st.header("오늘 복습할 단어")
    due_items = [
        (key, learned)
        for key, learned in study_data["learned_words"].items()
        if is_due(learned)
    ]

    if not due_items:
        st.info("오늘 복습할 단어가 없습니다.")
        return

    for key, learned in sorted(due_items):
        with st.container(border=True):
            st.write(f"**{learned['word']}** - {learned['meaning']}")
            st.caption(f"예문: {learned['example']}")
            selected = st.selectbox(
                "복습 후 다음 반복일",
                list(REVIEW_INTERVALS.keys()),
                key=f"today_interval_{key}",
            )
            if st.button("복습 완료 후 반복일 설정", key=f"review_done_{key}"):
                set_review_date(study_data, key, selected)
                st.rerun()


def render_quiz(study_data):
    st.header("복습 퀴즈")
    learned_words = study_data["learned_words"]

    if not learned_words:
        st.info("퀴즈를 풀려면 먼저 단어를 학습 완료로 저장해 주세요.")
        return

    options = {
        f"{learned['word']} ({learned['level']})": key
        for key, learned in sorted(learned_words.items())
    }
    selected_label = st.selectbox("퀴즈 단어 선택", list(options.keys()))
    selected_key = options[selected_label]
    learned = learned_words[selected_key]

    with st.container(border=True):
        st.subheader(learned["word"])
        user_answer = st.text_input("한글 뜻을 입력하세요", key=f"answer_{selected_key}")

        if st.button("정답 확인", key=f"check_{selected_key}"):
            normalized_user = user_answer.strip()
            normalized_answer = learned["meaning"].strip()
            is_correct = normalized_user == normalized_answer
            record_quiz_result(study_data, selected_key, normalized_user, is_correct)

            if is_correct:
                st.success("맞았습니다.")
            else:
                st.error(f"틀렸습니다. 정답: {learned['meaning']}")

    st.subheader("퀴즈 기록")
    recent_results = list(reversed(study_data["quiz_results"][-10:]))
    if not recent_results:
        st.caption("아직 퀴즈 기록이 없습니다.")
        return

    for result in recent_results:
        icon = "O" if result["is_correct"] else "X"
        st.write(
            f"{icon} {result['word']} | 입력: {result['user_answer'] or '(빈칸)'} "
            f"| 정답: {result['correct_answer']} | {result['checked_at']}"
        )


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="📘", layout="wide")
    st.title(APP_TITLE)

    words = load_words()
    study_data = load_study_data()

    selected_level = st.sidebar.radio("단어 난이도 선택", ["초급", "중급", "고급"])
    st.sidebar.divider()
    st.sidebar.metric("학습 완료 단어", len(study_data["learned_words"]))
    st.sidebar.metric("퀴즈 기록", len(study_data["quiz_results"]))

    tab_study, tab_quiz, tab_repeat = st.tabs(["단어 학습", "복습 퀴즈", "반복 학습"])

    with tab_study:
        st.header(f"{selected_level} 단어 목록")
        level_words = words.get(selected_level, [])
        if not level_words:
            st.info("이 난이도에는 등록된 단어가 없습니다.")
        for item in level_words:
            render_word_card(study_data, selected_level, item)

    with tab_quiz:
        render_quiz(study_data)

    with tab_repeat:
        render_today_review(study_data)
        st.divider()
        render_review_settings(study_data)


if __name__ == "__main__":
    main()
