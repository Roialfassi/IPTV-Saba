# 📋 IPTV Application System Checkpoint

## Pre-Launch Checklist

### ✅ Backend Health
- [ ] Database connection established
- [ ] All migrations run successfully
- [ ] Seed data loaded (if applicable)
- [ ] Environment variables configured
- [ ] Server starts without errors on port 3000
- [ ] Health endpoint responds: GET /health

### ✅ Frontend Health
- [ ] Development server starts on port 5173
- [ ] No console errors on load
- [ ] All routes render correctly
- [ ] API connection established

### ✅ Core Functionality

#### Profile Management
- [ ] Create new profile
- [ ] Switch between profiles
- [ ] Update profile information
- [ ] Delete profile (with confirmation)
- [ ] Profile stats display correctly

#### M3U Source Management
- [ ] Add M3U source URL
- [ ] Trigger sync manually
- [ ] View sync status
- [ ] Parse test M3U: https://iptv-org.github.io/iptv/countries/il.m3u
- [ ] Parse provided Croatian sample
- [ ] Parse provided Turkish series sample
- [ ] Parse provided Arabic movies sample
- [ ] Content appears after successful sync

#### Content Browsing
- [ ] Channels page loads with content
- [ ] Movies page loads with content
- [ ] Series page loads with content
- [ ] Series detail page shows episodes
- [ ] Pagination works correctly
- [ ] Filters work (by group, year, etc.)
- [ ] Search functionality works

#### Video Playback
- [ ] Click channel plays stream
- [ ] Click movie plays stream
- [ ] Click episode plays stream
- [ ] Video player controls work
- [ ] Volume control works
- [ ] Fullscreen works
- [ ] Close player stops stream
- [ ] HLS streams (.m3u8) play correctly

#### Favorites
- [ ] Add item to favorites
- [ ] Remove from favorites
- [ ] View favorites page
- [ ] Favorites persist after refresh

#### Watch History
- [ ] Continue watching appears on home
- [ ] Progress bar displays correctly
- [ ] Resume from last position works
- [ ] History page shows all watched items

### ✅ Performance Checks
- [ ] Channels page with 100+ items: < 2s load
- [ ] Search returns results: < 1s
- [ ] M3U sync (1000 entries): < 10s
- [ ] Database queries: < 100ms average
- [ ] Page navigation: < 500ms

### ✅ Error Handling
- [ ] Invalid M3U URL shows error
- [ ] Network error shows user-friendly message
- [ ] Missing content returns 404
- [ ] Invalid profile ID handled
- [ ] Malformed M3U parsed gracefully

### ✅ UI/UX
- [ ] Responsive on mobile (375px)
- [ ] Responsive on tablet (768px)
- [ ] Responsive on desktop (1920px)
- [ ] Loading states shown
- [ ] Empty states shown appropriately
- [ ] Buttons have hover effects
- [ ] Forms validate input
- [ ] Error messages are clear

### ✅ Data Persistence
- [ ] Favorites survive page refresh
- [ ] Watch history survives page refresh
- [ ] Profile selection persists
- [ ] Settings persist
- [ ] Downloaded content accessible offline

## 🧪 Test Scenarios

### Scenario 1: New User Onboarding
1. Open application (no profiles)
2. Create first profile
3. Add M3U source (Israel URL)
4. Wait for sync to complete
5. Browse channels
6. Play a channel
7. Add to favorites
8. Verify favorites page

**Expected:** Smooth flow, no errors, content playable

### Scenario 2: Multi-Profile Usage
1. Create Profile A and Profile B
2. Add different M3U sources to each
3. Switch between profiles
4. Verify content is profile-specific
5. Add favorites in Profile A
6. Switch to Profile B
7. Verify favorites don't show up

**Expected:** Complete data isolation between profiles

### Scenario 3: Large M3U Handling
1. Add M3U with 5000+ entries
2. Monitor sync progress
3. Verify all categories populated
4. Test search across large dataset
5. Test filtering
6. Check pagination

**Expected:** No crashes, acceptable performance

### Scenario 4: Network Failure Recovery
1. Start M3U sync
2. Disconnect network mid-sync
3. Observe error handling
4. Reconnect network
5. Retry sync
6. Verify partial data handled correctly

**Expected:** Graceful failure, successful retry

### Scenario 5: Video Playback
1. Play live channel (HLS stream)
2. Verify buffering is minimal
3. Test pause/resume
4. Test seek (if VOD)
5. Test volume
6. Test fullscreen
7. Switch to different content

**Expected:** Smooth playback, no freezing

## 🔍 Debug Commands

### Check Database
```bash
# Connect to database
npx prisma studio

# Run migrations
npx prisma migrate dev

# View logs
tail -f logs/app.log
```

### Check API
```bash
# Health check
curl http://localhost:3000/health

# Get profiles
curl http://localhost:3000/api/v1/profiles

# Test M3U parse
curl -X POST http://localhost:3000/api/v1/test/parse-m3u \
  -H "Content-Type: application/json" \
  -d '{"url":"https://iptv-org.github.io/iptv/countries/il.m3u"}'
```

### Performance Monitoring
```bash
# Monitor memory
node --expose-gc server.js

# Monitor database
npx prisma studio
# Check "Metrics" tab
```

## ✅ Sign-Off

When all checkpoints pass:
- [ ] Backend tests pass
- [ ] Frontend tests pass
- [ ] Manual testing complete
- [ ] Performance acceptable
- [ ] No critical bugs
- [ ] Documentation updated

**System Status:** ⚪ Not Started | 🟡 In Progress | 🟢 Ready

---

**Tester Name:** _______________
**Date:** _______________
**Version:** _______________
**Notes:** _______________
