import os
import re
import cv2
import hashlib
from datetime import datetime
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Image as PDFImage,
    Paragraph,
    Spacer
)
import shutil
import imagehash

# Updated directories with 'T' suffix
BASE_DIR = r'D:\\AI_train_data\\Train_Prod'
TRANSCRIPT_DIR = os.path.join(BASE_DIR, 'transcriptsT')
VIDEO_DIR = os.path.join(BASE_DIR, 'videosT')
FRAMES_DIR = os.path.join(BASE_DIR, 'framesT')
UNIQUE_FRAMES_DIR = os.path.join(BASE_DIR, 'unique_framesT')
PDF_OUTPUT_DIR = os.path.join(BASE_DIR, 'pdf_outputT')

def extract_timestamps_and_text(transcript_path):
    """Extract timestamps and associated text with improved regex"""
    timestamp_pattern = r'\[(\d{2}:\d{2}(?::\d{2})?)\]\s*(.*?)(?=\[|$)'
    entries = []
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        content = f.read()
        matches = re.findall(timestamp_pattern, content, re.DOTALL)
        
        for match in matches:
            timestamp, text = match
            time_parts = list(map(int, timestamp.split(':')))
            total_seconds = sum(
                part * 60**i for i, part in enumerate(reversed(time_parts))
            )
            
            entries.append({
                'timestamp': total_seconds,
                'text': text.strip()
            })
    
    return entries

def extract_frame(video_path, timestamp_seconds, output_path):
    """Extracts frame at specified timestamp using OpenCV with error handling"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error opening video: {video_path}")
        return False
    
    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_seconds * 1000)
    success, frame = cap.read()
    
    if success:
        cv2.imwrite(output_path, frame)
        return True
    print(f"Failed to extract frame at {timestamp_seconds}s from {video_path}")
    return False

def parse_session_time(timestamp):
    """Convert timestamp to trading session context"""
    hour = (timestamp // 3600) % 24
    if 4 <= hour < 9:    return "Premarket"
    if 9 <= hour < 16:   return "Regular Session"
    if 16 <= hour < 20:  return "Afterhours"
    return "Extended Hours"

def process_video_transcript_pair(transcript_file, video_file):
    """Process video/transcript pair with enhanced error handling"""
    base_name = os.path.splitext(transcript_file)[0]
    
    # Create directories with validation
    for dir_path in [
        os.path.join(FRAMES_DIR, base_name),
        UNIQUE_FRAMES_DIR,
        PDF_OUTPUT_DIR
    ]:
        os.makedirs(dir_path, exist_ok=True)

    # Process timestamps and text
    transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_file)
    video_path = os.path.join(VIDEO_DIR, video_file)
    entries = extract_timestamps_and_text(transcript_path)
    
    unique_entries = {}
    for entry in entries:
        try:
            frame_filename = f"{base_name}_{entry['timestamp']}.jpg"
            output_path = os.path.join(FRAMES_DIR, base_name, frame_filename)
            
            if extract_frame(video_path, entry['timestamp'], output_path):
                with Image.open(output_path) as img:
                    frame_hash = str(imagehash.average_hash(img, hash_size=16))
                    
                unique_path = os.path.join(UNIQUE_FRAMES_DIR, f"{frame_hash}.jpg")
                if frame_hash not in unique_entries:
                    shutil.copy(output_path, unique_path)
                    unique_entries[frame_hash] = {
                        'image_path': unique_path,
                        'texts': [entry['text']],
                        'timestamp': entry['timestamp']
                    }
                else:
                    unique_entries[frame_hash]['texts'].append(entry['text'])
                    
        except Exception as e:
            print(f"Error processing {entry['timestamp']}: {str(e)}")
            continue
#adding the nest 4 lines for debugging
print(f"Processing {len(image_entries)} unique chart patterns")
for entry in image_entries:
    print(f"Found frame: {entry['image_path']}")
    print(f"Associated texts: {entry['texts']}")


    create_pdf(base_name, list(unique_entries.values()))

def create_pdf(base_name, image_entries):
    pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{base_name}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    
    # Trading-specific styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='ChartNote',
        fontSize=10,
        textColor=colors.darkblue,
        leading=14
    ))
    
    story = []
    
    # Market Session Header
    story.append(Paragraph("<b>Price Action Analysis Report</b>", styles['Heading1']))
    story.append(Spacer(1, 12))
    
    if not image_entries:
        story.append(Paragraph("<i>No significant chart patterns identified</i>", styles['Italic']))
    else:
        # Technical Analysis Content
        for idx, entry in enumerate(image_entries, 1):
            # Chart Pattern Image
            story.append(Paragraph(f"Pattern {idx}:", styles['Heading3']))
            story.append(PDFImage(
                entry['image_path'],
                width=6*inch,
                height=3.5*inch
            ))
            
            # Timeframe Analysis
            session = parse_session_time(entry['timestamp'])
            story.append(Paragraph(
                f"Session: {session} | "
                f"Timestamp: {datetime.utcfromtimestamp(entry['timestamp']).strftime('%Y-%m-%d %H:%M')}",
                styles['ChartNote']
            ))
            
            # Key Observations
            story.append(Paragraph("Market Observations:", styles['Heading4']))
            for text in entry['texts']:
                story.append(Paragraph(f"• {text}", styles['Bullet']))
            
            story.append(Spacer(1, 24))

    doc.build(story)
    print(f"Generated PDF with {len(image_entries)} chart patterns")


def main():
    """Main execution with improved file handling"""
    with open(os.path.join(BASE_DIR, 'ListTT.txt'), 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            try:
                transcript_file, video_file = line.split('|')
                process_video_transcript_pair(
                    transcript_file.strip(),
                    video_file.strip()
                )
            except ValueError:
                print(f"Invalid line format: {line}")
            except FileNotFoundError as e:
                print(f"File error: {str(e)}")

if __name__ == "__main__":
    main()