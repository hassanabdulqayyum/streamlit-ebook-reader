import streamlit as st
import ebooklib
from ebooklib import epub
from lxml import etree
from io import BytesIO
import tempfile
import os
import nltk

# Ensure NLTK resources are downloaded
nltk.download('punkt', quiet=True)

def get_processed_elements(xhtml_content):
    """
    Processes the XHTML content using lxml to generate an ordered list of elements,
    preserving the document structure. Elements include headings, paragraphs,
    images with captions, etc.
    """
    parser = etree.XMLParser(recover=True)
    tree = etree.fromstring(xhtml_content, parser=parser)

    # Namespace handling (EPUB content often uses namespaces)
    namespaces = {'xhtml': 'http://www.w3.org/1999/xhtml'}

    # Using XPath to select elements
    body = tree.xpath('/xhtml:html/xhtml:body', namespaces=namespaces)
    if not body:
        return []
    body = body[0]

    # Extract elements in order
    elements = []
    for elem in body.iter():
        tag = etree.QName(elem).localname
        if tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements.append({
                'type': 'heading',
                'level': int(tag[1]),  # Extract level from tag name
                'content': ''.join(elem.itertext()).strip()
            })
        elif tag == 'p':
            # Get the text content, including tail text
            content = ''.join(elem.itertext()).strip()
            # Skip empty paragraphs
            if content:
                elements.append({
                    'type': 'paragraph',
                    'content': content
                })
        elif tag == 'img':
            # Handle images, possibly extract src and alt text
            src = elem.get('src')
            alt = elem.get('alt', '')
            elements.append({
                'type': 'image',
                'src': src,
                'alt': alt
            })
        elif tag == 'figure':
            # Handle figures (images with captions)
            img_elem = elem.find('.//xhtml:img', namespaces=namespaces)
            caption_elem = elem.find('.//xhtml:figcaption', namespaces=namespaces)
            if img_elem is not None:
                src = img_elem.get('src')
                alt = img_elem.get('alt', '')
                caption = ''.join(caption_elem.itertext()).strip() if caption_elem is not None else ''
                elements.append({
                    'type': 'figure',
                    'src': src,
                    'alt': alt,
                    'caption': caption
                })
        # You can add more handling for other tags like lists, tables, etc.

    return elements

def display_elements(element_index, elements):
    """
    Displays three elements at a time, highlighting the middle one if it's a paragraph.
    Other elements like headings, images, and captions are displayed appropriately.
    """
    # Extract the three elements to be displayed
    display_elements = elements[max(element_index-1, 0):element_index+2]

    html_content = ""

    for i, elem in enumerate(display_elements):
        # Define base font style for readability
        font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 1000px;
            margin: 10px auto;
            padding: 15px;
            border: 1px solid var(--primary-color);
            transition: text-shadow 0.5s;
        """

        # Highlight the middle element (or first if at the beginning) if it's a paragraph
        is_highlighted = (element_index == 0 and i == 0) or (element_index != 0 and i == 1)
        is_paragraph = elem['type'] == 'paragraph'

        if elem['type'] == 'heading':
            # Render headings with appropriate sizes
            heading_style = f"""
                font-size: {28 - elem['level'] * 2}px;
                font-weight: bold;
                margin-top: {20 - elem['level'] * 2}px;
            """
            html_content += f"<div style='{heading_style}'>{elem['content']}</div>"
        elif elem['type'] == 'paragraph':
            paragraph_text = elem['content']
            if is_highlighted and is_paragraph:
                # Use NLTK to split sentences accurately
                sentences = nltk.tokenize.sent_tokenize(paragraph_text)
                highlighted_sentences = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{j % 5 + 1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                        position: relative;
                        z-index: 1;
                    """
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif elem['type'] == 'image':
            # Display images
            img_html = f"<img src='data:image;base64,{get_base64_data(elem['src'])}' alt='{elem['alt']}' style='max-width:100%; height:auto;'>"
            html_content += f"<div style='text-align:center;'>{img_html}</div>"
        elif elem['type'] == 'figure':
            # Display figures with captions
            img_html = f"<img src='data:image;base64,{get_base64_data(elem['src'])}' alt='{elem['alt']}' style='max-width:100%; height:auto;'>"
            caption_html = f"<div style='font-size:16px; color:grey;'>{elem['caption']}</div>"
            html_content += f"<div style='text-align:center;'>{img_html}{caption_html}</div>"
        # Handle other types as needed

    # Display the HTML content using Streamlit
    st.write(html_content, unsafe_allow_html=True)

def get_base64_data(src):
    """
    Helper function to get base64 encoded data for images.
    """
    # This function assumes that 'src' is the path to the image within the EPUB package.
    # You'll need to extract the image data from the EPUB file.
    # For simplicity, this function returns an empty string.
    # You would need to implement this function to correctly display images.
    return ''

def main():
    # Inject CSS styles
    st.markdown("""
    <style>
    :root {
        /* Dark theme colors */
        --color-1: #d32f2f;
        --color-2: #1976d2;
        --color-3: #388e3c;
        --color-4: #512da8;
        --color-5: #fbc02d;
        --text-color: #fff;
        --primary-color: #2196f3;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: #fbc02d;
            --text-color: #000;
            --primary-color: #1976d2;
        }
    }

    /* Hide the Streamlit style elements (hamburger menu, header, footer) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive font sizes for mobile devices */
    @media only screen and (max-width: 600px) {
        div[style] {
            font-size: 5vw !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Reader")

    # Move file uploader to sidebar
    uploaded_file = st.sidebar.file_uploader("Choose an EPUB file", type="epub")

    if uploaded_file is not None:
        # Create a temporary file to store the EPUB file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # Load the EPUB file from the temporary file path
            book = epub.read_epub(tmp_file_path)
        except Exception as e:
            st.error(f"An error occurred while reading the EPUB file: {e}")
            return
        finally:
            # Clean up the temporary file
            os.remove(tmp_file_path)

        # Initialize the chapter content
        chapters = []
        chapter_titles = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item)
                # Attempt to get the chapter title from the item's metadata
                title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Use lxml to parse the XHTML content of the chapter
            xhtml_content = selected_item.get_content()

            # Get processed elements
            elements = get_processed_elements(xhtml_content)

            # Initialize session state for the element index
            if 'current_element' not in st.session_state:
                st.session_state.current_element = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_element > 0:
                        st.session_state.current_element -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_element + 1 < len(elements):
                        st.session_state.current_element += 1

            # Display the elements
            display_elements(st.session_state.current_element, elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
