import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import bs4
import tempfile
import os
import re

def parse_chapter_content(soup):
    """
    Parses the chapter's soup object and returns a list of elements.
    Each element is a dict with 'type' (e.g., 'paragraph', 'heading', 'image', 'caption') and 'content'.
    Returns the list of elements and the indices of paragraphs within this list.
    """
    elements = []
    paragraph_indices = []
    body = soup.find('body')
    if not body:
        body = soup  # Use the entire soup if no body tag

    idx = 0
    for child in body.children:
        if isinstance(child, bs4.element.Tag):
            if child.name == 'p':
                p_class = child.get('class', [])
                if 'caption' in p_class or 'caption' in child.get('id', ''):
                    elements.append({'type': 'caption', 'content': child})
                else:
                    elements.append({'type': 'paragraph', 'content': child})
                    paragraph_indices.append(idx)
            elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                elements.append({'type': 'heading', 'content': child})
            elif child.name == 'img' or child.name == 'image':
                elements.append({'type': 'image', 'content': child})
            else:
                # For other tags, you might decide how to handle them
                elements.append({'type': 'other', 'content': child})
        elif isinstance(child, bs4.element.NavigableString):
            # Skip pure strings if they are whitespace
            if not child.strip():
                continue
            # Consider adding as 'text'
            elements.append({'type': 'text', 'content': str(child)})
        idx += 1

    return elements, paragraph_indices

def display_paragraphs(current_paragraph_index, elements, paragraph_indices):
    """
    Displays three paragraphs at a time, highlighting the middle one.
    Other elements like headings, images, captions are displayed appropriately.
    """
    # Get the element index in elements for the current paragraph
    current_element_index = paragraph_indices[current_paragraph_index]

    # Collect elements to display: previous, current, next paragraphs and any elements in between
    display_indices = []

    # Indices for previous, current, and next paragraphs
    prev_paragraph_index = current_paragraph_index - 1
    next_paragraph_index = current_paragraph_index + 1

    # Collect elements from previous paragraph
    if prev_paragraph_index >= 0:
        prev_element_index = paragraph_indices[prev_paragraph_index]
        display_indices.extend(range(prev_element_index, current_element_index))
    else:
        prev_element_index = current_element_index

    # Collect elements from current paragraph
    if current_paragraph_index + 1 < len(paragraph_indices):
        next_element_index = paragraph_indices[current_paragraph_index + 1]
    else:
        next_element_index = len(elements)
    display_indices.extend(range(current_element_index, next_element_index))

    # Collect elements from next paragraph
    if next_paragraph_index < len(paragraph_indices):
        next_next_paragraph_index = next_paragraph_index + 1
        if next_next_paragraph_index < len(paragraph_indices):
            next_next_element_index = paragraph_indices[next_next_paragraph_index]
        else:
            next_next_element_index = len(elements)
        display_indices.extend(range(next_element_index, next_next_element_index))

    # Build the HTML content
    html_content = ""

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

    for idx in display_indices:
        element = elements[idx]
        element_type = element['type']
        content = element['content']

        if element_type == 'paragraph':
            # Check if this is the middle paragraph
            paragraph_idx_in_paragraph_indices = paragraph_indices.index(idx)
            is_current_paragraph = (paragraph_idx_in_paragraph_indices == current_paragraph_index)

            # Get the text content
            paragraph_text = content.get_text(separator=' ')

            if is_current_paragraph:
                # Highlight sentences in the paragraph
                # Use a regex to split sentences, attempting to handle abbreviations and references
                sentence_endings = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s')
                sentences = sentence_endings.split(paragraph_text.strip())

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
                # Non-highlighted paragraph
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif element_type == 'heading':
            # Display heading appropriately
            heading_text = content.get_text(separator=' ')
            html_content += f"<h2 style='{font_style}'>{heading_text}</h2>"
        elif element_type == 'image':
            # Display image
            # Need to handle image source paths
            img_src = content.get('src', '')
            if img_src:
                # Resolve image path if necessary
                img_tag = f'<img src="{img_src}" alt="Image" />'
                html_content += f"<div style='{font_style}'>{img_tag}</div>"
        elif element_type == 'caption':
            # Display caption
            caption_text = content.get_text(separator=' ')
            html_content += f"<div style='{font_style}; font-style: italic;'>{caption_text}</div>"
        else:
            # Other content
            other_text = content.get_text(separator=' ') if hasattr(content, 'get_text') else str(content)
            html_content += f"<div style='{font_style}'>{other_text}</div>"

    # Display the HTML content using Streamlit
    st.write(html_content, unsafe_allow_html=True)

def main():
    # Inject CSS styles
    st.markdown("""
    <style>
    :root {
        --text-color: #f4f4f4;
        --primary-color: #1d3557;
        /* Dark theme colors */
        --color-1: #d32f2f;
        --color-2: #1976d2;
        --color-3: #388e3c;
        --color-4: #512da8;
        --color-5: rgba(251, 192, 45, 0.9);
    }

    @media (prefers-color-scheme: light) {
        :root {
            --text-color: #1d3557;
            --primary-color: #f4f4f4;
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
                # Alternatively, use item.get_title() if available
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the selected chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            elements, paragraph_indices = parse_chapter_content(soup)

            # Initialize session state for the paragraph index
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

            # Display the paragraphs and other elements
            display_paragraphs(st.session_state.current_paragraph_index, elements, paragraph_indices)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
