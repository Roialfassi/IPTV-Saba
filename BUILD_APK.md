# Building the Android APK

## Fixed Build Issues

The pyjnius build error has been resolved by:
1. **Removed pyjnius and plyer** from requirements (they were causing build failures)
2. **Made download/record features optional** - they won't show in the app but core functionality works
3. **Simplified requirements** to only what's needed for basic app functionality

## Clean Build Steps (WSL/Linux)

```bash
cd ~/IPTV-Saba

# Step 1: Clean all buildozer caches (important!)
rm -rf .buildozer/
rm -rf ~/.buildozer/

# Step 2: Make sure you're on the correct branch
git status
# Should show: claude/android-app-conversion-011CUsFXJuNkkTuUgr5uaMXD

# Step 3: Pull latest changes
git pull origin claude/android-app-conversion-011CUsFXJuNkkTuUgr5uaMXD

# Step 4: Build the APK (this will take 15-30 minutes first time)
buildozer -v android debug

# The APK will be created in:
# bin/iptvsaba-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

## If Build Still Fails

### Install Missing System Dependencies

```bash
# Update package list
sudo apt-get update

# Install all required build tools
sudo apt-get install -y \
    git zip unzip openjdk-17-jdk python3-pip \
    autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev \
    build-essential libltdl-dev libffi-dev \
    libssl-dev ccache
```

### Check Your Environment

```bash
# Verify NDK is set
echo $ANDROID_NDK_HOME
# Should show: /home/roi11/Android/ndk/android-ndk-r25b

# Verify it exists
ls $ANDROID_NDK_HOME
# Should list NDK files

# Check Java version
java -version
# Should show Java 17 or higher

# Check Python version
python3 --version
# Should show Python 3.8 or higher
```

## What's Included in the APK

### ✓ Working Features
- Login screen with profile management
- Channel browsing and selection
- Group filtering
- Favorites management
- Video playback (native Android MediaPlayer)
- Profile auto-login
- Channel history
- Fullscreen video player with controls

### ✗ Disabled Features (due to pyjnius removal)
- Download channel feature
- Record channel feature
- Downloads list

These can be added back later when pyjnius build issues are resolved.

## Installing the APK

### On Your Android Device

1. **Copy APK to phone**:
```bash
# In WSL, find the APK
ls ~/IPTV-Saba/bin/*.apk

# If you have adb installed:
adb install ~/IPTV-Saba/bin/iptvsaba-1.0.0-arm64-v8a_armeabi-v7a-debug.apk
```

2. **Or manually**:
   - Copy `~/IPTV-Saba/bin/iptvsaba-1.0.0-*.apk` to your phone
   - Open file manager on phone
   - Tap the APK file
   - Allow "Install from unknown sources" if prompted
   - Install

3. **Grant Permissions**:
   - Storage (for saving profiles)
   - Network (for streaming)

## Testing the APK

1. Open the IPTV Saba app
2. Create a new profile with an M3U URL
3. Select the profile to load channels
4. Browse channels and groups
5. Add channels to favorites
6. Play a channel in fullscreen
7. Test video controls (play/pause, volume, back)

## Troubleshooting

### Build hangs or takes too long
- Be patient - first build takes 15-30 minutes
- Subsequent builds are much faster (5-10 minutes)

### "Command failed" error
- Check the error in the output
- Make sure all dependencies are installed
- Try clean build: `rm -rf .buildozer/ ~/.buildozer/`

### APK installs but crashes
- Check Android version (need Android 5.0 or higher)
- Check logcat: `adb logcat | grep python`
- Make sure permissions are granted

### Video doesn't play
- Test the M3U URL in VLC first
- Check internet connection
- Some streams may not work on Android

## Build Time Expectations

| Build Type | Time |
|------------|------|
| First build (clean) | 15-30 minutes |
| Rebuild after code change | 5-10 minutes |
| Rebuild after clean | 15-30 minutes |

## APK Size

Expected APK size: 30-50 MB

## Next Steps After Successful Build

1. Test all features on Android device
2. Fix any crashes or bugs
3. Add app icon and splash screen
4. Prepare for release build (signed APK)
5. Eventually re-add pyjnius for download/record features

## Adding Back Download/Record Features Later

When pyjnius build issues are resolved:

```ini
# In buildozer.spec
requirements = python3,kivy,pillow,requests,aiohttp,chardet,pyyaml,python-dateutil,android,pyjnius,plyer
```

The code is already set up to enable these features automatically when pyjnius is available.
