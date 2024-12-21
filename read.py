import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re
import nltk

# Download NLTK data files (punkt tokenizer)
nltk.download('punkt')

from nltk.tokenize import sent_tokenize


def process_chapter_content(soup):
    """
    Processes the HTML soup to produce a flat list of content elements.
    Each element is a dictionary with 'type' and 'content', where 'type' can be 'heading', 'paragraph', 'image', etc.
    """
    content_elements = []

    def process_node(node):
        if isinstance(node, str):
            if node.strip():
                # Text node
                content_elements.append({'type': 'text', 'content': node.strip()})
        elif node.name.startswith('h'):  # Heading tags
            content_elements.append({
                'type': 'heading',
                'level': int(node.name[1]),
                'content': node.get_text(strip=True)
            })
        elif node.name == 'p':
            # Paragraph
            paragraph_text = ''.join(str(child) for child in node.contents)
            content_elements.append({'type': 'paragraph', 'content': paragraph_text})
        elif node.name == 'img':
            # Image
            content_elements.append({
                'type': 'image',
                'src': node.get('src'),
                'alt': node.get('alt', '')
            })
        elif node.name == 'figure':
            # Figure
            caption = node.find('figcaption')
            img = node.find('img')
            fig_content = []
            if img:
                fig_content.append({
                    'type': 'image',
                    'src': img.get('src'),
                    'alt': img.get('alt', '')
                })
            if caption:
                fig_content.append({
                    'type': 'caption',
                    'content': caption.get_text(strip=True)
                })
            content_elements.append({'type': 'figure', 'content': fig_content})
        else:
            # For other tags, process their children
            for child in node.children:
                process_node(child)

    # Start processing from body
    if soup.body:
        for child in soup.body.children:
            process_node(child)
    else:
        for child in soup.children:
            process_node(child)

    return content_elements


def split_into_sentences(text):
    sentences = sent_tokenize(text)
    return sentences


def display_paragraphs(paragraph_indices, content_elements, current_paragraph_idx):
    """
    Displays three paragraphs at a time, including other elements.
    Highlights the middle paragraph.
    """
    num_paragraphs = len(paragraph_indices)
    # Determine indices of previous, current, and next paragraphs
    prev_para_idx = max(current_paragraph_idx - 1, 0)
    curr_para_idx = current_paragraph_idx
    next_para_idx = min(current_paragraph_idx + 1, num_paragraphs - 1)

    # Get the content indices of these paragraphs
    prev_elem_idx = paragraph_indices[prev_para_idx]
    curr_elem_idx = paragraph_indices[curr_para_idx]
    next_elem_idx = paragraph_indices[next_para_idx]

    # For start_idx, find previous element index
    start_idx = prev_elem_idx
    if prev_elem_idx > 0:
        start_idx = prev_elem_idx - 1
    else:
        start_idx = prev_elem_idx

    # For end_idx, find the start index of the paragraph after next, or end of content_elements
    if next_para_idx + 1 < len(paragraph_indices):
        end_idx = paragraph_indices[next_para_idx + 1]
    else:
        end_idx = len(content_elements)

    elements_to_display = content_elements[start_idx:end_idx]

    # Build the HTML content
    html_content = ""

    for elem in elements_to_display:
        if elem['type'] == 'heading':
            level = elem['level']
            heading_style = f"""
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: {32 - level * 2}px;
                color: var(--text-color);
                margin: 10px 0;
            """
            html_content += f"<h{level} style='{heading_style}'>{elem['content']}</h{level}>"
        elif elem['type'] == 'paragraph':
            # Determine if this is the highlighted paragraph
            is_highlighted = (elem == content_elements[curr_elem_idx])

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

            paragraph_text = elem['content']

            if is_highlighted:
                sentences = split_into_sentences(paragraph_text)
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
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentence.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentence)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif elem['type'] == 'image':
            # Display the image
            img_html = f'<img src="{elem["src"]}" alt="{elem["alt"]}" style="max-width:100%;">'
            html_content += img_html
        elif elem['type'] == 'figure':
            for fig_elem in elem['content']:
                if fig_elem['type'] == 'image':
                    img_html = f'<img src="{fig_elem["src"]}" alt="{fig_elem["alt"]}" style="max-width:100%;">'
                    html_content += img_html
                elif fig_elem['type'] == 'caption':
                    caption_style = """
                        font-family: Georgia, serif;
                        font-weight: 400;
                        font-size: 18px;
                        color: var(--text-color);
                        font-style: italic;
                        margin: 5px 0;
                    """
                    html_content += f"<div style='{caption_style}'>{fig_elem['content']}</div>"
        elif elem['type'] == 'caption':
            # Display caption
            caption_style = """
                font-family: Georgia, serif;
                font-weight: 400;
                font-size: 18px;
                color: var(--text-color);
                font-style: italic;
                margin: 5px 0;
            """
            html_content += f"<div style='{caption_style}'>{elem['content']}</div>"
        else:
            # Other content types
            pass

    # Display the HTML content using Streamlit
    st.write(html_content, unsafe_allow_html=True)


def main():
    # Inject CSS styles
    st.markdown("""
    <style>
    :root {
        --text-color: #f0f0f0;
        --primary-color: #f0f0f0;
        /* Dark theme colors */
        --color-1: #d32f2f;
        --color-2: #1976d2;
        --color-3: #388e3c;
        --color-4: #512da8;
        --color-5: rgba(251, 192, 45, 0.9);
    }

    @media (prefers-color-scheme: light) {
        :root {
            --text-color: #000;
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

        # Initialize chapters and chapter titles
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

            # Process the chapter content
            content_elements = process_chapter_content(soup)

            # Get indices of paragraph elements
            paragraph_indices = [i for i, elem in enumerate(content_elements) if elem['type'] == 'paragraph']

            # Initialize session state for the paragraph index
            if 'current_paragraph_idx' not in st.session_state:
                st.session_state.current_paragraph_idx = 0  # Index in paragraph_indices

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_idx > 0:
                        st.session_state.current_paragraph_idx -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_idx + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph_idx += 1

            # Display the paragraphs and other elements
            display_paragraphs(paragraph_indices, content_elements, st.session_state.current_paragraph_idx)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")


if __name__ == "__main__":
    main()
