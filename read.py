import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re

def process_chapter(soup):
    """
    Processes the HTML soup to generate a list of elements preserving their order.
    Each element is a dictionary with 'type' and 'content'.
    """
    elements = []

    # Note: Some EPUB files may not have a 'body' tag, adjust accordingly
    if soup.body:
        body_content = soup.body.contents
    else:
        body_content = soup.contents

    for elem in body_content:
        if isinstance(elem, str):
            # Ignore strings that are just whitespace
            if elem.strip():
                elements.append({'type': 'text', 'content': elem.strip()})
        elif isinstance(elem, bs4.element.Tag):
            if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                elements.append({'type': 'heading', 'content': elem.get_text(strip=True), 'level': elem.name})
            elif elem.name == 'p':
                elements.append({'type': 'paragraph', 'content': elem})
            elif elem.name == 'img':
                elements.append({'type': 'image', 'content': elem})
            else:
                # For other tags, we can include or ignore based on requirements
                elements.append({'type': 'other', 'content': elem})
    return elements

def split_sentences(text):
    # Pattern to find sentence endings
    # Avoid splitting at periods followed by numbers or lowercase letters
    pattern = r'(?<=[.!?])\s+(?=[A-Z"“])'  # Split at sentence endings followed by uppercase letter or quotation marks
    sentences = re.split(pattern, text)
    return sentences

def display_elements(element_index, elements):
    """
    Displays three elements at a time, highlighting the middle one if it's a paragraph.
    Other elements like headings, images, captions are displayed as part of the content.
    """
    # Extract the three elements to be displayed
    display_elements_list = elements[max(element_index-1, 0):element_index+2]

    html_content = ""

    for i, elem in enumerate(display_elements_list):
        # Define base font style for readability
        base_font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 800px;
            margin: 10px auto;
            padding: 15px;
            border: 1px solid var(--primary-color);
            transition: text-shadow 0.5s;
        """

        # Highlight the middle element (or first if at the beginning)
        is_highlighted = (element_index == 0 and i == 0) or (element_index != 0 and i == 1)

        if elem['type'] == 'paragraph':
            # Get the text content of the paragraph, including any inline tags
            paragraph_html = str(elem['content'])
            soup = BeautifulSoup(paragraph_html, 'html.parser')
            paragraph_text = ''.join([str(content) for content in soup.contents])

            if is_highlighted:
                # Split into sentences carefully
                sentences = split_sentences(paragraph_text)
                highlighted_sentence = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{j%5 +1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                        position: relative;
                        z-index: 1;
                    """
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentence.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentence)
                html_content += f"<div style='{base_font_style}'>{paragraph_content}</div>"
            else:
                html_content += f"<div style='{base_font_style}'>{paragraph_text}</div>"

        elif elem['type'] == 'heading':
            # Use different style for headings
            heading_level = int(elem.get('level', 'h2')[-1])
            heading_size = max(28 - (heading_level - 1) * 2, 22)
            heading_style = f"""
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: {heading_size}px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 800px;
                margin: 20px auto;
                padding: 15px;
                border-bottom: 1px solid var(--primary-color);
            """
            html_content += f"<div style='{heading_style}'>{elem['content']}</div>"
        elif elem['type'] == 'image':
            # Render image
            img_tag = elem['content']
            html_content += f"<div style='text-align:center;'>{str(img_tag)}</div>"
        else:
            # For 'text' or 'other' types
            content_html = str(elem['content'])
            html_content += f"<div style='{base_font_style}'>{content_html}</div>"

    # Display the HTML content using Streamlit
    st.markdown(html_content, unsafe_allow_html=True)

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
        --color-5: rgba(251, 192, 45, 0.9);
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9);
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

    st.title("Custom EPUB Reader")

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
                # Attempt to get the chapter title
                title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Use process_chapter function to get elements
            chapter_elements = process_chapter(soup)

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
                    if st.session_state.current_element + 1 < len(chapter_elements):
                        st.session_state.current_element += 1

            # Display the elements
            display_elements(st.session_state.current_element, chapter_elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
