export interface M3UEntry {
    id: string; // generated UUID
    tvgId: string;
    tvgName: string;
    tvgLogo: string;
    groupTitle: string;
    displayName: string;
    url: string;
    rawMetadata: string;
}

export interface ParsedM3U {
    sourceUrl: string;
    entries: M3UEntry[];
    parsedAt: Date;
    totalEntries: number;
    errors: ParseError[];
}

export interface ParseError {
    line: number;
    content: string;
    reason: string;
}
