import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup, Tag, NavigableString
import tempfile
import os
import re

def get_processed_elements(soup):
    """
    Processes the HTML soup and generates a list of elements with their types.
    Elements can be paragraphs, headings, images, captions, etc.
    """
    processed_elements = []

    # Let's iterate over the body content
    body = soup.find('body')
    if body is None:
        # Sometimes the content might not be within <body> tag
        body = soup

    for element in body.contents:
        if isinstance(element, Tag):
            # Determine the type
            if element.name == 'p':
                p_class = element.get('class', [])
                is_paragraph = (
                    'para' in p_class
                    or 'chapterOpenerText' in p_class
                    or 'paragraph' in p_class
                    or not p_class  # Consider paragraphs without class
                )

                if is_paragraph:
                    processed_elements.append({'type': 'paragraph', 'content': element})
                else:
                    processed_elements.append({'type': 'caption', 'content': element})
            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                processed_elements.append({'type': 'heading', 'content': element})
            elif element.name == 'img':
                processed_elements.append({'type': 'image', 'content': element})
            else:
                # Other elements, treat as needed
                processed_elements.append({'type': 'other', 'content': element})
        elif isinstance(element, NavigableString):
            # Text directly under body
            text = element.strip()
            if text:
                processed_elements.append({'type': 'text', 'content': text})

    return processed_elements

def split_sentences(text):
    """
    Splits the text into sentences while avoiding splitting at references or abbreviations.
    """
    # First, replace periods within brackets to prevent splitting inside references
    text = re.sub(r'\[(.*?)\]', lambda x: x.group(0).replace('.', ''), text)
    text = re.sub(r'\((.*?)\)', lambda x: x.group(0).replace('.', ''), text)

    # Now split sentences at period, question mark, or exclamation mark followed by space or end of line
    pattern = re.compile(r'(?<=[.!?])\s+')
    sentences = pattern.split(text)
    return sentences

def display_paragraphs(paragraph_index, processed_elements, paragraph_indices):
    """
    Displays paragraphs, highlighting the middle one. Handles different elements appropriately.
    """
    # Get the index in paragraph_indices corresponding to paragraph_index
    para_idx_in_indices = paragraph_index  # As we are maintaining paragraph_index in session state
    # Make sure para_idx_in_indices is within range
    para_idx_in_indices = max(0, min(para_idx_in_indices, len(paragraph_indices) - 1))

    # Get indices of previous, current, and next paragraphs in processed_elements
    indices_to_display = []

    if para_idx_in_indices > 0:
        start_idx = paragraph_indices[para_idx_in_indices - 1]
    else:
        start_idx = paragraph_indices[para_idx_in_indices]

    end_idx = paragraph_indices[min(para_idx_in_indices + 1, len(paragraph_indices) - 1)] + 1

    # Slice the elements to display
    elements_to_display = processed_elements[start_idx:end_idx]

    # Display the elements
    html_content = ""

    for elem in elements_to_display:
        elem_type = elem['type']
        content = elem['content']

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
            /* Remove or set background-color to transparent */
            /* background-color: transparent; */
            transition: text-shadow 0.5s;
        """

        # Determine if this is the middle paragraph to be highlighted
        is_highlighted = (elem_type == 'paragraph' and elem == processed_elements[paragraph_indices[para_idx_in_indices]])

        # Get the HTML content
        if isinstance(content, Tag):
            element_html = str(content)
        else:
            element_html = content

        if elem_type == 'paragraph':
            if is_highlighted:
                # Get text content for sentence splitting
                text_content = content.get_text(separator=' ')
                sentences = split_sentences(text_content)

                # Apply highlighting to sentences
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
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Display non-highlighted paragraph
                html_content += f"<div style='{font_style}'>{element_html}</div>"
        elif elem_type == 'heading':
            # Display headings
            heading_tag = content.name
            html_content += f"<{heading_tag}>{content.get_text(strip=True)}</{heading_tag}>"
        elif elem_type == 'image':
            # Display images
            html_content += f"<div style='text-align: center;'>{element_html}</div>"
        elif elem_type == 'caption':
            # Display captions
            caption_style = font_style + "font-style: italic;"
            html_content += f"<div style='{caption_style}'>{content.get_text(strip=True)}</div>"
        else:
            # Display other elements
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

            # Use the get_processed_elements function to get elements
            chapter_elements = get_processed_elements(soup)

            # Build a list of indices of paragraphs in chapter_elements
            paragraph_indices = [i for i, elem in enumerate(chapter_elements) if elem['type'] == 'paragraph']

            # Initialize session state for the paragraph index
            if 'current_paragraph' not in st.session_state:
                st.session_state.current_paragraph = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph > 0:
                        st.session_state.current_paragraph -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph += 1

            # Display the paragraphs
            display_paragraphs(st.session_state.current_paragraph, chapter_elements, paragraph_indices)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
