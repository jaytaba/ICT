# merges de duped images with transcript, summarizes all in one .pdf file

import os
from PIL import Image
import re
from fpdf import FPDF
import textwrap
import nltk
from nltk.tokenize import sent_tokenize
from transformers import pipeline

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('punkt_tab')

def extract_timestamp_seconds(filename):
    match = re.search(r'_(\d+)\.jpg$', filename)
    return int(match.group(1)) if match else None

def get_image_timestamps(image_folder, video_id):
    # Get all image timestamps for a video in sorted order
    timestamps = []
    images = {}
    for img in os.listdir(image_folder):
        if img.startswith(video_id) and img.endswith('.jpg'):
            timestamp = extract_timestamp_seconds(img)
            if timestamp is not None:
                timestamps.append(timestamp)
                images[timestamp] = img
    return sorted(timestamps), images

def process_transcript(transcript_file, image_timestamps):
    grouped_content = {}
    current_image_idx = 0
    current_group_texts = []
    
    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = re.finditer(r'\[(\d{2}):(\d{2})\](.*?)(?=\[\d{2}:\d{2}\]|$)', content, re.DOTALL)
            
            for match in matches:
                minutes = int(match.group(1))
                seconds = int(match.group(2))
                text = match.group(3).strip()
                current_timestamp = minutes * 60 + seconds

                while (current_image_idx < len(image_timestamps) - 1 and 
                       current_timestamp >= image_timestamps[current_image_idx + 1]):
                    if current_group_texts:
                        grouped_content[image_timestamps[current_image_idx]] = ' '.join(current_group_texts)
                        current_group_texts = []
                    current_image_idx += 1

                current_group_texts.append(text)

            if current_group_texts:
                grouped_content[image_timestamps[current_image_idx]] = ' '.join(current_group_texts)

    except Exception as e:
        print(f"Error processing transcript file: {str(e)}")
        return {}
    
    return grouped_content

def format_text(text):
    # Remove timestamps
    text = re.sub(r'\[\d{2}:\d{2}\]', '', text)
    
    # Capitalize first letter of sentences
    sentences = sent_tokenize(text)
    formatted_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            sentence = sentence[0].upper() + sentence[1:] if len(sentence) > 1 else sentence.upper()
            if not sentence[-1] in '.!?':
                sentence += '.'
            formatted_sentences.append(sentence)
    
    return ' '.join(formatted_sentences)

def generate_summary(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    max_chunk_length = 1024
    chunks = textwrap.wrap(text, max_chunk_length)
    
    summaries = []
    for chunk in chunks:
        summary = summarizer(chunk, max_length=130, min_length=30, do_sample=False)
        summaries.append(summary[0]['summary_text'])
    
    return ' '.join(summaries)

def create_pdf(image_folder, transcript_folder, output_pdf):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Store all formatted content first
    all_content = []  # Changed from dict to list to maintain order
    full_text = ""
    
    for transcript_file in sorted(os.listdir(transcript_folder)):  # Sort transcript files
        if not transcript_file.endswith('.txt'):
            continue
            
        video_id = os.path.splitext(transcript_file)[0]
        transcript_path = os.path.join(transcript_folder, transcript_file)
        
        # Get image timestamps and files
        image_timestamps, image_files = get_image_timestamps(image_folder, video_id)
        grouped_content = process_transcript(transcript_path, image_timestamps)
        
        # Format all text and store in chronological order
        for timestamp in sorted(grouped_content.keys()):  # Sort by timestamp
            text = grouped_content[timestamp]
            formatted_text = format_text(text)
            all_content.append({
                'key': f"{video_id}_{timestamp}",
                'timestamp': timestamp,
                'text': formatted_text,
                'image': image_files.get(timestamp)
            })
            full_text += formatted_text + " "
    
    # Sort content by timestamp
    all_content.sort(key=lambda x: (x['key'].split('_')[0], x['timestamp']))
    
    # Generate summary
    summary = generate_summary(full_text)
    
    # Start creating PDF
    # Add summary page
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Executive Summary", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", '', 12)
    lines = textwrap.wrap(summary, width=80)
    for line in lines:
        pdf.multi_cell(0, 10, line)
    
    # Add content pages in chronological order
    for content in all_content:
        pdf.add_page()
        
        # Add image if it exists
        if content['image']:
            img_path = os.path.join(image_folder, content['image'])
            if os.path.exists(img_path):
                pdf.image(img_path, x=10, y=pdf.get_y(), w=190)
                pdf.ln(140)  # Space after image
        
        # Add formatted text
        pdf.set_font("Arial", '', 12)
        lines = textwrap.wrap(content['text'], width=80)
        for line in lines:
            pdf.multi_cell(0, 10, line)
    
    pdf.output(output_pdf)


# Main execution
if __name__ == "__main__":
    image_folder = "D:\\AI_train_data\\Train_Prod\\unique_framesT"
    transcript_folder = "D:\\AI_train_data\\Train_Prod\\transcriptsT"
    output_pdf = "D:\\AI_train_data\\Train_Prod\\pdf_outputT\\output.pdf"
    
    create_pdf(image_folder, transcript_folder, output_pdf)
