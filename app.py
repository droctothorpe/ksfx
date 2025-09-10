#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import wave
import struct
import simpleaudio as sa

import rumps
from pynput import keyboard

class AirhornApp(rumps.App):
    def __init__(self):
        super(AirhornApp, self).__init__("၊၊||၊", quit_button=None)
        
        # Get the absolute path to the sound file
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.sound_path = os.path.join(script_dir, "sfx", "dj-airhorn-one.wav")
        
        # Check if sound file exists
        if not os.path.exists(self.sound_path):
            rumps.alert("Error", f"Sound file not found at: {self.sound_path}")
            sys.exit(1)
            
        # Set up menu items
        self.volume = 0.1  # Default to 10% volume
        self.volume_menu = rumps.MenuItem("Volume")
        self.volume_options = {
            "0%": rumps.MenuItem("0%", callback=self.set_volume),
            "10%": rumps.MenuItem("10%", callback=self.set_volume),
            "20%": rumps.MenuItem("20%", callback=self.set_volume),
            "30%": rumps.MenuItem("30%", callback=self.set_volume),
            "40%": rumps.MenuItem("40%", callback=self.set_volume),
            "50%": rumps.MenuItem("50%", callback=self.set_volume),
            "60%": rumps.MenuItem("60%", callback=self.set_volume),
            "70%": rumps.MenuItem("70%", callback=self.set_volume),
            "80%": rumps.MenuItem("80%", callback=self.set_volume),
            "90%": rumps.MenuItem("90%", callback=self.set_volume),
            "100%": rumps.MenuItem("100%", callback=self.set_volume)
        }
        
        # Add volume options to volume menu
        for option, menu_item in self.volume_options.items():
            self.volume_menu.add(menu_item)
        
        # Set default volume option as checked
        self.volume_options["10%"].state = 1
        
        # Set up main menu items
        self.menu = ["On", "Off", None, self.volume_menu, None, "Quit"]
        self.enabled = True
        self.listener = None
        
        # Pre-load the sound file with the default volume applied
        self.reload_sound_objects()  # This applies the volume and creates the sound pool
        self.current_sound_index = 0
        # Track the currently playing sounds
        self.play_objs = []
        
    @rumps.clicked("On")
    def enable(self, _):
        if not self.enabled:
            self.enabled = True
            # self.title = "၊၊||၊"
            
            # Start keyboard listener in a separate thread
            self.listener = keyboard.Listener(on_press=self.on_key_press)
            self.listener.start()
            # rumps.notification("Airhorn", "Keyboard Airhorn", "Airhorn enabled! Press any key to hear it.")
    
    @rumps.clicked("Off")
    def disable(self, _):
        if self.enabled:
            self.enabled = False
            self.title = "🔊"
            
            # Stop keyboard listener
            if self.listener:
                self.listener.stop()
                self.listener = None
    
    @rumps.clicked("Quit")
    def quit(self, _):
        # Clean up before quitting
        if self.listener:
            self.listener.stop()
        # Stop all playing sounds
        for obj in self.play_objs:
            try:
                obj.stop()
            except:
                pass  # Ignore errors if sound already stopped
        rumps.quit_application()
    
    def set_volume(self, sender):
        # Uncheck all volume options
        for option in self.volume_options.values():
            option.state = 0
        
        # Check the selected option
        sender.state = 1
        
        # Set the volume based on the selected option
        volume_text = sender.title
        volume_percent = int(volume_text.strip('%'))
        self.volume = volume_percent / 100.0
        
        # Reload sound objects with new volume
        self.reload_sound_objects()
    
    def reload_sound_objects(self):
        # Load the wave file
        with wave.open(self.sound_path, 'rb') as wave_file:
            # Get audio parameters
            n_channels = wave_file.getnchannels()
            sample_width = wave_file.getsampwidth()
            n_frames = wave_file.getnframes()
            frame_rate = wave_file.getframerate()
            audio_data = wave_file.readframes(n_frames)
            
            # Apply volume adjustment using native Python
            if sample_width == 1:  # 8-bit audio
                fmt = f"{len(audio_data)}B"  # unsigned char
                raw_data = struct.unpack(fmt, audio_data)
                # 8-bit audio is unsigned, centered at 128
                adjusted_data = [int(max(0, min(255, 128 + (sample - 128) * self.volume))) for sample in raw_data]
                audio_data = struct.pack(fmt, *adjusted_data)
            elif sample_width == 2:  # 16-bit audio
                fmt = f"{len(audio_data)//2}h"  # signed short
                raw_data = struct.unpack(fmt, audio_data)
                adjusted_data = [int(sample * self.volume) for sample in raw_data]
                audio_data = struct.pack(fmt, *adjusted_data)
            elif sample_width == 4:  # 32-bit audio
                fmt = f"{len(audio_data)//4}i"  # signed int
                raw_data = struct.unpack(fmt, audio_data)
                adjusted_data = [int(sample * self.volume) for sample in raw_data]
                audio_data = struct.pack(fmt, *adjusted_data)
            
            # Create WaveObject from the adjusted audio data
            self.wave_obj = sa.WaveObject(audio_data, n_channels, sample_width, frame_rate)
            self.sound_pool = [self.wave_obj] * 1
    
    def on_key_press(self, key):
        # Play sound when any key is pressed
        if self.enabled:
            # Stop all currently playing sounds without checking if they're playing
            # This avoids the overhead of checking play status
            for obj in self.play_objs:
                try:
                    obj.stop()
                except:
                    pass  # Ignore errors if sound already stopped
            
            # Use round-robin from the sound pool for faster response
            self.current_sound_index = (self.current_sound_index + 1) % len(self.sound_pool)
            # Play the sound immediately (volume is already applied to the audio data)
            play_obj = self.sound_pool[self.current_sound_index].play()
            
            # Update the list of playing objects
            self.play_objs = [play_obj]
            
        return True  # Continue listening

if __name__ == "__main__":
    app = AirhornApp()
    # Start keyboard listener automatically when app launches
    app.listener = keyboard.Listener(on_press=app.on_key_press)
    app.listener.start()
    app.run()
