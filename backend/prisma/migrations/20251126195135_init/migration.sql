-- CreateTable
CREATE TABLE "profiles" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "avatar" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "settings" TEXT NOT NULL DEFAULT '{}',
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);

-- CreateTable
CREATE TABLE "M3USource" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "url" TEXT NOT NULL,
    "name" TEXT,
    "lastFetched" DATETIME,
    "lastStatus" TEXT,
    "totalEntries" INTEGER NOT NULL DEFAULT 0,
    "profileId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "M3USource_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Channel" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "tvgId" TEXT,
    "tvgName" TEXT NOT NULL,
    "displayName" TEXT NOT NULL,
    "logo" TEXT,
    "url" TEXT NOT NULL,
    "groupTitle" TEXT NOT NULL,
    "contentType" TEXT NOT NULL,
    "metadata" TEXT NOT NULL DEFAULT '{}',
    "profileId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Channel_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Series" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "normalizedName" TEXT NOT NULL,
    "logo" TEXT,
    "groupTitle" TEXT NOT NULL,
    "profileId" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "Series_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "Episode" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "seriesId" TEXT NOT NULL,
    "seasonNumber" INTEGER NOT NULL,
    "episodeNumber" INTEGER NOT NULL,
    "title" TEXT,
    "url" TEXT NOT NULL,
    "tvgName" TEXT NOT NULL,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Episode_seriesId_fkey" FOREIGN KEY ("seriesId") REFERENCES "Series" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "favorites" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "profileId" TEXT NOT NULL,
    "contentType" TEXT NOT NULL,
    "contentId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "logo" TEXT,
    "url" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "favorites_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "watch_history" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "profileId" TEXT NOT NULL,
    "contentType" TEXT NOT NULL,
    "contentId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "logo" TEXT,
    "url" TEXT NOT NULL,
    "seriesId" TEXT,
    "seriesName" TEXT,
    "seasonNumber" INTEGER,
    "episodeNumber" INTEGER,
    "watchedAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "progress" INTEGER NOT NULL DEFAULT 0,
    "duration" INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT "watch_history_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "downloads" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "profileId" TEXT NOT NULL,
    "contentType" TEXT NOT NULL,
    "contentId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "logo" TEXT,
    "url" TEXT NOT NULL,
    "seriesId" TEXT,
    "seriesName" TEXT,
    "seasonNumber" INTEGER,
    "episodeNumber" INTEGER,
    "status" TEXT NOT NULL,
    "progress" REAL NOT NULL DEFAULT 0,
    "fileSize" BIGINT NOT NULL DEFAULT 0,
    "downloadedSize" BIGINT NOT NULL DEFAULT 0,
    "filePath" TEXT,
    "error" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    "completedAt" DATETIME,
    CONSTRAINT "downloads_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "search_history" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "profileId" TEXT NOT NULL,
    "query" TEXT NOT NULL,
    "filters" TEXT,
    "resultCount" INTEGER NOT NULL DEFAULT 0,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "search_history_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateTable
CREATE TABLE "profile_settings" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "profileId" TEXT NOT NULL,
    "autoplay" BOOLEAN NOT NULL DEFAULT true,
    "defaultQuality" TEXT NOT NULL DEFAULT 'auto',
    "skipIntroSeconds" INTEGER NOT NULL DEFAULT 0,
    "defaultVolume" INTEGER NOT NULL DEFAULT 80,
    "subtitlesEnabled" BOOLEAN NOT NULL DEFAULT false,
    "subtitlesLanguage" TEXT NOT NULL DEFAULT 'en',
    "theme" TEXT NOT NULL DEFAULT 'dark',
    "accentColor" TEXT NOT NULL DEFAULT '#3b82f6',
    "compactMode" BOOLEAN NOT NULL DEFAULT false,
    "showEPG" BOOLEAN NOT NULL DEFAULT true,
    "gridSize" TEXT NOT NULL DEFAULT 'medium',
    "contentLanguage" TEXT NOT NULL DEFAULT 'en',
    "ageRating" TEXT NOT NULL DEFAULT 'all',
    "hideAdultContent" BOOLEAN NOT NULL DEFAULT false,
    "cacheEnabled" BOOLEAN NOT NULL DEFAULT true,
    "cacheSize" INTEGER NOT NULL DEFAULT 500,
    "downloadQuality" TEXT NOT NULL DEFAULT '720p',
    "wifiOnlyDownloads" BOOLEAN NOT NULL DEFAULT true,
    "reminderEnabled" BOOLEAN NOT NULL DEFAULT true,
    "reminderMinutes" INTEGER NOT NULL DEFAULT 5,
    "newContentAlert" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL,
    CONSTRAINT "profile_settings_profileId_fkey" FOREIGN KEY ("profileId") REFERENCES "profiles" ("id") ON DELETE CASCADE ON UPDATE CASCADE
);

-- CreateIndex
CREATE INDEX "profiles_isActive_idx" ON "profiles"("isActive");

-- CreateIndex
CREATE INDEX "M3USource_profileId_idx" ON "M3USource"("profileId");

-- CreateIndex
CREATE INDEX "M3USource_lastFetched_idx" ON "M3USource"("lastFetched");

-- CreateIndex
CREATE INDEX "Channel_profileId_contentType_idx" ON "Channel"("profileId", "contentType");

-- CreateIndex
CREATE INDEX "Channel_groupTitle_idx" ON "Channel"("groupTitle");

-- CreateIndex
CREATE INDEX "Channel_tvgId_idx" ON "Channel"("tvgId");

-- CreateIndex
CREATE INDEX "Series_profileId_idx" ON "Series"("profileId");

-- CreateIndex
CREATE UNIQUE INDEX "Series_normalizedName_profileId_key" ON "Series"("normalizedName", "profileId");

-- CreateIndex
CREATE INDEX "Episode_seriesId_idx" ON "Episode"("seriesId");

-- CreateIndex
CREATE UNIQUE INDEX "Episode_seriesId_seasonNumber_episodeNumber_key" ON "Episode"("seriesId", "seasonNumber", "episodeNumber");

-- CreateIndex
CREATE INDEX "favorites_profileId_contentType_idx" ON "favorites"("profileId", "contentType");

-- CreateIndex
CREATE INDEX "favorites_createdAt_idx" ON "favorites"("createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "favorites_profileId_contentType_contentId_key" ON "favorites"("profileId", "contentType", "contentId");

-- CreateIndex
CREATE INDEX "watch_history_profileId_watchedAt_idx" ON "watch_history"("profileId", "watchedAt");

-- CreateIndex
CREATE UNIQUE INDEX "watch_history_profileId_contentType_contentId_key" ON "watch_history"("profileId", "contentType", "contentId");

-- CreateIndex
CREATE INDEX "downloads_profileId_status_idx" ON "downloads"("profileId", "status");

-- CreateIndex
CREATE UNIQUE INDEX "downloads_profileId_contentType_contentId_key" ON "downloads"("profileId", "contentType", "contentId");

-- CreateIndex
CREATE INDEX "search_history_profileId_createdAt_idx" ON "search_history"("profileId", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "profile_settings_profileId_key" ON "profile_settings"("profileId");
