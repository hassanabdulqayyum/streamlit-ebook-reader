import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup, Tag, NavigableString
import tempfile
import os
import re

def get_content_elements(soup):
    """
    Processes the HTML soup to produce an ordered list of content elements.
    Each content element is a dict with 'type' and 'content'.
    Types include 'heading', 'paragraph', 'image', 'caption', 'text', etc.
    """
    body = soup.body or soup
    content_elements = list(yield_elements(body))
    return content_elements

def yield_elements(element):
    for content in element.contents:
        if isinstance(content, NavigableString):
            text = content.strip()
            if text:
                yield {'type': 'text', 'content': text}
        elif isinstance(content, Tag):
            if content.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                yield {'type': 'heading', 'content': content}
            elif content.name == 'p':
                p_class = content.get('class', [])
                if 'caption' in p_class or 'caption' in content.get_text().lower():
                    yield {'type': 'caption', 'content': content}
                else:
                    yield {'type': 'paragraph', 'content': content}
            elif content.name == 'figure':
                yield {'type': 'figure', 'content': content}
            elif content.name == 'img':
                yield {'type': 'image', 'content': content}
            else:
                # For other tags, recursively process
                yield from yield_elements(content)

def split_into_sentences(text):
    # Simple sentence tokenizer
    # This regex splits on sentence-ending punctuation followed by whitespace
    # It handles common cases but may not be perfect
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    return sentences

def display_elements(element_index, content_elements):
    """
    Displays three elements at a time, centered on the current element.
    Highlights the middle paragraph if applicable.
    Other elements like headings, captions, images are displayed appropriately.
    """
    # Extract the three elements to be displayed
    display_elements = content_elements[max(element_index - 1, 0): element_index + 2]

    html_content = ""

    for i, content_element in enumerate(display_elements):
        element_type = content_element['type']
        element_content = content_element['content']
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

        is_middle_element = (element_index == 0 and i == 0) or (element_index != 0 and i == 1)

        if element_type == 'paragraph':
            # Process paragraph text
            # Remove superscript references
            for sup in element_content.find_all('sup'):
                sup.decompose()
            paragraph_text = element_content.get_text(separator=' ', strip=True)
            if is_middle_element:
                # Highlight sentences
                sentences = split_into_sentences(paragraph_text)
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
            else:
                paragraph_content = paragraph_text

            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"

        elif element_type == 'heading':
            # Display heading
            heading_text = element_content.get_text(strip=True)
            heading_style = """
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: 24px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 20px auto;
                padding: 15px;
                border: 1px solid var(--primary-color);
                transition: text-shadow 0.5s;
            """
            html_content += f"<div style='{heading_style}'>{heading_text}</div>"

        elif element_type == 'image':
            # Display image
            img_html = str(element_content)
            html_content += f"<div style='{font_style}'>{img_html}</div>"

        elif element_type == 'figure':
            # Display figure (image plus caption)
            figure_html = str(element_content)
            html_content += f"<div style='{font_style}'>{figure_html}</div>"

        elif element_type == 'caption':
            # Display caption
            caption_text = element_content.get_text(strip=True)
            caption_style = """
                font-family: Georgia, serif;
                font-style: italic;
                font-size: 18px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 10px auto;
                padding: 15px;
                border: 1px solid var(--primary-color);
                transition: text-shadow 0.5s;
            """
            html_content += f"<div style='{caption_style}'>{caption_text}</div>"

        elif element_type == 'text':
            # Display text
            text_content = content_element['content'].strip()
            if text_content:
                html_content += f"<div style='{font_style}'>{text_content}</div>"
        else:
            # Other types
            pass

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
        --primary-color: #1976d2;
        --text-color: #FFFFFF;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9); /* Adjust opacity here */
            --primary-color: #64b5f6;
            --text-color: #000000;
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
                # Attempt to get the chapter title
                title = item.get_name()
                # Alternatively, use item.get_title() if available
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')

            # Use the get_content_elements function to get content
            content_elements = get_content_elements(soup)

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
                    if st.session_state.current_element + 1 < len(content_elements):
                        st.session_state.current_element += 1

            # Display the elements
            display_elements(st.session_state.current_element, content_elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
