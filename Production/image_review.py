import os
import tkinter as tk
from tkinter import Label, Button
from PIL import Image, ImageTk

# Folder containing images
image_folder = r"D:\AI_train_data\Train_Prod\unique_frames"
image_files = sorted([f for f in os.listdir(image_folder) if f.lower().endswith(".jpg")])

# Track current image index
current_index = 0

def update_image():
    """ Update the displayed image """
    global current_index, img_label, img_display

    img_path = os.path.join(image_folder, image_files[current_index])
    img = Image.open(img_path)
    img = img.resize((800, 600))  # Resize for display
    img_display = ImageTk.PhotoImage(img)

    img_label.config(image=img_display)
    root.title(f"Image Viewer - {image_files[current_index]}")

def next_image():
    """ Show the next image """
    global current_index
    if current_index < len(image_files) - 1:
        current_index += 1
        update_image()

def prev_image():
    """ Show the previous image """
    global current_index
    if current_index > 0:
        current_index -= 1
        update_image()

# Setup GUI Window
root = tk.Tk()
root.geometry("900x700")
root.title("Image Viewer")

# Display Image
img_display = None
img_label = Label(root)
img_label.pack()

# Buttons
btn_prev = Button(root, text="Previous", command=prev_image, width=15)
btn_prev.pack(side=tk.LEFT, padx=20, pady=10)

btn_next = Button(root, text="Next", command=next_image, width=15)
btn_next.pack(side=tk.RIGHT, padx=20, pady=10)

# Load first image
update_image()

root.mainloop()
