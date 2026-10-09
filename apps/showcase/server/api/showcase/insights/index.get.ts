import { defineEventHandler, setHeader } from "h3";
import { insightETag, insightList } from "../../../utils/weekly-insights";

export default defineEventHandler((event) => {
  setHeader(event, "Cache-Control", "public, max-age=0, s-maxage=300, must-revalidate");
  setHeader(event, "ETag", insightETag);
  return insightList();
});
