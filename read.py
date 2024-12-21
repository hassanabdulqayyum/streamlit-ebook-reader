import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import tempfile
import os
import re

def extract_chapter_content(item):
    """
    Extracts and converts the HTML content of a chapter to Markdown.
    """
    html_content = item.get_body_content().decode("utf-8")
    # Convert HTML to Markdown
    markdown_content = md(html_content, heading_style="ATX")
    return markdown_content

def split_into_blocks(markdown_content):
    """
    Splits the Markdown content into blocks (paragraphs, headings, lists, etc.).
    We'll use two newlines as a separator.
    """
    blocks = re.split(r'\n\s*\n', markdown_content.strip())
    return blocks

def get_display_blocks(paragraph_index, blocks):
    """
    Given the current paragraph index, return the blocks to display.
    Ensures three paragraphs (or blocks) are displayed, with the middle one highlighted.
    """
    num_blocks = len(blocks)

    # Ensure paragraph_index is within bounds
    if paragraph_index < 0:
        paragraph_index = 0
    elif paragraph_index >= num_blocks:
        paragraph_index = num_blocks - 1

    # Get indices for the three blocks
    indices_to_show = []
    for offset in [-1, 0, 1]:
        idx = paragraph_index + offset
        if 0 <= idx < num_blocks:
            indices_to_show.append(idx)

    display_blocks = [blocks[i] for i in indices_to_show]
    return display_blocks, paragraph_index

def display_blocks(display_blocks, paragraph_index, blocks):
    """
    Displays the content blocks, highlighting the current paragraph.
    """
    current_block_index = blocks.index(display_blocks[1])  # Middle block

    st.markdown(f"<div style='font-family: Georgia, serif; font-size: 20px; line-height: 1.6;'>", unsafe_allow_html=True)

    for i, block in enumerate(display_blocks):
        block_index = current_block_index + i - 1  # Adjust index based on position
        # Check if the block is the current one to highlight
        if block_index == paragraph_index:
            # Highlight the block
            highlighted_block = highlight_block(block)
            st.markdown(highlighted_block, unsafe_allow_html=True)
        else:
            # Render normally
            st.markdown(block)

    st.markdown("</div>", unsafe_allow_html=True)

def highlight_block(block):
    """
    Adds HTML styles to highlight the block.
    """
    # Split block into sentences
    sentences = re.split(r'(?<=[.!?])\s+', block.strip())
    highlighted_sentences = []
    for j, sentence in enumerate(sentences):
        color_variable = f"var(--color-{j%5 +1})"
        highlighted_style = f"""
            background-color: {color_variable};
            padding: 2px 5px;
            border-radius: 5px;
            color: var(--text-color);
        """
        sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
        highlighted_sentences.append(sentence_html)
    highlighted_block = ' '.join(highlighted_sentences)
    return highlighted_block

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
        --color-5: #FBC02D;
        --text-color: #FFFFFF;
        --primary-color: #0E1117;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: #FBC02D;
            --text-color: #000000;
            --primary-color: #FFFFFF;
        }
    }

    /* Hide the Streamlit style elements (hamburger menu, header, footer) */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

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

            # Extract and convert chapter content to Markdown
            markdown_content = extract_chapter_content(selected_item)
            # Split content into blocks
            blocks = split_into_blocks(markdown_content)

            # Initialize session state for the paragraph index
            if 'current_paragraph' not in st.session_state or st.session_state.chapter != selected_chapter:
                st.session_state.current_paragraph = 0
                st.session_state.chapter = selected_chapter  # Keep track of selected chapter

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph > 0:
                        st.session_state.current_paragraph -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph + 1 < len(blocks):
                        st.session_state.current_paragraph += 1

            # Get the display blocks
            display_blocks, para_idx = get_display_blocks(st.session_state.current_paragraph, blocks)

            # Display the blocks
            display_blocks(display_blocks, st.session_state.current_paragraph, blocks)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
