import wx
import os
import tempfile
import threading
import uuid
import platform
import subprocess
import pyttsx3

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

def change_pitch(sound, pitch_factor):
    new_frame_rate = int(sound.frame_rate * pitch_factor)
    pitched_sound = sound._spawn(sound.raw_data, overrides={'frame_rate': new_frame_rate})
    return pitched_sound.set_frame_rate(44100)

class TextToSpeechFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Accessible Text to Speech Converter - Created by Rani Basak", size=(700, 720))
        self.engine = pyttsx3.init()
        self.voices = self.engine.getProperty('voices')
        self.default_voice_index = 0

        panel = wx.Panel(self)
        self.panel = panel

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        welcome_text = wx.StaticText(panel, label="Welcome to the Accessible Text to Speech Converter!\nCreated by Rani Basak.")
        font = welcome_text.GetFont()
        font.PointSize += 2
        font = font.Bold()
        welcome_text.SetFont(font)
        main_sizer.Add(welcome_text, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        main_sizer.Add(wx.StaticText(panel, label="Select Voice (Alt+V):"), 0, wx.ALL, 5)
        self.voice_choice = wx.Choice(panel, choices=[f"{i}. {v.name}" for i, v in enumerate(self.voices)])
        self.voice_choice.SetSelection(self.default_voice_index)
        main_sizer.Add(self.voice_choice, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(wx.StaticText(panel, label="Enter Text (Alt+T):"), 0, wx.ALL, 5)
        self.text_entry = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_WORDWRAP, size=(-1, 150))
        main_sizer.Add(self.text_entry, 1, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(wx.StaticText(panel, label="Speech Rate (Alt+R):"), 0, wx.ALL, 5)
        self.rate_slider = wx.Slider(panel, value=self.engine.getProperty('rate'), minValue=100, maxValue=300)
        main_sizer.Add(self.rate_slider, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(wx.StaticText(panel, label="Volume (Alt+U):"), 0, wx.ALL, 5)
        self.volume_slider = wx.Slider(panel, value=int(self.engine.getProperty('volume') * 10), minValue=0, maxValue=10)
        main_sizer.Add(self.volume_slider, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(wx.StaticText(panel, label="Pitch:"), 0, wx.ALL, 5)
        self.pitch_slider = wx.Slider(panel, value=100, minValue=50, maxValue=200)
        main_sizer.Add(self.pitch_slider, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(wx.StaticText(panel, label="File Name (Alt+F):"), 0, wx.ALL, 5)
        self.filename_entry = wx.TextCtrl(panel)
        main_sizer.Add(self.filename_entry, 0, wx.EXPAND | wx.ALL, 5)

        main_sizer.Add(wx.StaticText(panel, label="Select Format (Alt+M):"), 0, wx.ALL, 5)
        self.file_format = wx.Choice(panel, choices=["mp3", "wav"])
        self.file_format.SetSelection(0)
        main_sizer.Add(self.file_format, 0, wx.EXPAND | wx.ALL, 5)

        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.preview_btn = wx.Button(panel, label="Preview (Alt+P)")
        save_btn = wx.Button(panel, label="Save Audio (Alt+S)")
        btn_sizer.Add(self.preview_btn, 1, wx.ALL, 5)
        btn_sizer.Add(save_btn, 1, wx.ALL, 5)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER)

        self.preview_btn.Bind(wx.EVT_BUTTON, self.on_preview)
        save_btn.Bind(wx.EVT_BUTTON, self.on_save)

        panel.SetSizer(main_sizer)
        self.Centre()
        self.Show()

        self.setup_shortcuts()
        self.speak_text("Welcome to the Accessible Text to Speech Converter. Created by Rani Basak.")

    def setup_shortcuts(self):
        accel_table = wx.AcceleratorTable([
            (wx.ACCEL_ALT, ord('T'), wx.ID_HIGHEST + 1),
            (wx.ACCEL_ALT, ord('U'), wx.ID_HIGHEST + 2),
            (wx.ACCEL_ALT, ord('R'), wx.ID_HIGHEST + 3),
            (wx.ACCEL_ALT, ord('V'), wx.ID_HIGHEST + 4),
            (wx.ACCEL_ALT, ord('F'), wx.ID_HIGHEST + 5),
            (wx.ACCEL_ALT, ord('M'), wx.ID_HIGHEST + 6),
            (wx.ACCEL_ALT, ord('P'), wx.ID_HIGHEST + 7),
            (wx.ACCEL_ALT, ord('S'), wx.ID_HIGHEST + 8),
        ])
        self.SetAcceleratorTable(accel_table)

        self.Bind(wx.EVT_MENU, lambda evt: self.text_entry.SetFocus(), id=wx.ID_HIGHEST + 1)
        self.Bind(wx.EVT_MENU, lambda evt: self.volume_slider.SetFocus(), id=wx.ID_HIGHEST + 2)
        self.Bind(wx.EVT_MENU, lambda evt: self.rate_slider.SetFocus(), id=wx.ID_HIGHEST + 3)
        self.Bind(wx.EVT_MENU, lambda evt: self.voice_choice.SetFocus(), id=wx.ID_HIGHEST + 4)
        self.Bind(wx.EVT_MENU, lambda evt: self.filename_entry.SetFocus(), id=wx.ID_HIGHEST + 5)
        self.Bind(wx.EVT_MENU, lambda evt: self.file_format.SetFocus(), id=wx.ID_HIGHEST + 6)
        self.Bind(wx.EVT_MENU, self.on_preview, id=wx.ID_HIGHEST + 7)
        self.Bind(wx.EVT_MENU, self.on_save, id=wx.ID_HIGHEST + 8)

    def speak_text(self, text):
        self.engine.setProperty('voice', self.voices[self.voice_choice.GetSelection()].id)
        self.engine.setProperty('rate', self.rate_slider.GetValue())
        self.engine.setProperty('volume', self.volume_slider.GetValue() / 10.0)
        self.engine.say(text)
        self.engine.runAndWait()

    def on_preview(self, event):
        text = self.text_entry.GetValue().strip()
        if not text:
            wx.MessageBox("Please enter some text.", "Warning", wx.ICON_WARNING)
            return
        self.preview_btn.Disable()
        threading.Thread(target=self._preview_thread, args=(text,), daemon=True).start()

    def _preview_thread(self, text):
        temp_dir = tempfile.mkdtemp()
        temp_input = os.path.join(temp_dir, f"preview_input.wav")
        temp_output = os.path.join(temp_dir, f"preview_output.wav")
        try:
            self.engine.setProperty('voice', self.voices[self.voice_choice.GetSelection()].id)
            self.engine.setProperty('rate', self.rate_slider.GetValue())
            self.engine.setProperty('volume', self.volume_slider.GetValue() / 10.0)
            self.engine.save_to_file(text, temp_input)
            self.engine.runAndWait()

            if AudioSegment:
                with open(temp_input, "rb") as f:
                    sound = AudioSegment.from_file(f, format="wav")
                pitch_factor = self.pitch_slider.GetValue() / 100.0
                pitched_sound = change_pitch(sound, pitch_factor)
                pitched_sound.export(temp_output, format="wav")
            else:
                temp_output = temp_input

            if platform.system() == "Windows":
                self._play_windows(temp_output)
            elif platform.system() == "Darwin":
                self._play_mac(temp_output)
            else:
                self._play_linux(temp_output)

            wx.CallAfter(self._on_preview_done)
        except Exception as e:
            wx.CallAfter(wx.MessageBox, f"Preview error: {e}", "Error", wx.ICON_ERROR)
        finally:
            for f in [temp_input, temp_output]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except:
                    pass
            wx.CallAfter(self.preview_btn.Enable)

    def _play_windows(self, filepath):
        import winsound
        winsound.PlaySound(filepath, winsound.SND_FILENAME)

    def _play_mac(self, filepath):
        subprocess.run(['afplay', filepath])

    def _play_linux(self, filepath):
        if subprocess.call(['which', 'aplay'], stdout=subprocess.DEVNULL) == 0:
            subprocess.run(['aplay', filepath])
        elif subprocess.call(['which', 'paplay'], stdout=subprocess.DEVNULL) == 0:
            subprocess.run(['paplay', filepath])
        else:
            raise RuntimeError("No audio player found.")

    def _on_preview_done(self):
        wx.MessageBox("Preview finished successfully.", "Success", wx.ICON_INFORMATION)

    def on_save(self, event):
        text = self.text_entry.GetValue().strip()
        if not text:
            wx.MessageBox("Please enter some text.", "Warning", wx.ICON_WARNING)
            return

        with wx.DirDialog(self, "Select folder to save audio") as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            folder = dlg.GetPath()

        filename = self.filename_entry.GetValue().strip()
        if not filename:
            wx.MessageBox("Please enter a filename.", "Warning", wx.ICON_WARNING)
            return

        selected_format = self.file_format.GetStringSelection().lower()
        full_path = os.path.join(folder, f"{filename}.{selected_format}")
        temp_wav_path = os.path.join(folder, filename + "_temp.wav")

        try:
            self.engine.setProperty('voice', self.voices[self.voice_choice.GetSelection()].id)
            self.engine.setProperty('rate', self.rate_slider.GetValue())
            self.engine.setProperty('volume', self.volume_slider.GetValue() / 10.0)
            self.engine.save_to_file(text, temp_wav_path)
            self.engine.runAndWait()

            pitch_factor = self.pitch_slider.GetValue() / 100.0
            if AudioSegment:
                sound = AudioSegment.from_wav(temp_wav_path)
                pitched_sound = change_pitch(sound, pitch_factor)
            else:
                pitched_sound = AudioSegment.from_wav(temp_wav_path)

            if selected_format == "mp3" and AudioSegment:
                pitched_sound.export(full_path, format="mp3")
            else:
                pitched_sound.export(full_path, format="wav")

            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)

            wx.MessageBox(f"Audio saved as: {full_path}", "Success", wx.ICON_INFORMATION)
            self.clear_fields()
        except Exception as e:
            wx.MessageBox(f"Failed to save audio: {e}", "Error", wx.ICON_ERROR)

    def clear_fields(self):
        self.text_entry.SetValue("")
        self.filename_entry.SetValue("")
        self.voice_choice.SetSelection(self.default_voice_index)
        self.rate_slider.SetValue(200)
        self.volume_slider.SetValue(10)
        self.pitch_slider.SetValue(100)
        self.file_format.SetSelection(0)

if __name__ == "__main__":
    app = wx.App(False)
    frame = TextToSpeechFrame()
    app.MainLoop()
