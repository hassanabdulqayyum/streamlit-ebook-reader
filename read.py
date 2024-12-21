import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re
import bs4

def split_sentences(text):
    # Define a regex pattern for splitting sentences
    # This pattern handles basic cases and will split on '. ', '!', '?' with consideration for abbreviations
    # Here we use positive lookbehind and positive lookahead
    sentence_endings = re.compile(
        r'(?<=[.!?])\s+(?=[A-Z])'  # Sentence ends with .!? followed by space and capital letter
    )
    sentences = sentence_endings.split(text.strip())
    return sentences

def parse_chapter_content(soup):
    """
    Parses the HTML content of a chapter into a sequential list of content elements.
    Each element is a dictionary with 'type' and 'content' keys.
    """
    content_elements = []

    body = soup.body
    if not body:
        # Maybe the content is directly under <html> or another tag
        body = soup

    for element in body.children:
        if isinstance(element, bs4.element.Tag):
            tag_name = element.name.lower()
            # Determine the type of the tag
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Heading
                content_elements.append({'type': 'heading', 'content': str(element)})
            elif tag_name == 'p':
                # Paragraph
                content_elements.append({'type': 'paragraph', 'content': str(element)})
            elif tag_name == 'img':
                # Image
                content_elements.append({'type': 'image', 'content': str(element)})
            elif tag_name == 'figure':
                # Figure (could contain image and caption)
                content_elements.append({'type': 'figure', 'content': str(element)})
            elif tag_name == 'table':
                # Table
                content_elements.append({'type': 'table', 'content': str(element)})
            elif tag_name == 'div' or tag_name == 'section':
                # Handle nested structures recursively
                nested_elements = parse_chapter_content(element)
                content_elements.extend(nested_elements)
            else:
                # Other content, include if necessary
                pass
        elif isinstance(element, bs4.element.NavigableString):
            # Text node
            text = element.strip()
            if text:
                # Could be text outside of any tag
                # We can choose to include it or ignore
                pass
    return content_elements

def get_paragraph_indices(content_elements):
    """
    Returns a list of indices into content_elements where the elements are paragraphs.
    """
    paragraph_indices = []
    for idx, element in enumerate(content_elements):
        if element['type'] == 'paragraph':
            paragraph_indices.append(idx)
    return paragraph_indices

def get_display_content(content_elements, paragraph_indices, current_paragraph_idx):
    """
    Returns display_elements and indices in display_elements to highlight.
    """
    # Get indices of previous, current, and next paragraphs
    paragraph_idxs_to_use = []

    # Previous paragraph
    if current_paragraph_idx > 0:
        paragraph_idxs_to_use.append(paragraph_indices[current_paragraph_idx -1])

    # Current paragraph
    paragraph_idxs_to_use.append(paragraph_indices[current_paragraph_idx])

    # Next paragraph
    if current_paragraph_idx +1 < len(paragraph_indices):
        paragraph_idxs_to_use.append(paragraph_indices[current_paragraph_idx +1])

    # Now, get the range in content_elements
    start_idx = paragraph_idxs_to_use[0]
    end_idx = paragraph_idxs_to_use[-1]

    # Collect the display_elements
    display_elements = content_elements[start_idx:end_idx+1]

    # Determine the indices of paragraphs in display_elements to highlight
    paragraph_positions_in_display = []
    for idx in paragraph_idxs_to_use:
        relative_idx = idx - start_idx
        paragraph_positions_in_display.append(relative_idx)

    # We can highlight the middle paragraph
    middle_idx = len(paragraph_positions_in_display) // 2
    highlighted_idx = paragraph_positions_in_display[middle_idx]
    highlighted_indices = [highlighted_idx]

    return display_elements, highlighted_indices

def display_content(display_elements, highlighted_indices):
    """
    Displays the content elements, highlighting the paragraphs in highlighted_indices.
    """
    html_content = ""

    for idx, element in enumerate(display_elements):
        element_html = element['content']
        element_type = element['type']

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

        # If the element is a paragraph and is to be highlighted
        if element_type == 'paragraph' and idx in highlighted_indices:
            # Highlight the paragraph
            paragraph_text = BeautifulSoup(element_html, 'html.parser').get_text()
            # Split into sentences
            sentences = split_sentences(paragraph_text)
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
            # Display element as is
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

            # Use the parse_chapter_content function to get content_elements
            content_elements = parse_chapter_content(soup)

            # Get the paragraph_indices
            paragraph_indices = get_paragraph_indices(content_elements)

            if not paragraph_indices:
                st.error("No paragraphs found in the selected chapter.")
                return

            # Initialize session state for current_paragraph_idx
            if 'current_paragraph_idx' not in st.session_state:
                st.session_state.current_paragraph_idx = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_idx > 0:
                        st.session_state.current_paragraph_idx -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_idx +1 < len(paragraph_indices):
                        st.session_state.current_paragraph_idx += 1

            # Get the display content
            display_elements, highlighted_indices = get_display_content(
                content_elements, paragraph_indices, st.session_state.current_paragraph_idx)

            # Display the content
            display_content(display_elements, highlighted_indices)
        else:
            st.error("No readable content found in the EPUB file.")
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
