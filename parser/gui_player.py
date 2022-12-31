import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from PIL import Image, ImageTk
import csv
import os

class ImageViewer(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.pack(fill=tk.BOTH, expand=True)

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

        self.image = None  # Create the image attribute
        self.image_width = 0
        self.image_height = 0
        self.original_width = 1
        self.original_height = 1
        # Get the original size of the image
        # if hasattr(self, "image") and self.image is not None:
        #     self.original_width = self.image.width()
        #     self.original_height = self.image.height()
        # self.original_width = 100
        # self.original_height = 100

    def on_resize(self, event):
        # Calculate the new size of the image based on the aspect ratio
        aspect_ratio = self.original_width / self.original_height
        # new_width = event.width
        # new_height = int(event.width / aspect_ratio)

        # new_width = self.image_label.winfo_width()
        # new_height = self.image_label.winfo_height()

        # print("event", event.width, event.height)
        # print("label", new_width, new_height)

        # # Resize the image to fit the widget
        # # self.image = self.image.resize((new_width, new_height), Image.ANTIALIAS)
        # # Convert the PhotoImage to an Image object
        # # image = Image.frombytes(mode="RGB", size=(self.image.width(), self.image.height()),
        # #                         data=self.image.tostring())

        # # Resize the image
        # # image = image.resize((new_width, new_height), Image.ANTIALIAS)

        # # Convert the resized image back to a PhotoImage
        # # self.image = ImageTk.PhotoImage(image)

        # # Update the image size
        # self.image_width = new_width // 2
        # self.image_height = new_height

        # print("width // 2", self.image_width, self.image_height)

        # Update the size of the image
        # self.configure(width=new_width, height=new_height)
        # self.control_frame.configure(height=100)
        self.update_image()

    def create_widgets(self):
        # Create the image label
        self.image_label = tk.Label(self)
        self.image_label.pack(fill=tk.BOTH, expand=True)

        # Create the control frame
        self.control_frame = tk.Frame(self)
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        # set a size for the control frame
        self.control_frame.configure(height=200)

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

        self.update_image()
        self.progress_bar.config(maximum=len(self.images))
        self.paused = False
        self.speed = 1.0

    def update_image(self):
        # Load the current image pair
        left_image_path, right_image_path = self.images[self.current_index]
        left_image = Image.open(left_image_path)

        width, height = self.image_label.winfo_width() // 2 - 2, self.image_label.winfo_height() - 2
        print("width // 2", width, height)

        # height = height - self.control_frame.winfo_height()
        height = height - 50

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

root = tk.Tk()
app = ImageViewer(master=root)
app.mainloop()