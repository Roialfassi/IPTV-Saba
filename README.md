# IPTV App

A simple IPTV streaming application with profile management and easy mode for elderly users.

## Features

- **Multiple User Profiles**: Create and manage different profiles with separate M3U playlists
- **Channel Management**: Browse, favorite, and organize channels
- **Easy Mode**: Simplified interface showing only favorite channels for elderly users
- **Full-Screen Playback**: Comfortable viewing experience with essential playback controls
- **Profile Favorites & History**: Mark channels as favorites, keep track of recently watched channels, and persist data between sessions.


## Requirements

- Python 3.8+
- VLC Media Player installed on your system
- Internet connection

## Installation

1. Clone this repository
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Start the application by running:

```bash
cd src
python iptv_app.py
```

### First-time Setup

1. On the login screen, select "Create New Profile"
2. Enter a profile name
3. Provide your M3U playlist URL
4. Select your new profile to start watching

### Navigation

- **Login Screen**: Select existing profile or create a new one
- **Channel Selection**: Browse channels, mark favorites, filter by category
- **Full-Screen Player**: Watch content with playback controls

### Easy Mode for Elderly Users

Enable Easy Mode from the profile settings to show only favorite channels, simplifying navigation for elderly users.

### Usage Tips
- After launching, you will start at the Login Screen where you can select an existing profile or create a new one.
- Easy Mode is particularly useful for those who just want to watch their favorites without navigating through the entire channel list. It starts playing your first favorite channel and only cycles through favorites using next/previous.
- You can manage your channels, add/remove favorites, and view history through the Channel Selection Screen.
- The Full Screen Player offers a richer experience with more controls, EPG data (if configured), and advanced playback options.

## Troubleshooting

- **Playback Issues**: Ensure VLC is properly installed and your M3U link is valid
- **Stream Buffering**: Check your internet connection speed
- **Missing Channels**: Verify your M3U playlist is up-to-date


