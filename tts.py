import tkinter as tk
from tkinter import ttk
import threading
import sounddevice as sd
import soundfile as sf
import tempfile
import os
import time
import configparser
import requests
import json

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("TTS App")
        self.root.geometry("450x380")
        self.root.resizable(False, False)
        
        # Config file path
        self.config_file = "tts_settings.ini"
        
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
        
        # Load settings
        self.load_settings()
        
        # Apply initial theme
        self.apply_theme()
        
        # Show main frame
        self.main_frame.pack(fill='both', expand=True)
        
        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def generate_speech_edgetts(self, text, voice_name):
        """Generate speech using edge-tts with caching for speed"""
        import edge_tts
        import asyncio
        import hashlib
        
        # Create a hash of the text and voice for caching
        cache_key = hashlib.md5(f"{text}_{voice_name}".encode()).hexdigest()
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        
        # Check if we have a cached version
        if os.path.exists(cache_file):
            print(f"Using cached audio for: {text[:30]}...")
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
        self.progress.pack(fill='x', padx=20, pady=(0, 15))
        
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
        
        # Store widgets for theme updating
        self.main_widgets = [
            title_label, text_label, self.text_box, 
            text_frame, self.play_btn, self.stop_btn, 
            self.options_btn, control_frame
        ]
    
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
        checkbox_frame.pack(pady=(0, 15))
        
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
        
        # Back button
        self.back_btn = tk.Button(
            self.options_frame, 
            text="← Back",
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            width=15,
            height=2
        )
        self.back_btn.config(command=self.close_options)
        self.back_btn.pack(pady=10)
        
        # Store widgets for theme updating
        self.options_widgets = [
            options_title, voice_label, output1_label, 
            output2_label, self.stay_check, self.dark_check,
            self.back_btn, checkbox_frame
        ]
    
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
        is_cached = False
        
        try:
            print(f"Starting TTS for: {text[:50]}...")
            
            # Generate speech using edge-tts (with caching)
            voice_name = self.voices[voice_index]['voice']
            audio_file = self.generate_speech_edgetts(text, voice_name)
            is_cached = "Using cached" in open(audio_file + ".log", "r").read() if os.path.exists(audio_file + ".log") else False
            
            print(f"Audio file ready: {audio_file}")
            
            # Load audio file
            data, sr = sf.read(audio_file, dtype='float32')
            print(f"Audio loaded: {len(data)} samples at {sr}Hz")
            
            # Calculate duration for progress bar
            duration = len(data) / sr
            
            # Start playback on multiple devices
            for device_index in device_indices:
                print(f"Playing on device {device_index}")
                sd.play(data, sr, device=device_index)
            
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
            # Clean up - only delete if not cached
            self.is_playing = False
            self.progress_var.set(0)
            # Cache files are kept for speed - they're reused automatically
    
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
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()
