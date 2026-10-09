import { defineEventHandler, setHeader, setResponseStatus } from "h3";
import { insightDetail, insightETag } from "../../../utils/weekly-insights";

export default defineEventHandler((event) => {
  const detail = insightDetail(String(event.context.params?.start || ""));
  if (!detail) {
    setHeader(event, "Cache-Control", "no-store");
    setResponseStatus(event, 404, "Weekly insight not found.");
    return { statusCode: 404, statusMessage: "Weekly insight not found." };
  }
  setHeader(event, "Cache-Control", "public, max-age=0, s-maxage=300, must-revalidate");
  setHeader(event, "ETag", insightETag);
  return detail;
});
