import tkinter as tk
from tkinter import ttk
import threading
import sounddevice as sd
import soundfile as sf
import tempfile
import os
import time
import configparser
import hashlib
import json
from pynput import keyboard

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS App")
        self.root.geometry("450x450")
        self.root.resizable(False, False)
        
        # Config file path
        self.config_file = "tts_settings.ini"
        self.soundboard_file = "soundboard.json"
        
        # Cache directory for audio files
        self.cache_dir = "tts_cache"
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
        
        # Available voices using edge-tts API compatible voices (tested and working)
        self.voices = [
            {"name": "🇺🇸 Jenny (Female, US)", "voice": "en-US-JennyNeural"},
            {"name": "🇺🇸 Guy (Male, US)", "voice": "en-US-GuyNeural"},
            {"name": "🇺🇸 Aria (Female, US)", "voice": "en-US-AriaNeural"},
            {"name": "🇺🇸 Eric (Male, US)", "voice": "en-US-EricNeural"},
            {"name": "🇺🇸 Michelle (Female, US)", "voice": "en-US-MichelleNeural"},
            {"name": "🇺🇸 Roger (Male, US)", "voice": "en-US-RogerNeural"},
            {"name": "🇬🇧 Sonia (Female, UK)", "voice": "en-GB-SoniaNeural"},
            {"name": "🇬🇧 Ryan (Male, UK)", "voice": "en-GB-RyanNeural"},
            {"name": "🇬🇧 Libby (Female, UK)", "voice": "en-GB-LibbyNeural"},
            {"name": "🇦🇺 Natasha (Female, AU)", "voice": "en-AU-NatashaNeural"},
            {"name": "🇦🇺 William (Male, AU)", "voice": "en-AU-WilliamNeural"},
            {"name": "🇨🇦 Clara (Female, CA)", "voice": "en-CA-ClaraNeural"},
            {"name": "🇨🇦 Liam (Male, CA)", "voice": "en-CA-LiamNeural"},
            {"name": "🇮🇳 Neerja (Female, IN)", "voice": "en-IN-NeerjaNeural"},
            {"name": "🇮🇳 Prabhat (Male, IN)", "voice": "en-IN-PrabhatNeural"},
        ]
        
        self.audio_devices = sd.query_devices()
        
        # Playback control
        self.is_playing = False
        self.volume = tk.DoubleVar(value=1.0)  # 0.0 to 2.0
        self.volume_percent = None  # Will be set in create_main_frame
        
        # Soundboard
        self.soundboard_bindings = {}  # {hotkey: filepath}
        self.hotkey_listener = None
        self.load_soundboard()
        
        # Dark mode state
        self.dark_mode = tk.BooleanVar(value=False)
        self.stay_var = tk.BooleanVar(value=False)
        
        # Color schemes
        self.light_colors = {
            'bg': '#f0f0f0',
            'fg': '#000000',
            'button_bg': '#ffffff',
            'button_fg': '#000000',
            'entry_bg': '#ffffff',
            'entry_fg': '#000000',
            'accent': '#0078d4',
            'hover': '#e5e5e5'
        }
        
        self.dark_colors = {
            'bg': '#1e1e1e',
            'fg': '#ffffff',
            'button_bg': '#2d2d2d',
            'button_fg': '#ffffff',
            'entry_bg': '#2d2d2d',
            'entry_fg': '#ffffff',
            'accent': '#0078d4',
            'hover': '#3d3d3d'
        }
        
        # Create frames
        self.create_main_frame()
        self.create_options_frame()
        self.create_soundboard_frame()
        
        # Load settings
        self.load_settings()
        
        # Apply initial theme
        self.apply_theme()
        
        # Show main frame
        self.main_frame.pack(fill='both', expand=True)
        
        # Start global hotkey listener
        self.start_hotkey_listener()
        
        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def sanitize_filename(self, text):
        """Create safe filename from text"""
        # Remove or replace invalid filename characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '')
        # Limit length
        text = text[:50]
        return text.strip()
    
    def get_voice_short_name(self, voice_name):
        """Extract a readable short name from voice ID"""
        # voice_name format: "en-US-JennyNeural"
        parts = voice_name.split('-')
        if len(parts) >= 3:
            country = parts[1]  # "US"
            name = parts[2].replace('Neural', '')  # "Jenny"
            
            # Find the full voice info to get gender
            for voice in self.voices:
                if voice['voice'] == voice_name:
                    voice_display = voice['name']
                    if 'Female' in voice_display:
                        gender = 'Female'
                    elif 'Male' in voice_display:
                        gender = 'Male'
                    else:
                        gender = ''
                    return f"{name}{gender}{country}"
        
        return "Voice"
    
    def generate_speech_edgetts(self, text, voice_name):
        """Generate speech using edge-tts with caching and readable filenames"""
        import edge_tts
        import asyncio
        
        # Create readable filename with voice info
        safe_text = self.sanitize_filename(text)
        voice_short = self.get_voice_short_name(voice_name)
        filename = f"{safe_text}-{voice_short}.mp3"
        cache_file = os.path.join(self.cache_dir, filename)
        
        # Check if we have a cached version
        if os.path.exists(cache_file):
            print(f"Using cached audio: {filename}")
            return cache_file
        
        # Generate new audio
        async def _generate():
            communicate = edge_tts.Communicate(text, voice_name)
            await communicate.save(cache_file)
        
        # Run async function
        asyncio.run(_generate())
        return cache_file
    
    def get_colors(self):
        return self.dark_colors if self.dark_mode.get() else self.light_colors
    
    def create_main_frame(self):
        self.main_frame = tk.Frame(self.root)
        
        # Title
        title_label = tk.Label(
            self.main_frame, 
            text="🔊 Text to Speech",
            font=('Segoe UI', 16, 'bold')
        )
        title_label.pack(pady=(15, 10))
        
        # Text input label
        text_label = tk.Label(
            self.main_frame,
            text="Enter text to speak:",
            font=('Segoe UI', 10)
        )
        text_label.pack(pady=(5, 5), padx=20, anchor='w')
        
        # Text box with frame for border effect
        text_frame = tk.Frame(self.main_frame)
        text_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        self.text_box = tk.Text(
            text_frame, 
            height=6, 
            wrap='word',
            font=('Segoe UI', 10),
            relief='flat',
            borderwidth=2
        )
        self.text_box.pack(fill='x', padx=2, pady=2)
        
        # Progress bar
        self.progress_var = tk.IntVar()
        style = ttk.Style()
        style.theme_use('clam')
        
        self.progress = ttk.Progressbar(
            self.main_frame, 
            maximum=100, 
            variable=self.progress_var,
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress.pack(fill='x', padx=20, pady=(0, 10))
        
        # Control buttons frame
        control_frame = tk.Frame(self.main_frame)
        control_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        # Play button
        self.play_btn = tk.Button(
            control_frame, 
            text="▶ Play",
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=10,
            height=2
        )
        self.play_btn.config(command=self.play_tts)
        self.play_btn.pack(side='left', padx=(0, 10))
        
        # Stop button
        self.stop_btn = tk.Button(
            control_frame, 
            text="⏹ Stop",
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=10,
            height=2
        )
        self.stop_btn.config(command=self.stop_playback)
        self.stop_btn.pack(side='left')
        
        # Options button
        self.options_btn = tk.Button(
            control_frame, 
            text="⚙ Options",
            font=('Segoe UI', 10),
            relief='flat',
            cursor='hand2',
            width=10,
            height=2
        )
        self.options_btn.config(command=self.open_options)
        self.options_btn.pack(side='right')
        
        # Volume control frame
        volume_frame = tk.Frame(self.main_frame)
        volume_frame.pack(fill='x', padx=20, pady=(0, 10))
        
        volume_label = tk.Label(
            volume_frame,
            text="Volume:",
            font=('Segoe UI', 10)
        )
        volume_label.pack(side='left', padx=(0, 10))
        
        self.volume_percent = tk.IntVar(value=100)
        
        self.volume_slider = tk.Scale(
            volume_frame,
            from_=0,
            to=200,
            orient='horizontal',
            variable=self.volume_percent,
            command=self.on_volume_change,
            showvalue=False,
            length=200,
            resolution=1
        )
        self.volume_slider.set(100)
        self.volume_slider.pack(side='left', fill='x', expand=True)
        
        self.volume_label = tk.Label(
            volume_frame,
            text="100%",
            font=('Segoe UI', 10),
            width=5
        )
        self.volume_label.pack(side='left', padx=(10, 0))
        
        # Store widgets for theme updating
        self.main_widgets = [
            title_label, text_label, self.text_box, 
            text_frame, self.play_btn, self.stop_btn, 
            self.options_btn, control_frame, volume_frame,
            volume_label, self.volume_label
        ]
    
    def on_volume_change(self, value):
        """Update volume label when slider changes"""
        vol_percent = int(float(value))
        self.volume_label.config(text=f"{vol_percent}%")
        # Convert 0-200 scale to 0.0-2.0 multiplier
        self.volume.set(vol_percent / 100.0)
        print(f"Volume changed to: {vol_percent}% (multiplier: {self.volume.get()})")
        self.save_settings()
    
    def create_options_frame(self):
        self.options_frame = tk.Frame(self.root)
        
        # Title
        options_title = tk.Label(
            self.options_frame,
            text="⚙ Settings",
            font=('Segoe UI', 16, 'bold')
        )
        options_title.pack(pady=(15, 20))
        
        # Voice selection
        voice_label = tk.Label(
            self.options_frame, 
            text="Voice:",
            font=('Segoe UI', 10, 'bold')
        )
        voice_label.pack(pady=(5, 3), padx=25, anchor='w')
        
        self.voice_dropdown = ttk.Combobox(
            self.options_frame, 
            values=[v['name'] for v in self.voices], 
            state='readonly',
            font=('Segoe UI', 9),
            width=45
        )
        self.voice_dropdown.current(0)
        self.voice_dropdown.pack(pady=(0, 10), padx=25)
        
        # Output device 1
        output1_label = tk.Label(
            self.options_frame, 
            text="Output Device 1:",
            font=('Segoe UI', 10, 'bold')
        )
        output1_label.pack(pady=(5, 3), padx=25, anchor='w')
        
        device_names = [f"{i}: {d['name']}" for i, d in enumerate(self.audio_devices)]
        self.output1_dropdown = ttk.Combobox(
            self.options_frame, 
            values=device_names, 
            state='readonly',
            font=('Segoe UI', 9),
            width=45
        )
        default_device = sd.default.device[1]
        self.output1_dropdown.current(default_device if default_device < len(device_names) else 0)
        self.output1_dropdown.pack(pady=(0, 10), padx=25)
        
        # Output device 2
        output2_label = tk.Label(
            self.options_frame, 
            text="Output Device 2 (optional):",
            font=('Segoe UI', 10, 'bold')
        )
        output2_label.pack(pady=(5, 3), padx=25, anchor='w')
        
        self.output2_dropdown = ttk.Combobox(
            self.options_frame, 
            values=["None"] + device_names, 
            state='readonly',
            font=('Segoe UI', 9),
            width=45
        )
        self.output2_dropdown.current(0)
        self.output2_dropdown.pack(pady=(0, 15), padx=25)
        
        # Checkboxes frame
        checkbox_frame = tk.Frame(self.options_frame)
        checkbox_frame.pack(pady=(0, 10))
        
        # Stay on top checkbox
        self.stay_check = tk.Checkbutton(
            checkbox_frame, 
            text="📌 Stay on Top", 
            variable=self.stay_var,
            command=self.toggle_stay_on_top,
            font=('Segoe UI', 10),
            cursor='hand2'
        )
        self.stay_check.pack(side='left', padx=10)
        
        # Dark mode checkbox
        self.dark_check = tk.Checkbutton(
            checkbox_frame,
            text="🌙 Dark Mode",
            variable=self.dark_mode,
            command=self.toggle_dark_mode,
            font=('Segoe UI', 10),
            cursor='hand2'
        )
        self.dark_check.pack(side='left', padx=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.options_frame)
        buttons_frame.pack(pady=10)
        
        # Soundboard button
        self.soundboard_btn = tk.Button(
            buttons_frame, 
            text="🎵 Soundboard",
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=15,
            height=2
        )
        self.soundboard_btn.config(command=self.open_soundboard)
        self.soundboard_btn.pack(side='left', padx=5)
        
        # Back button
        self.back_btn = tk.Button(
            buttons_frame, 
            text="← Back",
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=15,
            height=2
        )
        self.back_btn.config(command=self.close_options)
        self.back_btn.pack(side='left', padx=5)
        
        # Store widgets for theme updating
        self.options_widgets = [
            options_title, voice_label, output1_label, 
            output2_label, self.stay_check, self.dark_check,
            self.back_btn, checkbox_frame, buttons_frame, self.soundboard_btn
        ]
    
    def create_soundboard_frame(self):
        self.soundboard_frame = tk.Frame(self.root)
        
        # Title
        soundboard_title = tk.Label(
            self.soundboard_frame,
            text="🎵 Soundboard",
            font=('Segoe UI', 16, 'bold')
        )
        soundboard_title.pack(pady=(15, 10))
        
        # Instructions
        instructions = tk.Label(
            self.soundboard_frame,
            text="Select cached sounds and assign hotkeys (ESC = None)",
            font=('Segoe UI', 9),
            fg='gray'
        )
        instructions.pack(pady=(0, 10))
        
        # Scrollable list frame
        list_frame = tk.Frame(self.soundboard_frame)
        list_frame.pack(fill='both', expand=True, padx=20, pady=(0, 10))
        
        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Listbox for sounds
        self.sounds_listbox = tk.Listbox(
            list_frame,
            font=('Segoe UI', 9),
            yscrollcommand=scrollbar.set,
            height=10
        )
        self.sounds_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.sounds_listbox.yview)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.soundboard_frame)
        buttons_frame.pack(pady=10)
        
        # Refresh button
        refresh_btn = tk.Button(
            buttons_frame,
            text="🔄 Refresh",
            font=('Segoe UI', 10),
            relief='flat',
            cursor='hand2',
            width=12,
            height=2,
            command=self.refresh_soundboard_list
        )
        refresh_btn.pack(side='left', padx=5)
        
        # Assign hotkey button
        self.assign_btn = tk.Button(
            buttons_frame,
            text="⌨ Assign Key",
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=15,
            height=2,
            command=self.assign_hotkey
        )
        self.assign_btn.pack(side='left', padx=5)
        
        # Back button
        back_btn = tk.Button(
            self.soundboard_frame,
            text="← Back to Options",
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=20,
            height=2,
            command=self.close_soundboard
        )
        back_btn.pack(pady=10)
        
        # Store widgets for theme
        self.soundboard_widgets = [
            soundboard_title, instructions, list_frame,
            self.sounds_listbox, buttons_frame, refresh_btn,
            self.assign_btn, back_btn
        ]
        
        # Initial refresh
        self.refresh_soundboard_list()
    
    def refresh_soundboard_list(self):
        """Refresh the list of cached sounds"""
        self.sounds_listbox.delete(0, tk.END)
        
        if not os.path.exists(self.cache_dir):
            return
        
        # Get all mp3 files in cache
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.mp3')]
        
        for filename in sorted(cache_files):
            filepath = os.path.join(self.cache_dir, filename)
            # Check if this file has a hotkey assigned
            hotkey = None
            for key, path in self.soundboard_bindings.items():
                if path == filepath:
                    hotkey = key
                    break
            
            # Display format: "filename [Hotkey: F1]" or just "filename"
            display_name = filename[:-4]  # Remove .mp3
            if hotkey:
                display_name += f" [Key: {hotkey}]"
            
            self.sounds_listbox.insert(tk.END, display_name)
    
    def assign_hotkey(self):
        """Assign a hotkey to the selected sound"""
        selection = self.sounds_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        display_name = self.sounds_listbox.get(idx)
        
        # Extract filename (remove hotkey info if present)
        if " [Key: " in display_name:
            filename = display_name.split(" [Key: ")[0] + ".mp3"
            # Also remove the old binding
            old_key = display_name.split(" [Key: ")[1].rstrip(']')
            if old_key in self.soundboard_bindings:
                del self.soundboard_bindings[old_key]
        else:
            filename = display_name + ".mp3"
        
        filepath = os.path.join(self.cache_dir, filename)
        
        # Show waiting dialog
        self.assign_btn.config(text="Press key...")
        self.root.update()
        
        # Wait for key press
        pressed_key = self.wait_for_keypress()
        
        if pressed_key and pressed_key != "esc":
            # Remove any existing binding with this key
            if pressed_key in self.soundboard_bindings:
                del self.soundboard_bindings[pressed_key]
            
            # Add new binding
            self.soundboard_bindings[pressed_key] = filepath
            self.save_soundboard()
            self.restart_hotkey_listener()
        elif pressed_key == "esc":
            # ESC removes the binding for this sound
            for key, path in list(self.soundboard_bindings.items()):
                if path == filepath:
                    del self.soundboard_bindings[key]
            self.save_soundboard()
            self.restart_hotkey_listener()
        
        self.assign_btn.config(text="⌨ Assign Key")
        self.refresh_soundboard_list()
    
    def wait_for_keypress(self):
        """Wait for a single keypress and return the key"""
        pressed_key = [None]
        
        def on_press(key):
            try:
                # Handle special keys
                if key == keyboard.Key.esc:
                    pressed_key[0] = "esc"
                elif hasattr(key, 'char') and key.char:
                    pressed_key[0] = key.char.lower()
                elif hasattr(key, 'name'):
                    pressed_key[0] = key.name.lower()
                else:
                    pressed_key[0] = str(key).replace("Key.", "").lower()
                return False  # Stop listener
            except:
                return False
        
        # Create temporary listener
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
        
        return pressed_key[0]
    
    def remove_hotkey(self):
        """Remove hotkey from selected sound"""
        selection = self.sounds_listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        display_name = self.sounds_listbox.get(idx)
        
        # Extract filename
        if " [Key: " in display_name:
            filename = display_name.split(" [Key: ")[0] + ".mp3"
        else:
            return  # No hotkey assigned
        
        filepath = os.path.join(self.cache_dir, filename)
        
        # Find and remove binding
        to_remove = None
        for key, path in self.soundboard_bindings.items():
            if path == filepath:
                to_remove = key
                break
        
        if to_remove:
            del self.soundboard_bindings[to_remove]
            self.save_soundboard()
            self.restart_hotkey_listener()
            self.refresh_soundboard_list()
    
    def start_hotkey_listener(self):
        """Start global hotkey listener"""
        def on_press(key):
            try:
                key_str = None
                if hasattr(key, 'char') and key.char:
                    key_str = key.char.lower()
                elif hasattr(key, 'name'):
                    key_str = key.name.lower()
                else:
                    key_str = str(key).replace("Key.", "").lower()
                
                if key_str in self.soundboard_bindings:
                    filepath = self.soundboard_bindings[key_str]
                    threading.Thread(target=self.play_soundboard_sound, args=(filepath,), daemon=True).start()
            except:
                pass
        
        self.hotkey_listener = keyboard.Listener(on_press=on_press)
        self.hotkey_listener.start()
    
    def restart_hotkey_listener(self):
        """Restart the hotkey listener with new bindings"""
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.start_hotkey_listener()
    
    def play_soundboard_sound(self, filepath):
        """Play a sound from the soundboard"""
        # Stop any currently playing sound
        self.stop_playback()
        
        self.is_playing = True
        
        try:
            # Get selected output devices
            device1_index = self.output1_dropdown.current()
            device2_index = self.output2_dropdown.current()
            
            devices = [device1_index]
            if device2_index > 0:
                devices.append(device2_index - 1)
            
            # Load audio
            data, sr = sf.read(filepath, dtype='float32')
            
            # Apply volume with clipping
            import numpy as np
            volume_multiplier = self.volume.get()
            data = np.clip(data * volume_multiplier, -1.0, 1.0)
            
            # Ensure audio is mono for compatibility
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            
            # Play on all devices
            for device_index in devices:
                try:
                    device_info = sd.query_devices(device_index)
                    max_channels = device_info['max_output_channels']
                    
                    if max_channels == 1:
                        output_data = data
                    elif max_channels >= 2:
                        output_data = np.column_stack([data, data])
                    else:
                        continue
                    
                    sd.play(output_data, sr, device=device_index)
                except Exception as e:
                    print(f"Error playing on device {device_index}: {e}")
            
            sd.wait()
            
        except Exception as e:
            print(f"Error playing soundboard sound: {e}")
        finally:
            self.is_playing = False
    
    def load_soundboard(self):
        """Load soundboard bindings from file"""
        if os.path.exists(self.soundboard_file):
            try:
                with open(self.soundboard_file, 'r') as f:
                    self.soundboard_bindings = json.load(f)
            except:
                self.soundboard_bindings = {}
    
    def save_soundboard(self):
        """Save soundboard bindings to file"""
        try:
            with open(self.soundboard_file, 'w') as f:
                json.dump(self.soundboard_bindings, f, indent=2)
        except Exception as e:
            print(f"Error saving soundboard: {e}")
    
    def open_soundboard(self):
        """Open soundboard window"""
        self.options_frame.pack_forget()
        self.soundboard_frame.pack(fill='both', expand=True)
        self.refresh_soundboard_list()
    
    def close_soundboard(self):
        """Close soundboard and return to options"""
        self.soundboard_frame.pack_forget()
        self.options_frame.pack(fill='both', expand=True)
    
    def load_settings(self):
        """Load settings from INI file"""
        config = configparser.ConfigParser()
        
        if os.path.exists(self.config_file):
            try:
                config.read(self.config_file)
                
                # Load voice
                if config.has_option('Settings', 'voice_index'):
                    voice_index = config.getint('Settings', 'voice_index')
                    if 0 <= voice_index < len(self.voices):
                        self.voice_dropdown.current(voice_index)
                
                # Load output device 1
                if config.has_option('Settings', 'output1_index'):
                    output1_index = config.getint('Settings', 'output1_index')
                    if 0 <= output1_index < len(self.audio_devices):
                        self.output1_dropdown.current(output1_index)
                
                # Load output device 2
                if config.has_option('Settings', 'output2_index'):
                    output2_index = config.getint('Settings', 'output2_index')
                    device_count = len(self.audio_devices) + 1
                    if 0 <= output2_index < device_count:
                        self.output2_dropdown.current(output2_index)
                
                # Load volume
                if config.has_option('Settings', 'volume'):
                    volume_percent = config.getint('Settings', 'volume')
                    self.volume_percent.set(volume_percent)
                    self.volume.set(volume_percent / 100.0)
                    self.volume_slider.set(volume_percent)
                    self.volume_label.config(text=f"{volume_percent}%")
                
                # Load dark mode
                if config.has_option('Settings', 'dark_mode'):
                    self.dark_mode.set(config.getboolean('Settings', 'dark_mode'))
                
                # Load stay on top
                if config.has_option('Settings', 'stay_on_top'):
                    stay_on_top = config.getboolean('Settings', 'stay_on_top')
                    self.stay_var.set(stay_on_top)
                    self.root.attributes('-topmost', stay_on_top)
                    
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save settings to INI file"""
        config = configparser.ConfigParser()
        config['Settings'] = {
            'voice_index': str(self.voice_dropdown.current()),
            'output1_index': str(self.output1_dropdown.current()),
            'output2_index': str(self.output2_dropdown.current()),
            'volume': str(self.volume_percent.get()),
            'dark_mode': str(self.dark_mode.get()),
            'stay_on_top': str(self.stay_var.get())
        }
        
        try:
            with open(self.config_file, 'w') as f:
                config.write(f)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def apply_theme(self):
        colors = self.get_colors()
        
        # Root window
        self.root.config(bg=colors['bg'])
        
        # Main frame widgets
        self.main_frame.config(bg=colors['bg'])
        for widget in self.main_widgets:
            if isinstance(widget, tk.Label):
                widget.config(bg=colors['bg'], fg=colors['fg'])
            elif isinstance(widget, tk.Text):
                widget.config(
                    bg=colors['entry_bg'], 
                    fg=colors['entry_fg'],
                    insertbackground=colors['fg'],
                    selectbackground=colors['accent']
                )
            elif isinstance(widget, tk.Button):
                widget.config(
                    bg=colors['button_bg'],
                    fg=colors['button_fg'],
                    activebackground=colors['hover'],
                    activeforeground=colors['fg']
                )
            elif isinstance(widget, tk.Frame):
                widget.config(bg=colors['bg'])
            elif isinstance(widget, tk.Scale):
                widget.config(
                    bg=colors['bg'],
                    fg=colors['fg'],
                    troughcolor=colors['button_bg'],
                    activebackground=colors['accent']
                )
        
        # Options frame widgets
        self.options_frame.config(bg=colors['bg'])
        for widget in self.options_widgets:
            if isinstance(widget, tk.Label):
                widget.config(bg=colors['bg'], fg=colors['fg'])
            elif isinstance(widget, tk.Checkbutton):
                widget.config(
                    bg=colors['bg'],
                    fg=colors['fg'],
                    activebackground=colors['bg'],
                    activeforeground=colors['fg'],
                    selectcolor=colors['button_bg']
                )
            elif isinstance(widget, tk.Button):
                widget.config(
                    bg=colors['button_bg'],
                    fg=colors['button_fg'],
                    activebackground=colors['hover'],
                    activeforeground=colors['fg']
                )
            elif isinstance(widget, tk.Frame):
                widget.config(bg=colors['bg'])
        
        # Soundboard frame widgets
        self.soundboard_frame.config(bg=colors['bg'])
        for widget in self.soundboard_widgets:
            if isinstance(widget, tk.Label):
                widget.config(bg=colors['bg'], fg=colors['fg'])
            elif isinstance(widget, tk.Listbox):
                widget.config(
                    bg=colors['entry_bg'],
                    fg=colors['entry_fg'],
                    selectbackground=colors['accent']
                )
            elif isinstance(widget, tk.Button):
                widget.config(
                    bg=colors['button_bg'],
                    fg=colors['button_fg'],
                    activebackground=colors['hover'],
                    activeforeground=colors['fg']
                )
            elif isinstance(widget, tk.Frame):
                widget.config(bg=colors['bg'])
        
        # Configure progress bar style
        style = ttk.Style()
        if self.dark_mode.get():
            style.configure(
                'Custom.Horizontal.TProgressbar',
                troughcolor=colors['button_bg'],
                background=colors['accent'],
                bordercolor=colors['bg'],
                lightcolor=colors['accent'],
                darkcolor=colors['accent']
            )
        else:
            style.configure(
                'Custom.Horizontal.TProgressbar',
                troughcolor='#e0e0e0',
                background=colors['accent'],
                bordercolor=colors['bg'],
                lightcolor=colors['accent'],
                darkcolor=colors['accent']
            )
        
        # Configure combobox style
        style.configure('TCombobox', fieldbackground=colors['entry_bg'])
        
        # Save settings when theme changes
        self.save_settings()
    
    def toggle_dark_mode(self):
        self.apply_theme()
    
    def toggle_stay_on_top(self):
        self.root.attributes('-topmost', self.stay_var.get())
        self.save_settings()
    
    def play_tts(self):
        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            return
        
        if self.is_playing:
            return
        
        voice_index = self.voice_dropdown.current()
        device1_index = self.output1_dropdown.current()
        device2_index = self.output2_dropdown.current()
        
        # Get actual device indices
        devices = [device1_index]
        if device2_index > 0:
            devices.append(device2_index - 1)
        
        # Save settings when playing
        self.save_settings()
        
        threading.Thread(target=self._tts_thread, args=(text, voice_index, devices), daemon=True).start()
    
    def _tts_thread(self, text, voice_index, device_indices):
        self.is_playing = True
        audio_file = None
        
        try:
            print(f"Starting TTS for: {text[:50]}...")
            
            # Generate speech using edge-tts (with caching)
            voice_name = self.voices[voice_index]['voice']
            audio_file = self.generate_speech_edgetts(text, voice_name)
            
            print(f"Audio file ready: {audio_file}")
            
            # Load audio file
            data, sr = sf.read(audio_file, dtype='float32')
            print(f"Audio loaded: {len(data)} samples at {sr}Hz, shape: {data.shape}")
            
            # Apply volume - ensure we're using the actual multiplier
            import numpy as np
            volume_multiplier = self.volume.get()
            print(f"Applying volume multiplier: {volume_multiplier}")
            
            # Clip to prevent distortion at high volumes
            data = np.clip(data * volume_multiplier, -1.0, 1.0)
            
            # Ensure audio is mono for compatibility
            if len(data.shape) > 1:
                data = data.mean(axis=1)
            
            # Calculate duration for progress bar
            duration = len(data) / sr
            
            # Start playback on multiple devices
            for device_index in device_indices:
                try:
                    print(f"Playing on device {device_index}")
                    
                    # Get device info
                    device_info = sd.query_devices(device_index)
                    max_channels = device_info['max_output_channels']
                    
                    # Prepare audio data for this device
                    if max_channels == 1:
                        output_data = data
                    elif max_channels >= 2:
                        output_data = np.column_stack([data, data])
                    else:
                        print(f"Warning: Device {device_index} has {max_channels} channels")
                        continue
                    
                    sd.play(output_data, sr, device=device_index)
                    
                except Exception as device_error:
                    print(f"Error playing on device {device_index}: {device_error}")
            
            # Update progress bar
            self._update_progress(duration)
            
            # Wait for playback to finish
            sd.wait()
            print("Playback finished")
            
        except Exception as e:
            print(f"Error during TTS playback: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            self.is_playing = False
            self.progress_var.set(0)
    
    def _update_progress(self, duration):
        steps = 50
        step_duration = duration / steps
        
        for i in range(steps + 1):
            if not self.is_playing:
                break
            self.progress_var.set(int((i / steps) * 100))
            time.sleep(step_duration)
    
    def stop_playback(self):
        self.is_playing = False
        sd.stop()
        self.progress_var.set(0)
    
    def open_options(self):
        self.main_frame.pack_forget()
        self.options_frame.pack(fill='both', expand=True)
    
    def close_options(self):
        self.options_frame.pack_forget()
        self.main_frame.pack(fill='both', expand=True)
    
    def on_closing(self):
        """Handle window closing"""
        self.stop_playback()
        self.save_settings()
        
        # Stop hotkey listener
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()
