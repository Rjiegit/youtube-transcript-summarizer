const DEFAULT_API_BASE_URL = "http://localhost:8080";

function setStatus(message, isError) {
  const statusEl = document.getElementById("status");
  statusEl.textContent = message;
  statusEl.classList.toggle("error", Boolean(isError));
}

function isValidBaseUrl(value) {
  if (!value) {
    return false;
  }
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch (error) {
    return false;
  }
}

async function restoreOptions() {
  const result = await chrome.storage.sync.get({
    apiBaseUrl: DEFAULT_API_BASE_URL
  });
  const input = document.getElementById("apiBaseUrl");
  input.value = result.apiBaseUrl || DEFAULT_API_BASE_URL;
}

async function saveOptions() {
  const input = document.getElementById("apiBaseUrl");
  const value = input.value.trim();

  if (!isValidBaseUrl(value)) {
    setStatus("Please enter a valid http/https URL.", true);
    return;
  }

  await chrome.storage.sync.set({ apiBaseUrl: value });
  setStatus("Saved.");
}

document.addEventListener("DOMContentLoaded", () => {
  restoreOptions();

  document.getElementById("saveButton").addEventListener("click", () => {
    saveOptions();
  });
});
