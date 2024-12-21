import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString
import tempfile
import os
import re

def get_chapter_content(soup):
    """
    Processes the HTML soup to generate a list of content items.
    Content items can be paragraphs, headings, images, captions, etc.
    """
    content_items = []
    # Iterate over the body elements in order
    if soup.body:
        body_elements = list(soup.body.children)
    else:
        body_elements = list(soup.children)

    for element in body_elements:
        if isinstance(element, NavigableString):
            # Ignore strings that are just whitespace
            if not element.strip():
                continue
        elif element.name:
            # Handle different types of elements
            if element.name == 'p':
                # Check for images or captions within <p> tags
                if element.find('img'):
                    content_items.append({'type': 'image', 'content': element})
                else:
                    content_items.append({'type': 'paragraph', 'content': element})
            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                content_items.append({'type': 'heading', 'content': element})
            elif element.name == 'img':
                content_items.append({'type': 'image', 'content': element})
            elif element.name == 'div':
                # Handle captions or other div content
                content_items.append({'type': 'div', 'content': element})
            else:
                content_items.append({'type': 'other', 'content': element})
        else:
            continue  # Ignore other elements
    return content_items

def split_sentences(text):
    """
    Splits text into sentences, handling abbreviations and references.
    """
    # Regular expression pattern for sentence splitting
    pattern = re.compile(r'''
        (?<!\b(?:[A-Z][a-z]{0,3}|e\.g|i\.e|Mr|Mrs|Ms|Dr|Prof|Sr|Jr|vs|etc)\.)  # Negative lookbehind for abbreviations
        (?<!\b[A-Z]\.)             # Negative lookbehind for single initials (e.g., "A.")
        (?<!\s\[\d+\])             # Negative lookbehind for references like [1], [2], etc.
        (?<=[.!?])                 # Positive lookbehind for sentence-ending punctuation
        \s+                        # Split at whitespace after punctuation
    ''', re.VERBOSE)

    sentences = pattern.split(text.strip())
    return sentences

def display_content_items(index, content_items):
    """
    Displays content items, highlighting the middle paragraph.
    """
    # Extract the three content items to be displayed
    display_items = content_items[max(index - 1, 0):index + 2]

    html_content = ""

    for i, item in enumerate(display_items):
        item_type = item['type']
        element = item['content']

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

        # Highlight the middle item (or first if at the beginning) if it's a paragraph
        is_highlighted = (index == 0 and i == 0) or (index != 0 and i == 1)

        if item_type == 'paragraph':
            paragraph_text = element.get_text(separator=' ', strip=True)
            if is_highlighted:
                sentences = split_sentences(paragraph_text)
                highlighted_sentence = []
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
                    # Ensure that each sentence ends with punctuation
                    if not sentence.endswith(('.', '!', '?')):
                        sentence += '.'
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentence.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentence)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif item_type == 'heading':
            heading_text = element.get_text(separator=' ', strip=True)
            heading_level = int(element.name[1])
            heading_style = f"""
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: {24 - (heading_level * 2)}px;
                color: var(--primary-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 20px auto 10px auto;
                padding: 5px;
            """
            html_content += f"<div style='{heading_style}'>{heading_text}</div>"
        elif item_type == 'image':
            # Include any images or captions
            img_html = str(element)
            html_content += f"<div style='{font_style}'>{img_html}</div>"
        else:
            # For other content types like divs, etc.
            other_content = element.get_text(separator=' ', strip=True)
            html_content += f"<div style='{font_style}'>{other_content}</div>"

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
                # Extract title from the navigation if available
                title = None
                if book.toc:
                    for toc_item in book.toc:
                        if isinstance(toc_item, epub.Link) and toc_item.href == item.file_name:
                            title = toc_item.title
                            break
                if not title:
                    # Fallback to item file name if title not found
                    title = os.path.basename(item.file_name)
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Use the get_chapter_content function to get content items
            chapter_content_items = get_chapter_content(soup)

            # Initialize session state for the content index
            if 'current_index' not in st.session_state:
                st.session_state.current_index = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_index > 0:
                        st.session_state.current_index -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_index + 1 < len(chapter_content_items):
                        st.session_state.current_index += 1

            # Display the content items
            display_content_items(st.session_state.current_index, chapter_content_items)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
