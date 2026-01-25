const DEFAULT_API_BASE_URL = "http://localhost:8080";
const MENU_ID_PAGE = "whisper-send-page";
const MENU_ID_LINK = "whisper-send-link";
const NOTIFY_TITLE = "Whisper Summary";
const BADGE_CLEAR_DELAY_MS = 5000;
const NOTIFICATION_DISMISS_DELAY_MS = 2000;

const YOUTUBE_PAGE_PATTERNS = [
  "*://*.youtube.com/watch*",
  "*://*.youtube.com/shorts*",
  "*://*.youtube.com/live*",
  "*://youtu.be/*"
];

const YOUTUBE_LINK_PATTERNS = [
  "*://*.youtube.com/watch*",
  "*://*.youtube.com/shorts*",
  "*://*.youtube.com/live*",
  "*://youtu.be/*"
];

function setBadge(text, color, title) {
  chrome.action.setBadgeBackgroundColor({ color });
  chrome.action.setBadgeText({ text });
  if (title) {
    chrome.action.setTitle({ title });
  }
  setTimeout(() => {
    chrome.action.setBadgeText({ text: "" });
  }, BADGE_CLEAR_DELAY_MS);
}

function notify(id, message, isSuccess) {
  const notificationId = `${id}-${Date.now()}`;
  const iconUrl = chrome.runtime.getURL("icon-128.png");
  chrome.notifications.create(notificationId, {
    type: "basic",
    iconUrl,
    title: NOTIFY_TITLE,
    message,
    priority: 2,
    requireInteraction: true,
    silent: false
  }, () => {
    if (chrome.runtime.lastError) {
      console.warn("Notification error:", chrome.runtime.lastError.message);
    }
  });
  setTimeout(() => {
    chrome.notifications.clear(notificationId);
  }, NOTIFICATION_DISMISS_DELAY_MS);
  const badgeText = isSuccess ? "OK" : "ERR";
  const badgeColor = isSuccess ? "#16a34a" : "#dc2626";
  setBadge(badgeText, badgeColor, message);
}

function normalizeBaseUrl(value) {
  if (!value) {
    return DEFAULT_API_BASE_URL;
  }
  return value.replace(/\/+$/, "");
}

function isValidYoutubeUrl(rawUrl) {
  if (!rawUrl) {
    return false;
  }

  let parsed;
  try {
    parsed = new URL(rawUrl);
  } catch (error) {
    return false;
  }

  const hostname = parsed.hostname.toLowerCase();
  const path = parsed.pathname || "";

  if (hostname.endsWith("youtube.com")) {
    if (path === "/watch") {
      return !!parsed.searchParams.get("v");
    }
    if (path.startsWith("/shorts/")) {
      return path.length > "/shorts/".length;
    }
    if (path.startsWith("/live/")) {
      return path.length > "/live/".length;
    }
    return false;
  }

  if (hostname === "youtu.be") {
    return path.length > 1;
  }

  return false;
}

async function getApiBaseUrl() {
  const result = await chrome.storage.sync.get({
    apiBaseUrl: DEFAULT_API_BASE_URL
  });
  return normalizeBaseUrl(result.apiBaseUrl);
}

async function sendTaskRequest(url) {
  if (!isValidYoutubeUrl(url)) {
    notify("whisper-invalid-url", "Invalid YouTube URL.", false);
    return;
  }

  const apiBaseUrl = await getApiBaseUrl();
  const endpoint = `${apiBaseUrl}/tasks`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url,
        db_type: "sqlite"
      }),
      signal: controller.signal
    });

    const data = await response.json().catch(() => ({}));

    if (response.status === 201) {
      const message = data.message || "Task queued.";
      notify("whisper-success", message, true);
      return;
    }

    const errorDetail = data.detail || data.message || `Request failed (${response.status}).`;
    notify("whisper-failure", errorDetail, false);
  } catch (error) {
    const message = error && error.name === "AbortError" ? "Request timed out." : "Request failed.";
    notify("whisper-error", message, false);
  } finally {
    clearTimeout(timeoutId);
  }
}

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: MENU_ID_PAGE,
    title: "Send YouTube to Whisper Summary",
    contexts: ["page"],
    documentUrlPatterns: YOUTUBE_PAGE_PATTERNS
  });

  chrome.contextMenus.create({
    id: MENU_ID_LINK,
    title: "Send YouTube link to Whisper Summary",
    contexts: ["link"],
    targetUrlPatterns: YOUTUBE_LINK_PATTERNS
  });
});

chrome.action.onClicked.addListener((tab) => {
  const url = tab && tab.url ? tab.url : "";
  sendTaskRequest(url);
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === MENU_ID_LINK) {
    sendTaskRequest(info.linkUrl || "");
    return;
  }

  if (info.menuItemId === MENU_ID_PAGE) {
    const url = tab && tab.url ? tab.url : "";
    sendTaskRequest(url);
  }
});
