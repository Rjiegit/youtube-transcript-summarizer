import streamlit as st
from database.db_factory import DBFactory
from processing import process_pending_tasks
import math
from datetime import timezone, timedelta

def add_url_callback(db_choice):
    url = st.session_state.url_input
    if url:
        db = DBFactory.get_db(db_choice)
        db.add_task(url)
        st.toast(f"Successfully added to queue: {url} using {db_choice}", icon="✅")
        st.session_state.url_input = ""
    else:
        st.toast("Please enter a URL", icon="❌")

def main_view():
    st.title("YouTube Transcript Summarizer")

    # Initialize state for processing
    if 'processing_tasks' not in st.session_state:
        st.session_state.processing_tasks = False

    # This block will execute when the state is True after a rerun
    if st.session_state.processing_tasks:
        with st.spinner("Processing all pending tasks..."):
            process_pending_tasks()
        st.toast("Finished processing all pending tasks.", icon="✅")
        st.session_state.processing_tasks = False # Reset state
        st.rerun()

    # Section for adding URLs to the queue
    st.header("Add YouTube URL to Queue")
    db_choice_add = st.selectbox("Select Database", ["SQLite", "Notion"], key="add_db")
    
    st.text_input("Enter YouTube URL", key="url_input")

    col1, col2, _ = st.columns([2, 3, 2])
    with col1:
        st.button("Add to Queue", on_click=add_url_callback, args=(db_choice_add,), use_container_width=True)
    with col2:
        # Only show the button if not processing
        if not st.session_state.processing_tasks:
            if st.button("Process All Pending Tasks", use_container_width=True, type="primary"):
                st.session_state.processing_tasks = True
                st.rerun()
        else:
            # Show an indicator that processing is happening
            st.info("Processing...")

    # Section for displaying tasks
    st.header("Tasks in Database")
    db_choice_view = st.selectbox("Select Database to View", ["SQLite", "Notion"], key="view_db")
    db = DBFactory.get_db(db_choice_view)

    tasks = db.get_all_tasks()

    if not tasks:
        st.write("No tasks in the database.")
    else:
        # Sort tasks by created_at in descending order
        tasks.sort(key=lambda x: x.created_at, reverse=True)

        # Pagination
        if 'page_size' not in st.session_state:
            st.session_state.page_size = 20
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        page_size = st.selectbox("Items per page", [20, 50, 100], index=[20, 50, 100].index(st.session_state.page_size), key="page_size_selector")
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
        col5.write("**Duration (s)**") # New column
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
                col5.write("-") # Or some other placeholder
            if col6.button("View", key=f"view_{task.id}"):
                st.session_state.selected_task_id = task.id
                st.session_state.db_choice = db_choice_view
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
        del st.session_state.db_choice
        st.rerun()

if __name__ == "__main__":
    if "selected_task_id" in st.session_state:
        detail_view(st.session_state.selected_task_id, st.session_state.db_choice)
    else:
        main_view()

