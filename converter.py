import os
import threading
from kivy.clock import Clock
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.metrics import dp
from yt_dlp import YoutubeDL
from pydub import AudioSegment

# Import KivyMD components
from kivymd.app import MDApp  
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivy.core.window import Window


class ConvertApp(MDApp):  
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "ConvertToMP3 (づ ◕‿◕ )づ"

        # Set window size
        Window.size = (800, 500)

    def build(self):
        # Create the root layout
        self.root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(15))

        # Top bar
        self.top_bar = MDTopAppBar(
            title="Paste a video link and convert it to MP3 file!",
            elevation=10,
            md_bg_color=self.theme_cls.primary_color,
        )
        self.root.add_widget(self.top_bar)

        # Add a label for the URL input
        self.url_label = MDLabel(
            text="URL: ",
            size_hint_y=None,
            height=dp(30),
            font_style="Subtitle1",
        )
        self.root.add_widget(self.url_label)

        # Add a text input for the URL
        self.url_entry = MDTextField(
            hint_text="Paste URL here...",
            mode="fill",
            size_hint=(1, None),
            height=dp(40),
        )
        self.root.add_widget(self.url_entry)

        # Add a label for the filename input
        self.filename_label = MDLabel(
            text="Name your file:",
            size_hint_y=None,
            height=dp(30),
            font_style="Subtitle1",
        )
        self.root.add_widget(self.filename_label)

        # Add a text input for the filename
        self.filename_entry = MDTextField(
            hint_text="Name your file here...",
            mode="fill",
            size_hint=(1, None),
            height=dp(40),
        )
        self.root.add_widget(self.filename_entry)

        # Add a convert button
        self.convert_btn = MDRaisedButton(
            text="convert!",
            size_hint=(1, None),
            height=dp(50),
            font_style="Button",
        )
        self.convert_btn.bind(on_press=lambda x: self.start_conversion())
        self.root.add_widget(self.convert_btn)

        # Add a label for displaying results
        self.result_label = MDLabel(
            text="",
            size_hint_y=None,
            height=dp(30),
            font_style="Body1",
        )
        self.root.add_widget(self.result_label)

        return self.root

    def start_conversion(self):
        # Access widgets directly
        url = self.url_entry.text
        filename = self.filename_entry.text

        # Validate inputs
        if not url or not filename:
            self.update_result_label("Please fill both fields!")
            return

        self.update_result_label("Starting conversion...")
        self.convert_btn.disabled = True  # Disable button during conversion

        # Start conversion in a new thread
        threading.Thread(target=self.convert_video, args=(url, filename)).start()

    def convert_video(self, url, filename):
        try:
            # Schedule folder selection in the main thread
            Clock.schedule_once(lambda dt: self.select_folder(url, filename))
        except Exception as e:
            self.update_result_label(f"Error during conversion: {str(e)}")

    def select_folder(self, url, filename, *args):
        # Create a file chooser for folder selection
        filechooser = FileChooserListView(path=os.path.expanduser("~"), dirselect=True)

        # Create a layout for the popup
        popup_layout = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(10))

        # Add the file chooser to the popup layout
        popup_layout.add_widget(filechooser)

        # Create a button layout for "Select" and "Cancel"
        button_layout = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        select_button = MDRaisedButton(text="Select", size_hint_x=0.5, font_style="Button")
        cancel_button = MDRaisedButton(text="Cancel", size_hint_x=0.5, font_style="Button")

        # Bind buttons to their respective actions
        select_button.bind(on_press=lambda x: self.on_folder_selected(filechooser.path, url, filename))
        cancel_button.bind(on_press=lambda x: self.popup.dismiss())

        # Add buttons to the button layout
        button_layout.add_widget(select_button)
        button_layout.add_widget(cancel_button)

        # Add the button layout to the popup layout
        popup_layout.add_widget(button_layout)

        # Create and open the popup
        self.popup = Popup(title="Select download folder", content=popup_layout, size_hint=(0.9, 0.9))
        self.popup.open()

    def on_folder_selected(self, folder_path, url, filename):
        if folder_path:
            # Set the selected folder path
            self.selected_folder = folder_path

            # Close the popup
            self.popup.dismiss()

            # Continue with the conversion process
            self.update_result_label("Downloading and converting...")
            threading.Thread(target=self.download_and_convert, args=(url, self.selected_folder, filename)).start()
        else:
            self.update_result_label("No folder selected!")

    def download_and_convert(self, url, download_folder, filename):
        try:
            # Ensure the download folder exists
            os.makedirs(download_folder, exist_ok=True)

            # Construct the output file path
            output_file = os.path.join(download_folder, filename + ".mp3")
            if not output_file:
                self.update_result_label("No file name selected!")
                return

            # Run the download and conversion
            video_file = self.download_vid(url, download_folder)
            if video_file:
                self.extract_audio(video_file, output_file)
                os.remove(video_file)

                # Extract folder name
                saving_route = os.path.basename(download_folder)

                # Display when download was successful plus where the file was saved
                self.update_result_label(f"Conversion done! Your file was saved in: {saving_route}")
                
                # Clear both URL & file name labels
                self.clear_input_fields()
            else:
                # Display error if something went wrong during the conversion
                self.update_result_label("Failed to download the video.")
        except Exception as e:
            self.update_result_label(f"Error during conversion: {str(e)}")
        finally:
            # Re-enable the convert button
            Clock.schedule_once(lambda dt: setattr(self.convert_btn, 'disabled', False))

    def download_vid(self, url, download_folder):
        ydl_options = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_folder, '%(id)s.%(ext)s'),  # Correct format for outtmpl
            'quiet': True,  # Suppress yt-dlp output
            'no_warnings': True,  # Suppress warnings
        }

        with YoutubeDL(ydl_options) as ydl:
            try:
                # Extract video info
                info_dict = ydl.extract_info(url, download=True)
                video_id = info_dict.get('id', None)
                ext = info_dict.get('ext', None)

                if not video_id or not ext:
                    raise Exception("Failed to extract video ID or extension.")

                # Construct the downloaded file path
                video_file = os.path.join(download_folder, f"{video_id}.{ext}")
                if not os.path.exists(video_file):
                    raise Exception(f"Failed to download {video_file}")

                return video_file
            except Exception as e:
                self.update_result_label(f"Error downloading video: {str(e)}")
                return None

    def extract_audio(self, video_file, output_file):
        try:
            # Convert the video file to MP3
            audio = AudioSegment.from_file(video_file)
            audio.export(output_file, format="mp3")
        except Exception as e:
            self.update_result_label(f"Error extracting audio: {str(e)}")

    def update_result_label(self, text):
        # Update the label in the main thread
        Clock.schedule_once(lambda dt: setattr(self.result_label, 'text', text))

    def clear_input_fields(self):
        Clock.schedule_once(lambda dt: setattr(self.url_entry, 'text', ''))
        Clock.schedule_once(lambda dt: setattr(self.filename_entry, 'text', ''))    

if __name__ == "__main__":
    ConvertApp().run()
