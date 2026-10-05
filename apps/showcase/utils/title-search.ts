export interface TitleSearchPart {
  text: string;
  matched: boolean;
}

export function normalizeTitleSearch(query: string): string {
  return query.trim().toLowerCase();
}

export function splitTitleSearch(title: string, query: string): TitleSearchPart[] {
  const normalizedQuery = normalizeTitleSearch(query);
  const normalizedTitle = title.toLowerCase();
  if (!normalizedQuery || !normalizedTitle.includes(normalizedQuery)) {
    return [{ text: title, matched: false }];
  }

  // Lowercasing can expand a character (İ → i + combining dot). Map each
  // normalized UTF-16 position back to the complete original code point.
  const originalStarts: number[] = [];
  const originalEnds: number[] = [];
  let originalOffset = 0;
  for (const character of title) {
    for (let index = 0; index < character.toLowerCase().length; index += 1) {
      originalStarts.push(originalOffset);
      originalEnds.push(originalOffset + character.length);
    }
    originalOffset += character.length;
  }

  const ranges: { start: number; end: number }[] = [];
  let searchOffset = 0;
  while (searchOffset < normalizedTitle.length) {
    const index = normalizedTitle.indexOf(normalizedQuery, searchOffset);
    if (index < 0) break;
    const start = originalStarts[index];
    const end = originalEnds[index + normalizedQuery.length - 1];
    const previous = ranges[ranges.length - 1];
    if (previous && start < previous.end) {
      previous.end = Math.max(previous.end, end);
    } else {
      ranges.push({ start, end });
    }
    searchOffset = index + normalizedQuery.length;
  }

  const parts: TitleSearchPart[] = [];
  let cursor = 0;
  for (const { start, end } of ranges) {
    if (start > cursor) parts.push({ text: title.slice(cursor, start), matched: false });
    parts.push({ text: title.slice(start, end), matched: true });
    cursor = end;
  }
  if (cursor < title.length) parts.push({ text: title.slice(cursor), matched: false });
  return parts;
}
