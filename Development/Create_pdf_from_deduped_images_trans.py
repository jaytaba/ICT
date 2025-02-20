# this code will read dedubed images from transcriptsT and deduped images from
# Unique_framesT folder and creates .pdf
import os
import re
from datetime import datetime
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

# Configure directories
BASE_DIR = r'D:\\AI_train_data\\Train_Prod'
TRANSCRIPT_DIR = os.path.join(BASE_DIR, 'transcriptsT')
UNIQUE_FRAMES_DIR = os.path.join(BASE_DIR, 'unique_framesT')
PDF_OUTPUT_DIR = os.path.join(BASE_DIR, 'pdf_outputT')

def parse_session_time(timestamp):
    """Convert timestamp to trading session context"""
    hour = (timestamp // 3600) % 24
    if 4 <= hour < 9:    return "Premarket"
    if 9 <= hour < 16:   return "Regular Session"
    if 16 <= hour < 20:  return "Afterhours"
    return "Extended Hours"

def process_transcript(transcript_file):
    """Process transcript file with existing frames"""
    base_name = os.path.splitext(transcript_file)[0]
    os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)
    
    # Extract timestamps and text
    transcript_path = os.path.join(TRANSCRIPT_DIR, transcript_file)
    entries = extract_timestamps_and_text(transcript_path)
    
    # Group entries by existing frames
    frame_entries = group_entries_by_frames(entries)
    
    create_pdf(base_name, frame_entries)

def extract_timestamps_and_text(transcript_path):
    """Extract timestamps and text using improved regex"""
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

def group_entries_by_frames(entries):
    """Group text entries by existing frame files"""
    frame_entries = {}
    
    # Get all existing frame files
    frame_files = {
        os.path.splitext(f)[0]: os.path.join(UNIQUE_FRAMES_DIR, f)
        for f in os.listdir(UNIQUE_FRAMES_DIR)
        if f.endswith('.jpg')
    }
    
    for entry in entries:
        # Frame files are named with their hash, we'll match by timestamp
        # This assumes frame files contain timestamp in their name
        frame_hash = f"{entry['timestamp']}"
        if frame_hash in frame_files:
            if frame_hash not in frame_entries:
                frame_entries[frame_hash] = {
                    'image_path': frame_files[frame_hash],
                    'texts': [entry['text']],
                    'timestamp': entry['timestamp']
                }
            else:
                frame_entries[frame_hash]['texts'].append(entry['text'])
    
    return list(frame_entries.values())

def create_pdf(base_name, image_entries):
    """Generate PDF with trading analysis layout"""
    pdf_path = os.path.join(PDF_OUTPUT_DIR, f"{base_name}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Image dimensions for trading charts
    img_width = 6.5 * inch
    img_height = 4 * inch
    
    # Custom styles for financial analysis
    signal_style = ParagraphStyle(
        name='SignalText',
        parent=styles['Normal'],
        fontSize=11,
        leading=13,
        textColor=colors.darkgreen,
        spaceAfter=6
    )
    
    timestamp_style = ParagraphStyle(
        name='Timestamp',
        parent=styles['Heading4'],
        textColor=colors.navy,
        fontSize=12
    )

    # PDF Header with market context
    story.append(Paragraph("<b>Advanced Price Action Analysis</b>", styles['Heading1']))
    story.append(Spacer(1, 0.25*inch))

    for entry in image_entries:
        # Add price chart image
        img = PDFImage(entry['image_path'], 
                      width=img_width,
                      height=img_height,
                      kind='proportional',
                      hAlign='CENTER')
        story.append(img)
        
        # Session time analysis
        session = parse_session_time(entry['timestamp'])
        story.append(Paragraph(
            f"Market Session: <b>{session}</b> | "
            f"Chart Time: {datetime.utcfromtimestamp(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}",
            timestamp_style
        ))
        
        # Key technical observations
        story.append(Paragraph("<b>Technical Observations:</b>", signal_style))
        for text in entry['texts']:
            cleaned_text = text.replace('\n', ' ').strip()
            story.append(Paragraph(f"• {cleaned_text}", signal_style))
        
        story.append(Spacer(1, 0.3*inch))

    doc.build(story)
    print(f"Generated professional trading PDF: {pdf_path}")

def main():
    """Process all transcripts in directory"""
    for transcript_file in os.listdir(TRANSCRIPT_DIR):
        if transcript_file.endswith('.txt'):
            try:
                process_transcript(transcript_file)
            except Exception as e:
                print(f"Error processing {transcript_file}: {str(e)}")

if __name__ == "__main__":
    main()