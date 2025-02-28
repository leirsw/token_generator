import streamlit as st

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import io



st.title("Token Generator")


if 'token' not in st.session_state:
    st.session_state.token = None


col1, col2 = st.columns([1, 2])
with col1:
    uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

    is_clicked_generate = st.button("Generate Token")
    
with col2:
    subcol1, subcol2 = st.columns([1, 1])
    with subcol1:
        name = st.text_input("Name")
    with subcol2:
        dual_name = st.checkbox("Dual name")
    size = st.selectbox("Size", ['tiny', 'small', 'medium', 'large', 'huge', 'gargantuan'])
    token_type = st.selectbox("Type", ['tabletop', 'initiative'])


def create_token(image_path, size='medium', token_type='tabletop', name=None, dual_name = False):
    """Create a token from an image
    
    Args:
        image_path: str or PIL Image
        size: 'tiny', 'small', 'medium', 'large', 'huge', 'gargantuan'
        token_type: 'tabletop' or 'initiative'
        name: str, optional name for initiative tracker
    """
    # Size definitions in mm
    DND_SIZES = {
        'tiny': 12.7,    # 0.5 inch
        'small': 25.4,   # 1 inch
        'medium': 25.4,  # 1 inch
        'large': 50.8,   # 2 inches
        'huge': 76.2,    # 3 inches
        'gargantuan': 101.6  # 4 inches
    }

    if token_type == 'initiative':  # Initiative tracker is always large. I might experiment with huge for a big boss but think that would be overkill
        size = 'large'

    
    # Load image
    if isinstance(image_path, str):
        img = Image.open(image_path)
    else:
        img = image_path
    
    # Convert mm to pixels (adjusting DPI to 150 for more accurate physical size)
    DPI = 100  # Changed from 300 to 150 to 75
    MM_TO_INCHES = 1/25.4
    pixels_per_mm = DPI * MM_TO_INCHES
    
    # Get token dimensions
    token_width_mm = DND_SIZES[size.lower()]
    token_width_px = int(token_width_mm * pixels_per_mm)
    
    # Add white base area for cuts (10mm extra)
    base_height_mm = 10 
    base_height_px = int(base_height_mm * pixels_per_mm)
    
    if token_type == 'tabletop':
        image_height_px = token_width_px  # Square image area
    else:
        image_height_px = token_width_px # Taller for initiative
        # Add small gap for fold (2mm)
        fold_gap_mm = 2
        fold_gap_px = int(fold_gap_mm * pixels_per_mm)
    
    # Resize image maintaining aspect ratio
    aspect = img.width / img.height
    new_width = token_width_px
    new_height = int(token_width_px / aspect)
    
    if new_height > image_height_px:
        new_height = image_height_px
        new_width = int(image_height_px * aspect)
    
    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Create canvas
    margin_px = 1
    canvas_width = token_width_px + 2 * margin_px
    
    if token_type == 'tabletop':
        canvas_height = 2 * (image_height_px + margin_px) + 2 * base_height_px
    else:
        canvas_height = int(2.8 * (image_height_px + margin_px + fold_gap_px))
    
    canvas = Image.new('RGB', (canvas_width, canvas_height), 'white')
    draw = ImageDraw.Draw(canvas)
    
    # Calculate image positions
    image_x = margin_px + (token_width_px - new_width) // 2
    
    if token_type == 'tabletop':
        # First image upside down, with base BELOW it
        image_y1 = canvas_height//2 - margin_px - image_height_px
        canvas.paste(img.rotate(180), (image_x, image_y1))
        
        # Second image normal orientation, with base BELOW it
        image_y2 = canvas_height//2 + margin_px
        canvas.paste(img, (image_x, image_y2))
    else:
        # For initiative tracker
        image_y1 = canvas_height//2 - image_height_px - fold_gap_px
        canvas.paste(img.rotate(180), (image_x, image_y1))
        
        image_y2 = canvas_height//2 + fold_gap_px
        canvas.paste(img, (image_x, image_y2))
        
        # Add name text (larger font)
        if name:

            font = ImageFont.load_default(int(token_width_mm / 2))
            
            # Bottom side name
            text_y = image_y2 + new_height + margin_px
            text_width = draw.textlength(name, font=font)
            text_x = margin_px + (token_width_px - text_width) // 2
            draw.text((text_x, text_y), name, fill='black', font=font)

            if dual_name:
                # Top side name (upside down)
                # Create a new image just for the text
                font_height = int(token_width_mm / 2 * pixels_per_mm)
                text_img = Image.new('RGB', (canvas_width, font_height), 'white')
                text_draw = ImageDraw.Draw(text_img)
                
                # Draw text centered on the new image
                text_x = (canvas_width - text_width) // 2
                text_draw.text((text_x, 0), name, fill='black', font=font)
                
                # Rotate the text image 180 degrees
                text_img = text_img.rotate(180)
                
                # Calculate position for the top text (just above the top image)
                text_y_top = image_y1 - font_height - margin_px
                
                # Paste the rotated text onto the main canvas
                canvas.paste(text_img, (0, text_y_top))


    
    # Draw fold line
    fold_y = canvas_height // 2
    for x in range(0, canvas_width, 6):
        draw.line([(x, fold_y), (x + 3, fold_y)], fill='grey', width=1)
    
    # Draw cut lines (only on bottom white area)
    if token_type == 'tabletop':
        base_y = canvas_height - margin_px
        cut_depth = int(9 * pixels_per_mm) - margin_px
        
        # Three evenly spaced cuts
        for x_ratio in [0.33, 0.66]:
            x = canvas_width * x_ratio
            draw.line([(x, base_y), (x, base_y - cut_depth)],
                     fill='grey', width=1)
            draw.line([(x, margin_px), (x, margin_px + cut_depth)],
                     fill='grey', width=1)
            
    
    # Draw outer border
    draw.rectangle([margin_px, margin_px, 
                   canvas_width-margin_px, canvas_height-margin_px],
                  outline='grey', width=1)
    
    return canvas




if is_clicked_generate:
    if uploaded_file:
        # Get uploaded file
        image = Image.open(uploaded_file)
        
        # Create token
        token = create_token(
            image,
            size,
            token_type,
            name if name else None,
            dual_name
        )
        
        st.session_state.token = token
        # Display token
        # st.image(token)

if st.session_state.token:
    st.image(st.session_state.token)


    # Create filename
    tokenname = name if name else "token"
    tokentype = 'tt' if token_type == 'tabletop' else 'init'
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"../generated_tokens/{tokenname}_{tokentype}_{timestamp}.png"

    buf = io.BytesIO()
    st.session_state.token.save(buf, format="PNG")
    buf.seek(0)

            # Provide download button
    st.download_button(
        label="Download Token",
        data=buf,
        file_name=filename,
        mime="image/png"
    )


