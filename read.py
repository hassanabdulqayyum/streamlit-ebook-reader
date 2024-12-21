import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re

def process_chapter(contents):
    """
    Processes the chapter contents to generate a list of elements with their types and content.
    """
    elements = []
    for elem in contents:
        if isinstance(elem, str):
            # Ignore string elements (like newline characters)
            continue
        elif elem.name and elem.name.startswith('h'):
            # Headings (h1, h2, h3, etc.)
            elements.append({'type': 'heading', 'content': str(elem), 'level': int(elem.name[1])})
        elif elem.name == 'p':
            # Paragraphs
            elements.append({'type': 'paragraph', 'content': str(elem)})
        elif elem.name == 'img':
            # Images
            elements.append({'type': 'image', 'content': str(elem)})
        elif elem.name in ['figure', 'figcaption']:
            # Figures and captions
            elements.append({'type': 'figure', 'content': str(elem)})
        else:
            # Other elements
            elements.append({'type': 'other', 'content': str(elem)})
    return elements

def display_content(paragraph_index, elements):
    """
    Displays content, showing three paragraphs centered at paragraph_index,
    and showing other elements (headings, images, etc.) appropriately.
    """
    # Extract the indices of paragraph elements
    paragraph_indices = [i for i, e in enumerate(elements) if e['type'] == 'paragraph']
    if not paragraph_indices:
        st.write("No paragraphs found in this chapter.")
        return

    # Find the position of the current paragraph in the list of paragraph indices
    current_para_pos = paragraph_indices.index(paragraph_index)
    # Get indices for previous, current, and next paragraphs
    indices_to_display = paragraph_indices[max(current_para_pos - 1, 0):current_para_pos + 2]

    # Build a range that includes any non-paragraph elements between selected paragraphs
    first_idx = indices_to_display[0]
    last_idx = indices_to_display[-1]
    element_range = range(first_idx, last_idx + 1)

    html_content = ""

    for idx in element_range:
        element = elements[idx]
        element_type = element['type']
        content_html = element['content']

        if element_type == 'paragraph':
            is_current_paragraph = (idx == paragraph_index)
            if is_current_paragraph:
                # Highlight the current paragraph
                paragraph_text = BeautifulSoup(content_html, 'html.parser').get_text()
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
                font_style = base_font_style()
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Display other paragraphs without highlighting
                font_style = base_font_style()
                html_content += f"<div style='{font_style}'>{content_html}</div>"
        elif element_type == 'heading':
            # Display headings with appropriate styles
            level = element.get('level', 2)
            font_style = heading_font_style(level)
            html_content += f"<div style='{font_style}'>{content_html}</div>"
        else:
            # Display other elements (images, figures, etc.)
            font_style = base_font_style()
            html_content += f"<div style='{font_style}'>{content_html}</div>"

    # Display the HTML content
    st.write(html_content, unsafe_allow_html=True)

def base_font_style():
    return """
        font-family: Georgia, serif;
        font-weight: 450;
        font-size: 20px;
        color: var(--text-color);
        line-height: 1.6;
        max-width: 1000px;
        margin: 10px auto;
        padding: 15px;
        transition: text-shadow 0.5s;
    """

def heading_font_style(level):
    size = {1: '32px', 2: '28px', 3: '24px', 4: '20px', 5: '18px', 6: '16px'}.get(level, '20px')
    margin_top = '30px' if level == 1 else '20px'
    margin_bottom = '10px'
    return f"""
        font-family: Georgia, serif;
        font-weight: bold;
        font-size: {size};
        color: var(--text-color);
        line-height: 1.6;
        max-width: 1000px;
        margin: {margin_top} auto {margin_bottom} auto;
        padding: 5px;
        transition: text-shadow 0.5s;
    """

def split_sentences(paragraph_text):
    """
    Splits paragraph_text into sentences, avoiding splitting at abbreviations or within references.
    """
    # Regex to split sentences while handling common abbreviations and not splitting at references
    sentence_endings = re.compile(r'(?<!\b[a-z])(?<![A-Z][a-z]\.)(?<=\.|\?|!)(\s|$)')
    sentences = sentence_endings.split(paragraph_text)
    # Combine the sentences and separators back together
    sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2])]

    # Remove any empty strings or whitespace-only strings
    sentences = [s.strip() for s in sentences if s.strip()]
    return sentences

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
            # Use the process_chapter function to get elements
            if soup.body:
                contents = soup.body.contents
            else:
                contents = soup.contents
            chapter_elements = process_chapter(contents)

            # Find indices of paragraphs
            paragraph_indices = [i for i, e in enumerate(chapter_elements) if e['type'] == 'paragraph']

            if not paragraph_indices:
                st.write("No paragraphs found in this chapter.")
                return

            # Initialize session state for the paragraph index
            if 'current_paragraph_idx' not in st.session_state:
                st.session_state.current_paragraph_idx = paragraph_indices[0]

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    current_para_pos = paragraph_indices.index(st.session_state.current_paragraph_idx)
                    if current_para_pos > 0:
                        st.session_state.current_paragraph_idx = paragraph_indices[current_para_pos - 1]
            with col3:
                if st.button("Next"):
                    current_para_pos = paragraph_indices.index(st.session_state.current_paragraph_idx)
                    if current_para_pos + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph_idx = paragraph_indices[current_para_pos + 1]

            # Display the content
            display_content(st.session_state.current_paragraph_idx, chapter_elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
