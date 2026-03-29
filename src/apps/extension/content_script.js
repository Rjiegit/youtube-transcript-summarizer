function extractChannelIdFromDom() {
  const metaChannel = document.querySelector('meta[itemprop="channelId"]');
  if (metaChannel && metaChannel.content) {
    return metaChannel.content.trim();
  }

  const rssLink = document.querySelector(
    'link[rel="alternate"][type="application/rss+xml"]'
  );
  if (rssLink && rssLink.href) {
    try {
      const parsed = new URL(rssLink.href);
      const channelId = parsed.searchParams.get("channel_id");
      if (channelId) {
        return channelId.trim();
      }
    } catch (error) {
      return "";
    }
  }

  return "";
}

function extractChannelTitle(channelId) {
  const ogTitle = document.querySelector('meta[property="og:title"]');
  if (ogTitle && ogTitle.content) {
    const value = ogTitle.content.trim();
    if (value) {
      return value;
    }
  }

  const metaTitle = document.querySelector('meta[name="title"]');
  if (metaTitle && metaTitle.content) {
    const value = metaTitle.content.trim();
    if (value) {
      return value;
    }
  }

  const pageHeader = document.querySelector(
    'ytd-channel-name yt-formatted-string, #channel-name yt-formatted-string, h1.ytd-c4-tabbed-header-renderer'
  );
  if (pageHeader && pageHeader.textContent) {
    const value = pageHeader.textContent.trim();
    if (value) {
      return value;
    }
  }

  return channelId || "";
}

function detectPageType() {
  const { pathname } = window.location;
  if (pathname.startsWith("/channel/") || pathname.startsWith("/@")) {
    return "channel";
  }
  if (
    pathname === "/watch" ||
    pathname.startsWith("/shorts/") ||
    pathname.startsWith("/live/")
  ) {
    return "video";
  }
  return "unknown";
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || message.type !== "WHISPER_GET_CHANNEL_CONTEXT") {
    return false;
  }

  const channelId = extractChannelIdFromDom();
  sendResponse({
    channelId,
    channelTitle: extractChannelTitle(channelId),
    pageType: detectPageType()
  });
  return false;
});
