import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import nltk

# Ensure nltk punkt tokenizer is downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

def split_into_sentences(text):
    return nltk.sent_tokenize(text)

def get_content_blocks(soup):
    """
    Processes the HTML soup to generate a list of content blocks.
    Each block is a dict with keys 'type' and 'content'.
    Type can be 'heading', 'paragraph', 'image', 'caption', 'other'.
    """
    content_blocks = []
    body = soup.body or soup

    for element in body.contents:
        if isinstance(element, str):
            if element.strip():
                content_blocks.append({'type': 'text', 'content': element.strip()})
            continue
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            content_blocks.append({'type': 'heading', 'content': element})
        elif element.name == 'p':
            p_class = element.get('class', [])
            if any('caption' in cls.lower() for cls in p_class):
                content_blocks.append({'type': 'caption', 'content': element})
            else:
                content_blocks.append({'type': 'paragraph', 'content': element})
        elif element.name == 'img':
            content_blocks.append({'type': 'image', 'content': element})
        elif element.name in ['div', 'section', 'article']:
            # recursively process the contents
            content_blocks.extend(get_content_blocks(element))
        else:
            content_blocks.append({'type': element.name, 'content': element})

    return content_blocks

def display_content_blocks(block_index, content_blocks):
    """
    Displays three content blocks at a time, highlighting the middle one if it's a paragraph.
    Other elements like captions and images are displayed appropriately.
    """
    # Extract the three content blocks to be displayed
    display_blocks = content_blocks[max(block_index - 1, 0): block_index + 2]

    html_content = ""

    for i, block in enumerate(display_blocks):
        block_type = block['type']
        element = block['content']

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

        if block_type == 'heading':
            heading_style = font_style + """
                font-weight: bold;
                font-size: 24px;
                text-align: center;
            """
            heading_text = element.get_text()
            html_content += f"<div style='{heading_style}'>{heading_text}</div>"
        elif block_type == 'paragraph':
            # Highlight the middle paragraph (or first if at the beginning)
            is_highlighted = (block_index == 0 and i == 0) or (block_index != 0 and i == 1)

            paragraph_text = element.get_text()

            if is_highlighted:
                # Use NLTK's sentence tokenizer
                sentences = split_into_sentences(paragraph_text)
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
                    # Escape HTML in sentence
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
        elif block_type == 'image':
            # Generate the img tag
            img_html = str(element)
            html_content += f"<div style='text-align: center;'>{img_html}</div>"
        elif block_type == 'caption':
            caption_style = font_style + """
                font-style: italic;
                font-size: 16px;
                text-align: center;
            """
            caption_text = element.get_text()
            html_content += f"<div style='{caption_style}'>{caption_text}</div>"
        else:
            # For other types, render as is
            other_html = str(element)
            html_content += f"<div style='{font_style}'>{other_html}</div>"

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
                # Attempt to get the chapter title from the TOC
                title = item.get_name()
                # Alternatively, you can parse the item content to find the title
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Use the get_content_blocks function to get content blocks
            content_blocks = get_content_blocks(soup)

            # Initialize session state for the block index
            if 'current_block' not in st.session_state:
                st.session_state.current_block = 0

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_block > 0:
                        st.session_state.current_block -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_block + 1 < len(content_blocks):
                        st.session_state.current_block += 1

            # Display the content blocks
            display_content_blocks(st.session_state.current_block, content_blocks)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
