import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString, Tag
import tempfile
import os
import re


def get_toc_map(book):
    """
    Creates a mapping from href to title using the book's table of contents (toc).
    """
    toc_map = {}

    def parse_toc_entries(entries):
        for entry in entries:
            if isinstance(entry, epub.Link):
                href = entry.href.split("#")[0] if entry.href else ''
                title = entry.title
                toc_map[href.lstrip('/')] = title
            elif isinstance(entry, epub.Section):
                href = entry.href.split("#")[0] if entry.href else ''
                title = entry.title
                toc_map[href.lstrip('/')] = title
                # Recursively parse nested entries using 'children'
                if entry.children:
                    parse_toc_entries(entry.children)
            elif isinstance(entry, (list, tuple)):
                parse_toc_entries(entry)
            else:
                pass

    parse_toc_entries(book.toc)
    return toc_map


def get_processed_elements(soup):
    """
    Processes the HTML soup and returns a list of elements.
    Each element is a dict with 'type' and 'content'.
    Types can be 'heading', 'paragraph', 'image', 'caption', etc.
    """
    elements = []

    # Assuming that the content is within 'body' tag
    body = soup.body if soup.body else soup

    # Iterate through all descendants of the body
    for elem in body.descendants:
        if isinstance(elem, NavigableString):
            # Skip strings that are just whitespace or newline characters
            if not elem.strip():
                continue
            # Wrap standalone strings in a span for uniform handling
            elements.append({'type': 'text', 'content': elem})
        elif isinstance(elem, Tag):
            if elem.name == 'p':
                p_class = elem.get('class', [])
                is_paragraph = 'para' in p_class or 'chapterOpenerText' in p_class or 'paragraph' in p_class or not p_class

                if is_paragraph:
                    elements.append({'type': 'paragraph', 'content': elem})
                else:
                    # Captions or other types of 'p' elements
                    elements.append({'type': 'caption', 'content': elem})
            elif elem.name.startswith('h'):
                # Heading tags like h1, h2, h3, etc.
                elements.append({'type': 'heading', 'content': elem})
            elif elem.name == 'img':
                elements.append({'type': 'image', 'content': elem})
            elif elem.name == 'div':
                # Some divs may contain paragraphs or other content
                div_class = elem.get('class', [])
                is_paragraph = 'paragraph' in div_class or 'para' in div_class or 'text' in div_class
                if is_paragraph:
                    elements.append({'type': 'paragraph', 'content': elem})
                else:
                    # Handle other div types if needed
                    elements.append({'type': 'other', 'content': elem})
            else:
                # Handle other elements if needed
                elements.append({'type': 'other', 'content': elem})

    return elements

def split_sentences(text):
    # Regex to split sentences, handling abbreviations and references
    sentence_endings = re.compile(r'''
        (?<!\b\w\.\w\.)           # Negative lookbehind for strings like "e.g."
        (?<!\b[A-Z][a-z]\.)       # Negative lookbehind for abbreviations like "Dr."
        (?<!\s[A-Z])              # Negative lookbehind for single capital letters
        (?<=\.|\?|!|\.\")         # Positive lookbehind for punctuation or punctuation followed by quote
        \s+                       # Split on whitespace
        ''', re.VERBOSE)
    sentences = sentence_endings.split(text.strip())
    return sentences

def display_paragraphs(current_paragraph_index, chapter_elements, paragraph_indices):
    """
    Displays elements around the current paragraph, highlighting the middle paragraph.
    Non-paragraph elements like headings, captions, images are displayed appropriately.
    """
    if not paragraph_indices:
        st.write("No paragraphs found in this chapter.")
        return

    # Get indices of the previous, current, and next paragraphs
    paragraph_count = len(paragraph_indices)
    prev_index = max(current_paragraph_index -1, 0)
    next_index = min(current_paragraph_index +1, paragraph_count -1)

    # Get the positions in the elements list
    start_elem_index = paragraph_indices[prev_index]
    end_elem_index = paragraph_indices[next_index]

    # Ensure start_elem_index <= end_elem_index
    if start_elem_index > end_elem_index:
        start_elem_index, end_elem_index = end_elem_index, start_elem_index

    # Get elements from start_elem_index to end_elem_index, including any non-paragraph elements in between
    display_elements = chapter_elements[start_elem_index:end_elem_index+1]

    # Build HTML content
    html_content = ""

    for elem in display_elements:
        elem_type = elem['type']
        elem_content = elem['content']

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

        if elem_type == 'paragraph':
            # Check if this is the middle paragraph to highlight
            is_highlighted = (elem == chapter_elements[paragraph_indices[current_paragraph_index]])

            # Get text content
            paragraph_text = elem_content.get_text(separator=' ')

            if is_highlighted:
                # Split sentences and highlight them
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
                    # Ensure punctuation stays attached to the sentence
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentence.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentence)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Just display the paragraph
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif elem_type == 'heading':
            # Define heading style
            heading_style = """
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: 24px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 20px auto 10px auto;
                padding: 15px;
            """
            heading_text = elem_content.get_text(separator=' ')
            html_content += f"<div style='{heading_style}'>{heading_text}</div>"
        elif elem_type == 'image':
            # Handle image display
            img_src = elem_content.get('src')
            if img_src and not img_src.startswith('http'):
                # Handle relative image paths
                # For simplicity, displaying a placeholder
                img_html = f"<div style='text-align:center;'>[Image]</div>"
            else:
                img_html = f"<img src='{img_src}' alt='Image' style='max-width: 100%; height: auto;'>"
            html_content += img_html
        elif elem_type == 'caption':
            caption_text = elem_content.get_text(separator=' ')
            caption_style = """
                font-family: Georgia, serif;
                font-style: italic;
                font-size: 18px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 1000px;
                margin: 5px auto 15px auto;
                padding: 15px;
            """
            html_content += f"<div style='{caption_style}'>{caption_text}</div>"
        elif elem_type == 'text':
            # Handle standalone text
            text_content = str(elem_content).strip()
            if text_content:
                html_content += f"<div style='{font_style}'>{text_content}</div>"
        else:
            # Handle other types if needed
            other_text = elem_content.get_text(separator=' ').strip()
            if other_text:
                html_content += f"<div style='{font_style}'>{other_text}</div>"

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
            --color-5: rgba(251, 192, 45, 0.9); /* Adjust opacity here */
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

    st.title("EPUB Reader")

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

        # Create a mapping from href to title using the table of contents
        toc_map = get_toc_map(book)

        # Initialize the chapter content
        chapters = []
        chapter_titles = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item)
                # Get the href of the item
                href = item.get_name()
                # Adjust href in case it starts with '/'
                href = href.lstrip('/')
                # Look up the title in the toc_map
                title = toc_map.get(href, None)
                if not title:
                    # Try to get the title from the HTML content
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    if soup.title:
                        title = soup.title.string.strip()
                    else:
                        # Use a default title
                        title = f"Chapter {len(chapter_titles)+1}"
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_content(), 'html.parser')
            # Use the get_processed_elements function to get elements
            chapter_elements = get_processed_elements(soup)

            # Build a list of indices of paragraph elements
            paragraph_indices = [i for i, elem in enumerate(chapter_elements) if elem['type'] == 'paragraph']

            # If no paragraphs are found, display a message
            if not paragraph_indices:
                st.write("No paragraphs found in this chapter.")
                return

            if 'current_paragraph_index' not in st.session_state:
                st.session_state.current_paragraph_index = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_index > 0:
                        st.session_state.current_paragraph_index -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_index + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph_index += 1

            # Display the elements around the current paragraph
            display_paragraphs(st.session_state.current_paragraph_index, chapter_elements, paragraph_indices)

        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
