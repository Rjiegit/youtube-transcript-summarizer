import { CustomConverter } from "opencc-js/core";
import traditionalCharacters from "opencc-js/dict/TSCharacters";

// Use only the character dictionary: regional phrases and synonyms are not search aliases.
const simplifyCharacter = CustomConverter(traditionalCharacters);

export interface TitleSearchPart {
  text: string;
  matched: boolean;
}

export interface TitleSearchRange {
  start: number;
  end: number;
}

export interface SearchableTitle {
  normalized: string;
  originalStarts: number[];
  originalEnds: number[];
}

export function normalizeTitleSearch(query: string): string {
  return Array.from(query.trim(), simplifyCharacter).join("").toLowerCase();
}

export function prepareTitleSearch(title: string): SearchableTitle {
  const convertedCharacters: string[] = [];
  const originalStarts: number[] = [];
  const originalEnds: number[] = [];
  let originalOffset = 0;
  for (const character of title) {
    const converted = simplifyCharacter(character);
    convertedCharacters.push(converted);
    // Conversion can change UTF-16 length; lowercasing can also expand İ.
    // Every resulting unit points to the complete original code point.
    for (let index = 0; index < converted.toLowerCase().length; index += 1) {
      originalStarts.push(originalOffset);
      originalEnds.push(originalOffset + character.length);
    }
    originalOffset += character.length;
  }

  return {
    // Lowercase the whole string to preserve contextual casing (e.g. final sigma).
    normalized: convertedCharacters.join("").toLowerCase(),
    originalStarts,
    originalEnds,
  };
}

export function findTitleMatches(title: SearchableTitle, normalizedQuery: string): TitleSearchRange[] {
  if (!normalizedQuery) return [];

  const ranges: TitleSearchRange[] = [];
  let searchOffset = 0;
  while (searchOffset < title.normalized.length) {
    const index = title.normalized.indexOf(normalizedQuery, searchOffset);
    if (index < 0) break;
    const start = title.originalStarts[index];
    const end = title.originalEnds[index + normalizedQuery.length - 1];
    const previous = ranges[ranges.length - 1];
    if (previous && start < previous.end) {
      previous.end = Math.max(previous.end, end);
    } else {
      ranges.push({ start, end });
    }
    searchOffset = index + normalizedQuery.length;
  }
  return ranges;
}

export function splitTitleSearch(title: string, ranges: readonly TitleSearchRange[]): TitleSearchPart[] {
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
