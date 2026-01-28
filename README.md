# TTS App - Installation Guide

A modern Text-to-Speech application with multiple voice options, dual audio output support, volume boost, and soundboard functionality.

## Prerequisites

### 1. Install Python
Download and install Python 3.8 or higher from:
- **Official Python Website**: [https://www.python.org/downloads/](https://www.python.org/downloads/)
- During installation, make sure to check "Add Python to PATH"

### 2. Verify Python Installation
Open Command Prompt (Windows) or Terminal (Mac/Linux) and run:
```bash
python --version
```
You should see something like `Python 3.12.x`

## Installation Steps

### 1. Download the TTS App
- Download `tts.py` from this repository
- Save it to a folder of your choice (e.g., `C:\Users\YourName\Downloads\tts\`)

### 2. Install Required Libraries
Open Command Prompt or Terminal in the folder where you saved `tts.py` and run these commands:

```bash
pip install sounddevice soundfile edge-tts pynput
```

**Note**: If `tkinter` gives an error, it's likely already included with Python. Just ignore and continue.

### 3. Run the Application
In the same terminal window, run:
```bash
python tts.py
```

The TTS App window should now open!

## Setup & Configuration

### Basic Setup

1. **Click the "Options" button** in the main window

2. **Select Your Voice**
   - Choose from 15 different voices
   - Options include US, UK, Australian, Canadian, and Indian accents
   - Both male and female voices available

3. **Select Output Device 1**
   - Choose your primary audio output (speakers/headphones)
   - This is where the TTS audio will play

4. **Select Output Device 2 (Optional)**
   - Leave as "None" if you only need one output
   - See "Virtual Cable Setup" below for advanced routing

5. **Adjust Volume (0-200%)**
   - Default is 100% (normal volume)
   - Can boost up to 200% for extra loudness
   - Below 100% reduces volume

6. **Click "Back"** to return to the main screen

### Virtual Cable Setup (Optional)

If you want to route TTS audio to your microphone (for Discord, OBS, etc.):

#### Install VB-Audio Virtual Cable
1. Download VB-CABLE from: [https://vb-audio.com/Cable/](https://vb-audio.com/Cable/)
2. Extract the zip file
3. Right-click `VBCABLE_Setup_x64.exe` (or x86 for 32-bit) and select "Run as Administrator"
4. Follow the installation prompts
5. Restart your computer

#### Configure TTS App with Virtual Cable
1. Open TTS App and go to **Options**
2. **Output Device 1**: Select your speakers/headphones (so you can hear it)
3. **Output Device 2**: Select "CABLE Input (VB-Audio Virtual Cable)"
4. Click **Back**

#### Configure Your Application (Discord, OBS, etc.)
- Set your microphone input to "CABLE Output (VB-Audio Virtual Cable)"
- Now TTS audio will play through both your speakers AND appear as microphone input!

## Features

### Volume Control
- Adjust volume from 0% to 200% using the slider on the main page
- 100% is default/normal volume
- Volume settings are saved automatically

### Dark Mode
- Go to **Options** and check **Dark Mode**
- Easy on the eyes for night use

### Stay on Top
- Go to **Options** and check **Stay on Top**
- Keeps the TTS window above other applications

### Soundboard
Access via **Options** → **Soundboard**

The soundboard allows you to assign global hotkeys to your TTS phrases for instant playback:

1. **Generate TTS audio first** - Type text and press Play to create cached audio files
2. **Open Soundboard** - Go to Options → Soundboard
3. **Assign Hotkeys**:
   - Select a sound from the list
   - Click "Assign Key"
   - Press any key (F1-F12, letters, numbers, etc.)
   - Press ESC to remove a hotkey
4. **Use Globally** - Hotkeys work even when the app is minimized or you're in other programs

**Soundboard Features:**
- Global hotkeys (work system-wide)
- Automatically stops current sound when playing a new one
- Works through both selected output devices
- Cached files named as: `text-VoiceNameGenderCountry.mp3`

### Settings Persistence
- All your settings (voice, outputs, volume, theme) are automatically saved to `tts_settings.ini`
- Soundboard bindings are saved to `soundboard.json`
- Settings are restored when you restart the app

## Cache System

The app automatically caches generated audio for faster playback:
- **First time playing text**: 2-3 seconds (downloads from Microsoft servers)
- **Playing same text again**: < 0.5 seconds (instant from cache)
- Cache is stored in the `tts_cache` folder next to the app
- Files are named descriptively: `hello-JennyFemaleUS.mp3`
- You can delete this folder to clear the cache if needed

## Usage

### Basic TTS
1. Type or paste your text in the text box
2. Adjust volume slider if needed (0-200%)
3. Click **Play** to hear it
4. Click **Stop** to stop playback at any time
5. The progress bar shows playback progress

### Soundboard Usage
1. Create TTS phrases you want to use frequently
2. Go to Options → Soundboard
3. Assign hotkeys to your favorite phrases
4. Use hotkeys anywhere on your system for instant playback

## Troubleshooting

### "No module named 'X'" Error
Run the installation command again:
```bash
pip install sounddevice soundfile edge-tts pynput
```

### No Audio Playing
1. Check your audio device settings in **Options**
2. Make sure your speakers/headphones are set as the default device
3. Try selecting a different output device

### Volume Too Quiet
1. Increase the volume slider above 100%
2. Can go up to 200% for extra boost
3. Check your system volume is also turned up

### Voice Doesn't Work
Some voices may occasionally fail. Try:
1. Selecting a different voice (Jenny and Guy are most reliable)
2. Checking your internet connection (needed for first-time generation)
3. Restarting the app

### Hotkeys Not Working
1. Make sure the app is running (can be minimized)
2. Try reassigning the hotkey
3. Avoid keys that conflict with system shortcuts (Ctrl, Alt combinations)
4. Run the app as administrator if needed

### Error Opening OutputStream
This happens when output devices have different channel configurations:
1. Try using only one output device
2. Restart the application
3. Check that both devices are working properly in Windows sound settings

### App Won't Start
1. Make sure Python is installed correctly
2. Try running from Command Prompt to see error messages:
   ```bash
   python tts.py
   ```
3. Reinstall dependencies

## File Structure

After running the app, you'll have:
```
your-folder/
├── tts.py                  (main application)
├── README.md               (this file)
├── tts_settings.ini        (saved settings)
├── soundboard.json         (hotkey bindings)
└── tts_cache/              (cached audio files)
    ├── hello-JennyFemaleUS.mp3
    ├── goodbye-GuyMaleUS.mp3
    └── ...
```

## Notes

- **Internet Required**: First time generating a phrase requires internet connection
- **Cached Audio**: Previously generated phrases play instantly offline
- **Multiple Voices**: Try different voices to find your favorite
- **Dual Output**: Use both outputs to play audio in two places simultaneously
- **Global Hotkeys**: Soundboard works even when app is in background
- **Volume Boost**: Can amplify audio up to 2x normal volume (200%)

## Need Help?

If you encounter any issues:
1. Check the console/terminal for error messages
2. Make sure all dependencies are installed
3. Try restarting the application
4. Ensure you have an active internet connection for new phrases
5. Check that your audio devices are working properly

**Enjoy your TTS App!**