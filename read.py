import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import bs4
import tempfile
import os

def process_chapter_content(soup):
    """
    Processes the chapter content and returns a list of content blocks.
    Each block is either a paragraph or a heading, along with its type.
    """
    content_blocks = []
    current_paragraph = {'type': 'paragraph', 'text': '', 'elements': []}

    # Define classes to identify different content types
    paragraph_classes = ['para', 'paraNoIndent', 'chapterOpenerText']
    heading_classes = ['chapterTitle', 'chapterNumber', 'chapterSubtitle', 'chapterSubtitle1', 'c2']
    ignore_classes = ['spaceBreak1', 'centerImage']
    caption_classes = ['caption']

    # Iterate over elements in order
    for elem in soup.body.descendants:
        if isinstance(elem, bs4.element.Tag):
            if elem.name == 'p':
                p_class = elem.get('class', [])
                if any(cls in paragraph_classes for cls in p_class):
                    # Save current paragraph if it has content
                    if current_paragraph['text'] or current_paragraph['elements']:
                        content_blocks.append(current_paragraph)
                        current_paragraph = {'type': 'paragraph', 'text': '', 'elements': []}
                    # Start a new paragraph
                    current_paragraph['text'] = elem.get_text(separator=' ').strip()
                    # Collect images in the paragraph
                    for img in elem.find_all('img'):
                        current_paragraph['elements'].append(str(img))
                elif any(cls in heading_classes for cls in p_class):
                    # Save current paragraph if it has content
                    if current_paragraph['text'] or current_paragraph['elements']:
                        content_blocks.append(current_paragraph)
                        current_paragraph = {'type': 'paragraph', 'text': '', 'elements': []}
                    # Append heading as a separate block
                    heading_text = elem.get_text(separator=' ').strip()
                    content_blocks.append({'type': 'heading', 'text': heading_text, 'elements': []})
                elif any(cls in caption_classes for cls in p_class):
                    # Add captions to the current paragraph elements
                    current_paragraph['elements'].append(str(elem))
                elif any(cls in ignore_classes for cls in p_class):
                    # Ignore these elements
                    pass
                else:
                    # Treat other <p> tags as part of the current paragraph elements
                    current_paragraph['elements'].append(str(elem))
            elif elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Save current paragraph if it has content
                if current_paragraph['text'] or current_paragraph['elements']:
                    content_blocks.append(current_paragraph)
                    current_paragraph = {'type': 'paragraph', 'text': '', 'elements': []}
                # Append heading as a separate block
                heading_text = elem.get_text(separator=' ').strip()
                content_blocks.append({'type': 'heading', 'text': heading_text, 'elements': []})
            elif elem.name == 'img':
                # Add images to the current paragraph elements
                current_paragraph['elements'].append(str(elem))
            elif elem.name == 'br':
                # Line breaks; can be ignored or handled as needed
                pass
            else:
                # Other tags can be handled as needed
                pass
        elif isinstance(elem, bs4.element.NavigableString):
            text = elem.strip()
            if text:
                current_paragraph['text'] += ' ' + text

    # Append the last paragraph if it exists
    if current_paragraph['text'] or current_paragraph['elements']:
        content_blocks.append(current_paragraph)

    return content_blocks

def display_paragraphs(paragraph_index, content_blocks):
    """
    Displays content blocks, highlighting the middle paragraph.
    Headings are displayed distinctly from paragraphs.
    """
    # Find indices of the previous, current, and next paragraphs
    paragraph_indices = [i for i, block in enumerate(content_blocks) if block['type'] == 'paragraph']
    if not paragraph_indices:
        st.write("No paragraphs to display.")
        return

    # Get the index positions in content_blocks
    current_para_pos = paragraph_indices[paragraph_index]
    prev_para_pos = paragraph_indices[paragraph_index - 1] if paragraph_index > 0 else None
    next_para_pos = paragraph_indices[paragraph_index + 1] if paragraph_index + 1 < len(paragraph_indices) else None

    # Collect content to display
    display_indices = [idx for idx in [prev_para_pos, current_para_pos, next_para_pos] if idx is not None]

    html_content = ""
    for idx in range(len(content_blocks)):
        block = content_blocks[idx]
        if block['type'] == 'heading':
            # Display heading
            heading_style = """
                font-family: Georgia, serif;
                font-weight: bold;
                font-size: 24px;
                color: var(--text-color);
                line-height: 1.6;
                max-width: 800px;
                margin: 20px auto 10px auto;
                padding: 10px;
                border-bottom: 2px solid var(--primary-color);
            """
            heading_html = f"<div style='{heading_style}'>{block['text']}</div>"
            html_content += heading_html
        elif idx in display_indices:
            para = block
            # Define base font style for readability
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
            # Combine the text and elements into the paragraph content
            paragraph_content = para['text']
            for elem_html in para['elements']:
                paragraph_content += elem_html

            # Highlight the middle paragraph
            is_highlighted = (idx == current_para_pos)
            if is_highlighted:
                sentences = paragraph_content.strip().split('. ')
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
                    # Ensure sentence ends with a period if not already present
                    if not sentence.strip().endswith('.'):
                        sentence = sentence.strip() + '.'
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_html = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_html}</div>"
            else:
                # Include any images or captions in the paragraph_html
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # For other paragraphs not in display indices, do nothing
            continue

    # Display the HTML content using Streamlit
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
        --color-5: rgba(251, 192, 45, 0.9);
        --text-color: #f0f0f0;
        --primary-color: #fff;
    }
    @media (prefers-color-scheme: light) {
        :root {
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9);
            --text-color: #000;
            --primary-color: #000;
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
                # Attempt to get the chapter title from the item's metadata or filename
                title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_content(), 'html.parser')
            # Use the process_chapter_content function to get content blocks
            content_blocks = process_chapter_content(soup)

            # Initialize session state for the paragraph index
            if 'current_paragraph' not in st.session_state:
                st.session_state.current_paragraph = 0

            # Total number of paragraphs
            paragraph_blocks = [block for block in content_blocks if block['type'] == 'paragraph']
            total_paragraphs = len(paragraph_blocks)

            # Display navigation buttons and paragraph info
            col1, col2, col3 = st.columns([1, 2, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph > 0:
                        st.session_state.current_paragraph -= 1
            with col2:
                st.write(f"Paragraph {st.session_state.current_paragraph + 1} of {total_paragraphs}")
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph + 1 < total_paragraphs:
                        st.session_state.current_paragraph += 1

            # Display the content
            display_paragraphs(st.session_state.current_paragraph, content_blocks)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
