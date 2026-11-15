import { defineEventHandler, setHeader, setResponseStatus } from "h3";
import { topicReadingDetail, insightETag } from "../../../utils/weekly-insights";

export default defineEventHandler((event) => {
  const detail = topicReadingDetail(String(event.context.params?.id || ""));
  if (!detail) {
    setHeader(event, "Cache-Control", "no-store");
    setResponseStatus(event, 404, "Topic reading not found.");
    return { statusCode: 404, statusMessage: "Topic reading not found." };
  }
  setHeader(event, "Cache-Control", "public, max-age=0, s-maxage=300, must-revalidate");
  setHeader(event, "ETag", insightETag);
  return detail;
});
