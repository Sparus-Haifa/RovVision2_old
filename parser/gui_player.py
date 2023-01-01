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
        self.file_path = None
        self.sections_file_path = None
        self.sections = []
        # Set the indices of the markers
        # self.marker_indices = []
        # self.update_image()
        self.paused = True
        self.speed = 1.0

        # Bind the resize event to the callback function
        self.bind("<Configure>", self.on_resize)

        # Bind the <Left> and <Right> events to the functions
        # self.bind_all('<KeyPress-Left>', self.show_previous_image)
        # self.bind_all('<KeyPress-Right>', self.show_next_image)

        # self.start_keypresses()

        self.bind_all('<KeyPress-Left>', self.show_previous_image)
        self.bind_all('<KeyPress-Right>', self.show_next_image)


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
        # self.progress_bar = ttk.Progressbar(self.control_frame, orient="horizontal", length=200)
        # self.progress_bar.pack(side=tk.TOP, fill=tk.X, expand=True)

        # Create a seeker frame
        self.seeker_frame = tk.Frame(self)
        self.seeker_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=True)

        # Create the canvas to draw the markers on
        self.canvas = tk.Canvas(self.seeker_frame, width=400, height=20)
        self.canvas.pack(side='bottom', fill=tk.X, expand=True)


        # Create the seeker
        self.seeker = ttk.Scale(self.seeker_frame, from_=0, to=100, orient='horizontal', command=self.show_image_at_index)
        self.seeker.pack(side='bottom', fill=tk.X, expand=True)

        # Bind the <Configure> event to the seeker
        self.seeker.bind('<Configure>', self.draw_markers)

        # Create the status label
        # self.status_label = tk.Label(self.control_frame, text="Status")
        # self.status_label.pack(side="bottom", fill=tk.X)

        # Create an index label
        self.index_label = tk.Label(self.control_frame, text="")
        self.index_label.pack(side="right")

        # Create a Enable/Disable sections button
        self.enable_disable_button = tk.Button(self.control_frame, text="Enable/Disable Sections", command=self.enable_disable_sections)
        self.enable_disable_button.pack(side="right")
        # Set the initial state of the button as disabled
        self.enable_disable_button.configure(state="disabled")

    # Create a function to open the sections csv file
    def enable_disable_sections(self):
        print("enable_disable_sections")
        # Open the csv file
        main_path = os.path.dirname(self.file_path)
        sections_file_path = os.path.join(main_path, "sections.csv")
        with open(sections_file_path) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            # Skip the header
            next(csv_reader)
            for row in csv_reader:
                print(row)
                # Get the start and end indices of the section
                start_index = int(row[2])
                end_index = int(row[3])
                # Get the recording name
                recording_name = row[1] 
                self.sections.append((start_index, end_index, recording_name))

        # Update markers
        self.draw_markers(None)



    def draw_markers(self, event):
        print("draw_markers")
        # Clear the canvas
        self.canvas.delete('all')
        # Calculate the width and height of the seeker
        width = self.seeker.winfo_width()
        height = self.seeker.winfo_height()
        # Calculate the distance between each marker
        marker_distance = width / (len(self.images) - 1)
        # marker_distance = min(width / (len(self.images) - 1), 2)
        # marker_distance = width / (6 - 1)

        # Draw a vertical line at each marker index
        # for index in marker_indices:
        # for index in range(len(self.images)):
        for section in self.sections:
            start_index = section[0]
            end_index = section[1]

            # x = index * marker_distance
            # self.canvas.create_line(x, 0, x, height, fill='red')
            self.canvas.create_rectangle(start_index * marker_distance, 0, end_index * marker_distance, height, fill='red')

    def show_image_at_index(self, index):
        print("show_image_at_index")
        # Get the index of the image to show
        self.current_index = int(float(index))
        # Update the image
        self.update_image()
        self.update_index_label()

    def open_csv(self):
        # Open a file dialog to select the CSV file
        self.file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])

        # Get the directory of the CSV file
        main_path = os.path.dirname(self.file_path)

        # Read the image pairs from the CSV file
        with open(self.file_path, "r") as f:
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
        # self.progress_bar.config(maximum=len(self.images))
        # self.update_index_label()
        self.update_progress()
        # Enable the enable/disable sections button
        self.enable_disable_button.config(state="normal")

        self.seeker.config(to=len(self.images))
        self.paused = True
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

        # Process any pending idle tasks before updating the label
        self.update_idletasks()

    def play_pause(self):
        if self.paused:
            self.paused = False
            self.play_pause_button.config(text="Pause")
        else:
            self.paused = True
            self.play_pause_button.config(text="Play")



    def show_previous_image(self, event=None):
        # Go back to the previous image
        if not self.images:
            return
        self.current_index = (self.current_index - 1) % len(self.images)
        self.update_image()
        self.update_progress()
        

    def show_next_image(self, event=None):
        # Advance to the next image
        if not self.images:
            return
        self.current_index = (self.current_index + 1) % len(self.images)
        self.update_image()
        self.update_progress()



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
        # self.progress_bar.config(value=self.current_index)
        self.seeker.set(self.current_index)
        self.update_index_label()

    def update_index_label(self):
        self.index_label.config(text=f"Index: {self.current_index}")

root = tk.Tk()
app = ImageViewer(master=root)
app.mainloop()