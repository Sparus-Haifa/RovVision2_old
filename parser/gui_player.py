import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import csv
import os

CONTROL_FRAME_HEIGHT = 200

class ImageViewer(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)
        self.configure(width=300, height=300)

        # Set up the GUI
        self.create_widgets()

        # Initialize the state of the viewer
        self.current_index = 0
        self.images = []
        # self.update_image()
        self.paused = False
        self.speed = 1.0

        # Bind the resize event to the callback function
        self.bind("<Configure>", self.on_resize)

        # Get the original size of the image


    def on_resize(self, event):
        # Calculate the new size of the image based on the aspect ratio
        # aspect_ratio = self.original_width / self.original_height
        self.update_image()

    def create_widgets(self):
        # Create the image label
        self.image_label = tk.Label(self)
        self.image_label.pack(fill=tk.BOTH, expand=True)
        # set a size for the image label
        # self.image_label.configure(height=300, width=300)

        # Create the control frame
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=True)
        # set a size for the control frame
        self.control_frame.configure(height=CONTROL_FRAME_HEIGHT)

        # Create the "Open" button
        self.open_button = tk.Button(self.control_frame, text="Open", command=self.open_csv)
        self.open_button.pack(side="left")

        # Create the "Play/Pause" button
        self.play_pause_button = tk.Button(self.control_frame, text="Play", command=self.play_pause)
        self.play_pause_button.pack(side="left")

        # Create the "Fast Forward" button
        self.fast_forward_button = tk.Button(self.control_frame, text=">>", command=self.fast_forward)
        self.fast_forward_button.pack(side="left")

        # Create the "Rewind" button
        self.rewind_button = tk.Button(self.control_frame, text="<<", command=self.rewind)
        self.rewind_button.pack(side="left")

        # Create the speed scale
        self.speed_scale = tk.Scale(self.control_frame, from_=1.0, to=1000.0, resolution=1.0, orient="horizontal", command=self.set_speed)
        self.speed_scale.pack(side="left")

        # Create the progress bar
        self.progress_bar = ttk.Progressbar(self.control_frame, orient="horizontal", length=200)
        self.progress_bar.pack(side=tk.TOP, fill=tk.X, expand=True)

        # Create the seeker
        self.seeker = ttk.Scale(self.control_frame, from_=0, to=100, orient='horizontal', command=self.show_image_at_index)
        self.seeker.pack(side='bottom', fill=tk.X, expand=True)

        # Create the status label
        self.status_label = tk.Label(self.control_frame, text="Status")
        self.status_label.pack(side="bottom", fill=tk.X)

        # Create an index label
        self.index_label = tk.Label(self.control_frame, text="Index")
        self.index_label.pack(side="bottom", fill=tk.X)

    def show_image_at_index(self, index):
        pass

    def open_csv(self):
        # Open a file dialog to select the CSV file
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

        # Get the directory of the CSV file
        main_path = os.path.dirname(filepath)

        # Read the image pairs from the CSV file
        with open(filepath, "r") as f:
            reader = csv.reader(f)
            headers = next(reader)
            for row in reader:
                index, flc, fls, bagfile = row
                flc_filename = f"{int(flc):08d}.tiff"
                fls_filename = f"{int(fls):08d}.tiff"
                self.images.append((os.path.join(main_path, bagfile, "imgs", flc_filename), os.path.join(main_path, bagfile, "imgs", fls_filename)))


        # Reset the state of the viewer
        self.current_index = 0
        # get image size from first image
        # first_image = Image.open(self.images[0][0])
        # self.original_width, self.original_height = first_image.size
        # self.image_width = self.original_width
        # self.image_height = self.original_height

        # self.image_label.configure(width=300, height=300)

        self.update_image()
        self.progress_bar.config(maximum=len(self.images))
        self.seeker.config(to=len(self.images))
        self.paused = False
        self.speed = 1.0

    def update_image(self):
        if not self.images:
            return

        # Load the current image pair
        left_image_path, right_image_path = self.images[self.current_index]
        left_image = Image.open(left_image_path)

        label_width = self.image_label.winfo_width()
        label_height = self.image_label.winfo_height()
        print("label_width", label_width, label_height)


        width = label_width // 2 - 2
        height = label_height - 2
        print("width // 2", width, height)

        # print("control_frame", self.control_frame.winfo_width(), self.control_frame.winfo_height())
        # if self.control_frame.winfo_height() < CONTROL_FRAME_HEIGHT:
        #     self.control_frame.configure(height=CONTROL_FRAME_HEIGHT)


        # height = height - self.control_frame.winfo_height()
        # height = max(height - 50, 50)
        height = max(height - 78 + self.control_frame.winfo_height(), 50)

        print("control_frame", self.control_frame.winfo_width(), self.control_frame.winfo_height())
        # if self.control_frame.winfo_height() < 78:
        #     self.control_frame.configure(height=78)
        #     height = height - 78

        # resize image
        left_image = left_image.resize((width, height), Image.ANTIALIAS)

        right_image = Image.open(right_image_path)

        # resize image
        right_image = right_image.resize((width, height), Image.ANTIALIAS)

    # Combine the images into a single image
        # width, height = left_image.size
        # width, height = self.image_width, self.image_height
        combined_image = Image.new("RGB", (width * 2, height))
        combined_image.paste(left_image, (0, 0))
        combined_image.paste(right_image, (width, 0))

        # Convert the image to a PhotoImage object
        self.image = ImageTk.PhotoImage(combined_image)

        # Update the image label with the new image
        self.image_label.config(image=self.image)

    def play_pause(self):
        if self.paused:
            # Change the button text to "Pause" and start the update loop
            self.play_pause_button.config(text="Pause")
            self.paused = False
            self.update_loop()
        else:
            # Change the button text to "Play" and stop the update loop
            self.play_pause_button.config(text="Play")
            self.paused = True

    def fast_forward(self):
        # Advance to the next image
        self.current_index = (self.current_index + 1) % len(self.images)
        self.update_image()
        self.update_progress()

    def rewind(self):
        # Go back to the previous image
        self.current_index = (self.current_index - 1) % len(self.images)
        self.update_image()
        self.update_progress()

    def set_speed(self, event):
        # Update the speed based on the value of the speed scale
        self.speed = float(event)

    def update_loop(self):
        if not self.paused:
            # Advance to the next image
            self.current_index = (self.current_index + 1) % len(self.images)
            self.update_image()
            self.update_progress()

            # Schedule the next update
            self.after(int(1000 / self.speed), self.update_loop)

    def update_progress(self):
        # Update the progress bar with the current image index
        self.progress_bar.config(value=self.current_index)
        self.seeker.set(self.current_index)
        self.index_label.config(text=f"Index: {self.current_index}")

root = tk.Tk()
app = ImageViewer(master=root)
app.mainloop()