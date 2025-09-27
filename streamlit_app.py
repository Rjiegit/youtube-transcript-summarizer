import streamlit as st
from database.db_factory import DBFactory
from processing import process_pending_tasks
from url_validator import normalize_youtube_url, is_valid_youtube_url
import math
from datetime import timezone, timedelta


SCROLL_FLAG_KEY = "scroll_to_view_top"


def maybe_scroll_to_top():
    if st.session_state.get(SCROLL_FLAG_KEY):
        st.session_state[SCROLL_FLAG_KEY] = False
        st.components.v1.html(
            """
            <script>
            window.scrollTo({ top: 0, behavior: 'auto' });
            </script>
            """,
            height=0,
        )


def add_url_callback(db_choice):
    url = st.session_state.url_input
    if url:
        normalized = normalize_youtube_url(url)
        if not normalized or not is_valid_youtube_url(normalized):
            st.toast("Invalid YouTube URL", icon="❌")
            return
        db = DBFactory.get_db(db_choice)
        db.add_task(normalized)
        st.toast(
            f"Successfully added to queue: {normalized} using {db_choice}",
            icon="✅",
        )
        st.session_state.url_input = ""
    else:
        st.toast("Please enter a URL", icon="❌")


def main_view():
    st.title("YouTube Transcript Summarizer")
    maybe_scroll_to_top()

    # Initialize state for processing
    if "processing_tasks" not in st.session_state:
        st.session_state.processing_tasks = False

    # This block will execute when the state is True after a rerun
    if st.session_state.processing_tasks:
        with st.spinner("Processing all pending tasks..."):
            process_pending_tasks()
        st.toast("Finished processing all pending tasks.", icon="✅")
        st.session_state.processing_tasks = False  # Reset state
        st.rerun()

    # Section for adding URLs to the queue
    st.header("Add YouTube URL to Queue")
    # Use a single database selection for the entire view
    db_choice = st.selectbox("Select Database", ["SQLite", "Notion"], key="db_choice")

    st.text_input("Enter YouTube URL", key="url_input")

    col1, col2, _ = st.columns([2, 3, 2])
    with col1:
        st.button(
            "Add to Queue",
            on_click=add_url_callback,
            args=(db_choice,),
            use_container_width=True,
        )
    with col2:
        # Only show the button if not processing
        if not st.session_state.processing_tasks:
            if st.button(
                "Process All Pending Tasks", use_container_width=True, type="primary"
            ):
                st.session_state.processing_tasks = True
                st.rerun()
        else:
            # Show an indicator that processing is happening
            st.info("Processing...")

    # Section for displaying tasks
    st.header("Tasks in Database")
    # Reuse the same database selection for viewing tasks
    db = DBFactory.get_db(db_choice)

    tasks = db.get_all_tasks()

    if not tasks:
        st.write("No tasks in the database.")
    else:
        # Sort tasks by created_at in descending order
        tasks.sort(key=lambda x: x.created_at, reverse=True)

        # Pagination
        if "page_size" not in st.session_state:
            st.session_state.page_size = 20
        if "current_page" not in st.session_state:
            st.session_state.current_page = 1

        page_size = st.selectbox(
            "Items per page",
            [20, 50, 100],
            index=[20, 50, 100].index(st.session_state.page_size),
            key="page_size_selector",
        )
        st.session_state.page_size = page_size

        total_pages = math.ceil(len(tasks) / st.session_state.page_size)
        start_idx = (st.session_state.current_page - 1) * st.session_state.page_size
        end_idx = start_idx + st.session_state.page_size
        paginated_tasks = tasks[start_idx:end_idx]

        # Display tasks in a table-like format
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.write("**URL**")
        col2.write("**Title**")
        col3.write("**Status**")
        col4.write("**Created At (Taipei)**")
        col5.write("**Duration (s)**")  # New column
        col6.write("**Action**")

        for task in paginated_tasks:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.write(task.url)
            col2.write(task.title)
            col3.write(task.status)
            taipei_time = task.created_at.astimezone(timezone(timedelta(hours=8)))
            col4.write(taipei_time.strftime("%Y-%m-%d %H:%M:%S"))
            # Display duration if available and task is completed
            if task.status == "Completed" and task.processing_duration is not None:
                col5.write(f"{task.processing_duration:.2f}")
            else:
                col5.write("-")  # Or some other placeholder
            if col6.button("View", key=f"view_{task.id}"):
                st.session_state.selected_task_id = task.id
                # Store selection under a different key to avoid
                # modifying the widget-backed session key "db_choice".
                st.session_state.selected_db_choice = db_choice
                st.session_state[SCROLL_FLAG_KEY] = True
                st.rerun()

        # Pagination controls
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Previous"):
                if st.session_state.current_page > 1:
                    st.session_state.current_page -= 1
                    st.rerun()
        with col2:
            st.write(f"Page {st.session_state.current_page} of {total_pages}")
        with col3:
            if st.button("Next"):
                if st.session_state.current_page < total_pages:
                    st.session_state.current_page += 1
                    st.rerun()


def detail_view(task_id, db_choice):
    st.title("Task Details")
    maybe_scroll_to_top()
    db = DBFactory.get_db(db_choice)
    task = db.get_task_by_id(task_id)

    if task:
        st.write(f"**URL:** {task.url}")
        st.write(f"**Title:** {task.title}")
        st.write(f"**Status:** {task.status}")
        if task.processing_duration is not None:
            st.write(f"**Processing Duration:** {task.processing_duration:.2f} seconds")
        st.header("Summary")
        st.markdown(task.summary)
    else:
        st.error("Task not found.")

    if st.button("Back to Main View"):
        del st.session_state.selected_task_id
        if "selected_db_choice" in st.session_state:
            del st.session_state.selected_db_choice
        st.session_state[SCROLL_FLAG_KEY] = True
        st.rerun()


if __name__ == "__main__":
    if "selected_task_id" in st.session_state:
        # Use a separate session key to carry the db selection
        # into the detail view to avoid conflicting with the
        # selectbox widget key "db_choice" in the main view.
        chosen_db = st.session_state.get(
            "selected_db_choice",
            st.session_state.get("db_choice", "SQLite"),
        )
        detail_view(st.session_state.selected_task_id, chosen_db)
    else:
        main_view()
