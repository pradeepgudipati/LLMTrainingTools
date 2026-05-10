import os

from werkzeug.utils import secure_filename

# Save file to folder
def save_file(file, folder):
    filename = secure_filename(file.filename)
    if not os.path.exists(folder):
        os.makedirs(folder)
        print("Directory ", folder, " Created ")
    file_path = os.path.join(folder, filename)
    file.save(file_path)
    return file_path
