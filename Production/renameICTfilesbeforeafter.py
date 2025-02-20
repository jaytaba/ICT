import os
import re

folder_path = r"D:\AI_train_data\Train_Prod\transcripts"

def rename_file(old_name):
    # Extract numeric month and title using a more flexible approach
    match = re.search(r"(\d{1,2})\s*-\s*ICT Mentorship Core Content\s*-\s*Month\s*(\d{1,2})\s*-\s*(.+?)\.txt", old_name, re.IGNORECASE)
    
    if match:
        original_number = match.group(1)  # The first number in filename
        month_number = match.group(2)  # Month extracted from "Month XX"
        title = match.group(3).strip()

        # Create an abbreviation from title
        abbr = ''.join(word[0] for word in title.split() if word[0].isalpha()).upper()
        
        # Construct new filename
        new_name = f"{month_number}-{abbr}.txt"
        return new_name
    return None

# Iterate through the directory and rename files
for file in os.listdir(folder_path):
    if file.endswith(".txt"):
        new_name = rename_file(file)
        if new_name:
            old_path = os.path.join(folder_path, file)
            new_path = os.path.join(folder_path, new_name)

            # Print old and new names for debugging
            print(f'Renaming: "{file}" -> "{new_name}"')

            os.rename(old_path, new_path)

print("Renaming complete.")
