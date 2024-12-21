import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re
import html

def parse_chapter_content(soup):
    """
    Parses the chapter content into a list of elements with type and content.
    Each element is a dictionary with 'type' and 'content'.
    """
    content_elements = []
    for element in soup.body.find_all(recursive=False):
        if isinstance(element, str):
            continue  # Skip strings directly under body (like whitespace)
        elif element.name == 'p':
            content_elements.append({'type': 'paragraph', 'content': str(element)})
        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            content_elements.append({'type': 'title', 'content': str(element)})
        elif element.name == 'img':
            content_elements.append({'type': 'image', 'content': str(element)})
        else:
            # Handle other elements
            content_elements.append({'type': element.name, 'content': str(element)})
    return content_elements

def apply_highlighting_to_paragraph(paragraph_html):
    """
    Highlights the sentences in paragraph_html with different colors.
    """
    # Parse the paragraph_html to get the text
    soup = BeautifulSoup(paragraph_html, 'html.parser')
    paragraph_text = soup.get_text(' ')

    sentences = re.split(r'(?<=[.!?]) +', paragraph_text.strip())
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
        sentence = html.escape(sentence)
        sentence_html = f'<span style="{highlighted_style}">{sentence}</span>'
        highlighted_sentence.append(sentence_html)

    paragraph_content = ' '.join(highlighted_sentence)
    # Optionally, wrap in <p> tag with base font style
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
    return f"<div style='{font_style}'><p>{paragraph_content}</p></div>"

def display_elements(display_elements, highlight_paragraph_idx):
    """
    Displays the elements in display_elements, highlighting the paragraph at highlight_paragraph_idx.
    """
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
        bottom-margin: 20px;
        padding: 15px;
        transition: text-shadow 0.5s;
    """

    for i, element in enumerate(display_elements):
        elem_type = element['type']
        elem_content = element['content']

        if i == highlight_paragraph_idx and elem_type == 'paragraph':
            # This is the current paragraph to be highlighted
            # Apply highlighting
            highlighted_paragraph_html = apply_highlighting_to_paragraph(elem_content)
            html_content += highlighted_paragraph_html
        else:
            # Display element normally with font style
            html_content += f"<div style='{font_style}'>{elem_content}</div>"

    st.write(html_content, unsafe_allow_html=True)

def get_display_elements(content_elements, paragraph_indices, current_paragraph_pos):
    """
    Returns the list of elements to display based on the current paragraph index,
    along with the index of the highlighted paragraph within that list.
    Includes the previous, current, and next paragraphs, including any non-paragraph elements in between.
    """
    prev_paragraph_pos = max(current_paragraph_pos - 1, 0)
    next_paragraph_pos = min(current_paragraph_pos + 1, len(paragraph_indices) -1)

    start_idx = paragraph_indices[prev_paragraph_pos]
    end_idx = paragraph_indices[next_paragraph_pos] +1  # +1 to include the element at end_idx

    display_elements = content_elements[start_idx:end_idx]

    # The index of the current paragraph in display_elements
    highlight_paragraph_idx = paragraph_indices[current_paragraph_pos] - start_idx

    return display_elements, highlight_paragraph_idx

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
        --text-color: #FFFFFF;
        --primary-color: #2979ff;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9); /* Adjust opacity here */
            --text-color: #000000;
            --primary-color: #2979ff;
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
                # Try to extract title from the item
                title = item.get_name()
                try:
                    item_soup = BeautifulSoup(item.get_content(), 'html.parser')
                    if item_soup.title:
                        title = item_soup.title.string
                except:
                    pass
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_content(), 'html.parser')

            # Parse content into elements
            content_elements = parse_chapter_content(soup)

            # Get indices of paragraphs
            paragraph_indices = [i for i, elem in enumerate(content_elements) if elem['type'] == 'paragraph']

            if paragraph_indices:
                # Initialize session state for the paragraph index
                if 'current_paragraph_pos' not in st.session_state:
                    st.session_state.current_paragraph_pos = 0

                # Display navigation buttons
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    if st.button("Previous"):
                        if st.session_state.current_paragraph_pos > 0:
                            st.session_state.current_paragraph_pos -= 1
                with col3:
                    if st.button("Next"):
                        if st.session_state.current_paragraph_pos + 1 < len(paragraph_indices):
                            st.session_state.current_paragraph_pos += 1

                # Get display elements and highlight paragraph index
                display_elements_list, highlight_paragraph_idx = get_display_elements(
                    content_elements, paragraph_indices, st.session_state.current_paragraph_pos)

                # Display the elements
                display_elements(display_elements_list, highlight_paragraph_idx)
            else:
                st.error("No paragraphs found in the selected chapter.")
                return
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
