import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re

def get_processed_elements(soup):
    """
    Processes the HTML soup to generate a list of elements.
    Each element is a dict with 'type' and 'content'.
    """
    elements = []
    body = soup.find('body') or soup

    for child in body.contents:
        if isinstance(child, str):
            continue  # Skip strings directly under body

        if child.name == 'p':
            elements.append({'type': 'paragraph', 'content': str(child)})
        elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            elements.append({'type': 'heading', 'content': str(child)})
        elif child.name == 'img':
            elements.append({'type': 'image', 'content': str(child)})
        elif child.name in ['figure', 'figcaption']:
            elements.append({'type': 'caption', 'content': str(child)})
        elif child.name == 'div':
            # Process the child elements of the div
            elements.extend(get_processed_elements(child))
        else:
            # Add other elements if necessary
            elements.append({'type': 'other', 'content': str(child)})

    return elements

def split_into_sentences(text):
    """
    Splits text into sentences, handling references and abbreviations properly.
    """
    # Regular expression pattern to identify sentence boundaries
    pattern = re.compile(r'''
        (?<!\b[A-Z])       # Negative lookbehind for abbreviations (e.g., U.S.)
        (?<!\b[A-Z][a-z])  # Negative lookbehind for abbreviations (e.g., Mr.)
        (?<!\b\w\.\w\.)    # Negative lookbehind for initials (e.g., J.D.)
        (?<!\d\.\d)        # Negative lookbehind for decimal numbers (e.g., 3.14)
        (?<=[.!?])         # Positive lookbehind for sentence-ending punctuation
        \s+                # One or more whitespace characters
        (?=[A-Z])          # Positive lookahead for a capital letter
    ''', re.VERBOSE)

    sentences = pattern.split(text)
    return sentences

def display_elements(element_index, elements):
    """
    Displays three elements at a time, highlighting the middle one if it's a paragraph.
    """
    # Extract the three elements to be displayed
    display_elements = elements[max(element_index - 1, 0): element_index + 2]
    html_content = ""

    for i, element in enumerate(display_elements):
        # Define base font style for readability
        font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 1000px;
            margin: 10px auto;
            bottom-margin: 20px;
            padding: 15px;
            border: 1px solid var(--primary-color);
            transition: text-shadow 0.5s;
        """

        is_middle = (element_index == 0 and i == 0) or (element_index != 0 and i == 1)

        if is_middle and element['type'] == 'paragraph':
            # Process and highlight the paragraph
            paragraph_html = element['content']
            soup = BeautifulSoup(paragraph_html, 'html.parser')
            paragraph_text = soup.get_text(separator=' ')
            sentences = split_into_sentences(paragraph_text)

            # Highlight each sentence with different colors
            highlighted_sentences = []
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
                highlighted_sentences.append(sentence_html)

            paragraph_content = ' '.join(highlighted_sentences)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # Display other elements without highlighting
            element_html = element['content']
            html_content += f"<div style='{font_style}'>{element_html}</div>"

    # Display the HTML content using Streamlit
    st.write(html_content, unsafe_allow_html=True)

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

    /* Hide Streamlit's default elements */
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

    st.title("EPUB Reader")

    # File uploader in sidebar
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
            # Chapter selector in sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Get the processed elements
            chapter_elements = get_processed_elements(soup)

            # Initialize session state for the element index
            if 'current_chapter' not in st.session_state or st.session_state.current_chapter != selected_chapter:
                st.session_state.current_element = 0
                st.session_state.current_chapter = selected_chapter

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
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
