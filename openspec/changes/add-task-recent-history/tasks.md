## 1. Implementation
- [x] 1.1 Define a session-based recent history structure for viewed tasks
- [x] 1.2 Update Streamlit UI to append/move tasks into recent history when viewing details, including Notion URL data
- [x] 1.3 Mark viewed tasks in the task list based on recent history data
- [x] 1.4 Keep ordering stable (most recent first) and deduplicate entries
- [x] 1.5 Add minimal tests or helper-level checks if new utilities are extracted
- [x] 1.6 Record task access when Notion link is clicked (including opening in a new window)
- [x] 1.7 Persist recent history across refreshes with a 30-day TTL

## 2. Validation
- [ ] 2.1 Manually verify recent history updates after clicking View and survives browser refresh
- [ ] 2.2 Confirm recent history ordering (most recent first) and no duplicate entries
