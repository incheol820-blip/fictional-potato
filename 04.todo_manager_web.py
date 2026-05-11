import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import streamlit as st

TODO_FILE = Path("todos.json")


@dataclass
class Todo:
    id: int
    text: str
    created_at: str
    due: Optional[str]
    priority: int = 3
    done: bool = False
    done_at: Optional[str] = None


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def format_due(due: Optional[str]) -> str:
    if due is None:
        return "-"
    try:
        return datetime.fromisoformat(due).date().isoformat()
    except ValueError:
        return due


def load_todos() -> list[Todo]:
    if not TODO_FILE.exists():
        return []

    try:
        with TODO_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise RuntimeError("todos.json 파일이 손상되었습니다(JSON 파싱 실패).") from exc
    except OSError as exc:
        raise RuntimeError(f"파일을 읽는 중 오류가 발생했습니다: {exc}") from exc

    if not isinstance(data, list):
        raise RuntimeError("todos.json의 루트는 배열(list)이어야 합니다.")

    todos: list[Todo] = []
    for item in data:
        if not isinstance(item, dict):
            raise RuntimeError("todos.json 항목 형식이 잘못되었습니다.")
        try:
            todo = Todo(
                id=int(item["id"]),
                text=str(item["text"]),
                created_at=str(item["created_at"]),
                due=item.get("due"),
                priority=int(item.get("priority", 3)),
                done=bool(item.get("done", False)),
                done_at=item.get("done_at"),
            )
        except (KeyError, ValueError, TypeError) as exc:
            raise RuntimeError(f"todos.json 항목 값이 잘못되었습니다: {item}") from exc

        if todo.priority < 1 or todo.priority > 5:
            raise RuntimeError(f"우선순위 값이 유효하지 않습니다(id={todo.id}).")
        todos.append(todo)

    return todos


def save_todos(todos: list[Todo]) -> None:
    data = [asdict(todo) for todo in todos]
    try:
        with TODO_FILE.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise RuntimeError(f"파일을 저장하는 중 오류가 발생했습니다: {exc}") from exc


def next_id(todos: list[Todo]) -> int:
    return max((todo.id for todo in todos), default=0) + 1


def sorted_todos(todos: list[Todo]) -> list[Todo]:
    return sorted(todos, key=lambda t: (t.done, t.priority, t.due or "9999"))


def todo_to_row(todo: Todo) -> dict[str, str | int]:
    return {
        "ID": todo.id,
        "내용": todo.text,
        "우선순위": todo.priority,
        "마감일": format_due(todo.due),
        "생성일": todo.created_at,
        "상태": "완료" if todo.done else "진행",
        "완료일": todo.done_at or "-",
    }


def complete_todo_by_id(todos: list[Todo], target_id: int) -> bool:
    target = next((t for t in todos if t.id == target_id), None)
    if target is None or target.done:
        return False
    target.done = True
    target.done_at = now_iso()
    save_todos(todos)
    return True


def clear_done_todos(todos: list[Todo]) -> int:
    kept = [t for t in todos if not t.done]
    removed = len(todos) - len(kept)
    if removed > 0:
        save_todos(kept)
    return removed


def main() -> None:
    st.set_page_config(page_title="Streamlit To-Do 앱", page_icon="📝")
    st.title("📝 Streamlit To-Do 앱")
    st.write("간단한 파일 기반 할 일 관리자입니다. 아래에서 할 일을 추가하고 완료 상태를 관리하세요.")

    todos = load_todos()
    active_count = sum(1 for t in todos if not t.done)
    done_count = sum(1 for t in todos if t.done)

    col1, col2, col3 = st.columns(3)
    col1.metric("전체 항목", len(todos))
    col2.metric("진행 중", active_count)
    col3.metric("완료", done_count)

    with st.sidebar.expander("새 할 일 추가", expanded=True):
        with st.form("todo_add_form"):
            text = st.text_input("할 일 내용", max_chars=100)
            use_due = st.checkbox("마감일 설정")
            if use_due:
                due_date = st.date_input("마감일", value=date.today())
            else:
                due_date = None
            priority = st.slider("우선순위", 1, 5, 3)
            add_clicked = st.form_submit_button("할 일 추가")

            if add_clicked:
                if not text.strip():
                    st.error("할 일 내용은 비워둘 수 없습니다.")
                else:
                    due = due_date.isoformat() if due_date else None
                    todo = Todo(
                        id=next_id(todos),
                        text=text.strip(),
                        created_at=now_iso(),
                        due=due,
                        priority=priority,
                    )
                    todos.append(todo)
                    save_todos(todos)
                    st.success(f"할 일이 추가되었습니다. (id={todo.id})")

    st.write("---")
    st.header("할 일 목록")

    if not todos:
        st.info("등록된 할 일이 없습니다. 사이드바에서 새로운 할 일을 추가하세요.")
    else:
        todos_sorted = sorted_todos(todos)
        st.dataframe([todo_to_row(todo) for todo in todos_sorted], use_container_width=True)

        st.write("---")
        st.subheader("진행 중인 할 일 완료 처리")
        for todo in todos_sorted:
            if todo.done:
                continue
            cols = st.columns([1, 4, 2, 1])
            cols[0].write(todo.id)
            cols[1].write(todo.text)
            cols[2].write(f"우선순위 {todo.priority}, 마감일 {format_due(todo.due)}")
            if cols[3].button("완료", key=f"complete_{todo.id}"):
                if complete_todo_by_id(todos, todo.id):
                    st.success(f"id={todo.id} 항목을 완료 처리했습니다.")
                    todos = load_todos()

    st.write("---")
    if st.button("완료 항목 삭제"):
        removed = clear_done_todos(todos)
        if removed == 0:
            st.info("삭제할 완료 항목이 없습니다.")
        else:
            st.success(f"완료 항목 {removed}개를 삭제했습니다.")
            todos = [t for t in todos if not t.done]


if __name__ == "__main__":
    main()
