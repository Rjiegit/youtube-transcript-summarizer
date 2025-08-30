import streamlit as st
from db.db_factory import DBFactory
from processing import process_pending_tasks
from db.task import Task
import pandas as pd

st.title("YouTube Transcript Summarizer")

# Section for adding URLs to the queue
st.header("Add YouTube URL to Queue")
db_choice_add = st.selectbox("Select Database", ["Notion", "SQLite"], key="add_db")
url = st.text_input("Enter YouTube URL")

if st.button("Add to Queue"):
    if url:
        db = DBFactory.get_db(db_choice_add)
        db.add_task(url)
        st.success(f"Successfully added to queue: {url} using {db_choice_add}")
    else:
        st.error("Please enter a URL")

# Section for processing pending tasks
st.header("Process Pending Tasks")
if st.button("Process All Pending Tasks"):
    with st.spinner("Processing all pending tasks..."):
        process_pending_tasks()
    st.success("Finished processing all pending tasks.")

# Section for displaying tasks
st.header("Tasks in Database")
db_choice_view = st.selectbox("Select Database to View", ["Notion", "SQLite"], key="view_db")
db = DBFactory.get_db(db_choice_view)

tasks = db.get_all_tasks()

if not tasks:
    st.write("No tasks in the database.")
else:
    df = pd.DataFrame(tasks)
    st.table(df)
