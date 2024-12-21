import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re
import bs4

def parse_chapter_content(soup):
    """
    Parses the chapter soup and returns a list of content blocks.
    Each content block is a dictionary with 'type' and 'content'.
    """
    content_blocks = []
    # Iterate over direct children of the body tag to maintain order
    for element in soup.body.children:
        if isinstance(element, bs4.Tag):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                content_blocks.append({'type': 'heading', 'content': str(element)})
            elif element.name == 'p':
                if element.get_text(strip=True) != '':
                    content_blocks.append({'type': 'paragraph', 'content': str(element)})
            elif element.name in ['img', 'image']:
                content_blocks.append({'type': 'image', 'content': str(element)})
            elif element.name == 'figure':
                content_blocks.append({'type': 'figure', 'content': str(element)})
            elif element.name == 'div' and 'caption' in element.get('class', []):
                content_blocks.append({'type': 'caption', 'content': str(element)})
            else:
                # Handle other tags if necessary
                pass
        elif isinstance(element, bs4.NavigableString):
            if element.strip():
                content_blocks.append({'type': 'text', 'content': element.strip()})
    return content_blocks

def split_into_sentences(text):
    """
    Splits text into sentences using a regex that avoids splitting at periods within abbreviations or numbers.
    """
    sentence_endings = re.compile(
        r'''(?<!\b[A-Z][a-z]\.)           # No split for abbreviations like 'Dr.', 'Mr.'
             (?<!\b[A-Z]\.)               # No split for single-letter initials 'A.'
             (?<!\b[A-Za-z]\.[A-Za-z]\.)  # No split for initials like 'U.S.'
             (?<!\b\.\.\.)                # No split for ellipsis '...'
             (?<=\.|\?|!)\s''',           # Split at '.' '?' '!' followed by space
        re.VERBOSE)
    sentences = sentence_endings.split(text)
    return sentences

def get_display_indices(paragraph_indices, current_para_idx, content_blocks):
    """
    Returns a list of content block indices to display, including the paragraphs and any adjacent elements.
    """
    indices_to_display = set()

    # Determine indices for previous, current, and next paragraphs
    para_idxs = [current_para_idx - 1, current_para_idx, current_para_idx + 1]

    for para_idx in para_idxs:
        if 0 <= para_idx < len(paragraph_indices):
            start_idx = paragraph_indices[para_idx]
            if para_idx + 1 < len(paragraph_indices):
                end_idx = paragraph_indices[para_idx + 1]
            else:
                end_idx = len(content_blocks)
            for idx in range(start_idx, end_idx):
                indices_to_display.add(idx)

    return sorted(indices_to_display)

def display_paragraphs(current_para_idx, content_blocks, paragraph_indices):
    """
    Displays three paragraphs at a time, highlighting the current one.
    Other elements like headings, captions, and images are displayed appropriately.
    """
    display_block_indices = get_display_indices(paragraph_indices, current_para_idx, content_blocks)
    html_content = ''

    for idx in display_block_indices:
        block = content_blocks[idx]
        block_type = block['type']
        block_content = block['content']

        # Base font style
        font_style = """
            font-family: Georgia, serif;
            font-weight: 450;
            font-size: 20px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 800px;
            margin: 10px auto;
            padding: 15px;
            border: 1px solid var(--primary-color);
        """

        # Check if this block is the current paragraph
        is_current_paragraph = (idx == paragraph_indices[current_para_idx])

        if block_type == 'paragraph':
            paragraph_html = block_content
            soup = BeautifulSoup(paragraph_html, 'html.parser')
            paragraph_text = soup.get_text(separator=' ')

            if is_current_paragraph:
                sentences = split_into_sentences(paragraph_text)
                highlighted_sentences = []
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
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                html_content += f"<div style='{font_style}'>{paragraph_html}</div>"
        elif block_type == 'heading':
            heading_style = f"""
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: 24px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 800px;
                margin: 20px auto 10px auto;
                padding: 0px;
            """
            html_content += f"<div style='{heading_style}'>{block_content}</div>"
        elif block_type == 'image':
            html_content += f"<div style='text-align: center;'>{block_content}</div>"
        elif block_type == 'figure':
            html_content += f"<div>{block_content}</div>"
        elif block_type == 'caption':
            caption_style = f"""
                font-family: Georgia, serif;
                font-style: italic;
                font-size: 18px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 800px;
                margin: 5px auto;
                padding: 0px;
            """
            html_content += f"<div style='{caption_style}'>{block_content}</div>"
        else:
            html_content += f"<div style='{font_style}'>{block_content}</div>"

    st.write(html_content, unsafe_allow_html=True)

def main():
    # Inject CSS styles
    st.markdown("""
    <style>
    :root {
        --color-1: #d32f2f;
        --color-2: #1976d2;
        --color-3: #388e3c;
        --color-4: #512da8;
        --color-5: #fbc02d;
    }
    @media (prefers-color-scheme: light) {
        :root {
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: #fbc02d;
        }
    }
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

    st.title("Reader")

    # File uploader in the sidebar
    uploaded_file = st.sidebar.file_uploader("Choose an EPUB file", type="epub")

    if uploaded_file is not None:
        # Create a temporary file to store the EPUB
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # Load the EPUB file
            book = epub.read_epub(tmp_file_path)
        except Exception as e:
            st.error(f"An error occurred while reading the EPUB file: {e}")
            return
        finally:
            os.remove(tmp_file_path)

        # Extract chapters and titles
        chapters = []
        chapter_titles = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item)
                title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            content_blocks = parse_chapter_content(soup)

            # Map paragraph indices
            paragraph_indices = [idx for idx, block in enumerate(content_blocks) if block['type'] == 'paragraph']

            if 'current_paragraph_idx' not in st.session_state:
                st.session_state.current_paragraph_idx = 0

            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_idx > 0:
                        st.session_state.current_paragraph_idx -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_idx + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph_idx += 1

            display_paragraphs(st.session_state.current_paragraph_idx, content_blocks, paragraph_indices)
        else:
            st.error("No readable content found in the EPUB file.")
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
