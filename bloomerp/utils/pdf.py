from xhtml2pdf import pisa
import requests
import os
from io import BytesIO

def fetch_image(image_url):
    """Helper function to download image from a URL and save it temporarily."""
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            # Save the image temporarily in memory
            temp_image_path = os.path.join(os.getcwd(), "temp_image.jpg")
            with open(temp_image_path, 'wb') as img_file:
                img_file.write(response.content)
            return temp_image_path
        return None
    except Exception as e:
        print(f"Error fetching image: {e}")
        return None

def link_callback(uri, rel):
    """Link callback function to handle external images."""
    if uri.startswith("http://") or uri.startswith("https://"):
        # If the URI is an external image, fetch and return its local path
        return fetch_image(uri)
    else:
        # If it's a local file path, resolve it and return
        return uri

def generate_pdf(
        html_content:str, 
        css_content:str|None=None,
        font_url=None, 
        page_margin=1, 
        is_landscape=False
        )->bytes:
    '''Generate a PDF from HTML content with optional CSS styling and custom font.'''

    # Adjust the page margin and orientation via inline CSS
    orientation = "landscape" if is_landscape else "portrait"

    # Define the CSS for the PDF
    if not css_content:
        css_content = ""

    css = f"""
    <style>
        @page {{
            size: {orientation};
            margin: {page_margin}in;

            
        }}
        body {{
            font-family: 'CustomFont', sans-serif;
        }}

        {css_content}

    </style>
    """

    # Add Google Fonts embedding if a font URL is provided
    if font_url:
        css += f"<link href='{font_url}' rel='stylesheet'>"

    # Define the footer HTML
    footer_html = ""

    # Combine CSS with the HTML content
    full_html = css + html_content + footer_html

    # Create an in-memory buffer
    pdf_buffer = BytesIO()

    # Create the PDF using xhtml2pdf's pisa
    pisa_status = pisa.CreatePDF(
        src=full_html,
        dest=pdf_buffer,
        link_callback=link_callback  # For handling images from URLs
    )

    # Check if the PDF was generated successfully
    if pisa_status.err:
        print("Error occurred while creating PDF")
        return None
    else:
        print("PDF generated successfully")
        pdf_buffer.seek(0)  # Move the buffer cursor to the beginning
        return pdf_buffer.getvalue()