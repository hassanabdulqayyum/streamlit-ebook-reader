import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString
import re
import tempfile
import os

class ContentBlock:
    def __init__(self, block_type, content):
        self.block_type = block_type  # 'heading', 'paragraph', 'image', 'caption', etc.
        self.content = content  # HTML content or text content

def get_content_blocks(soup):
    """
    Parses the HTML soup and returns a list of ContentBlock objects.
    Differentiates between headings, paragraphs, images, captions, etc.
    """
    content_blocks = []

    # Find the body or the main content container
    body = soup.find('body')
    if not body:
        body = soup

    # Iterate over the elements in the body
    for element in body.descendants:
        if isinstance(element, NavigableString):
            continue  # Skip text nodes directly under body

        if element.name == 'p':
            # Check for class or other attributes to distinguish between paragraph and captions
            p_class = element.get('class', [])
            if 'caption' in p_class or 'ImageCaption' in p_class:
                block_type = 'caption'
            else:
                block_type = 'paragraph'
            content_blocks.append(ContentBlock(block_type, str(element)))
        
        elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            content_blocks.append(ContentBlock('heading', str(element)))

        elif element.name == 'img':
            content_blocks.append(ContentBlock('image', str(element)))

        elif element.name == 'figure':
            content_blocks.append(ContentBlock('figure', str(element)))

        elif element.name == 'div':
            # Sometimes content may be within divs
            # You can choose to process divs recursively or skip them
            pass  # For now, skip divs to prevent duplication
            
        elif element.name in ['ol', 'ul']:
            # List items
            content_blocks.append(ContentBlock('list', str(element)))

        elif element.name == 'table':
            # Tables
            content_blocks.append(ContentBlock('table', str(element)))

        else:
            # For other tags, you can decide to include or exclude them
            pass

    return content_blocks

def get_display_indices(content_blocks, paragraph_indices, current_paragraph_idx):
    """
    Returns the positions in content_blocks to display, including the previous, current, and next paragraphs,
    along with any non-paragraph content blocks in between.
    """
    positions_to_display = []

    # Get positions of previous, current, and next paragraphs in content_blocks
    current_para_pos = paragraph_indices[current_paragraph_idx]

    if current_paragraph_idx > 0:
        prev_para_pos = paragraph_indices[current_paragraph_idx -1]
    else:
        prev_para_pos = current_para_pos  # If at the beginning

    if current_paragraph_idx +1 < len(paragraph_indices):
        next_para_pos = paragraph_indices[current_paragraph_idx +1]
    else:
        next_para_pos = current_para_pos  # If at the end

    # Now, get all content_blocks from prev_para_pos to next_para_pos (inclusive)
    start_pos = min(prev_para_pos, current_para_pos, next_para_pos)
    end_pos = max(prev_para_pos, current_para_pos, next_para_pos)

    # Get all indices from start_pos to end_pos, including any content in between
    positions_to_display = list(range(start_pos, end_pos +1))

    return positions_to_display

def display_paragraphs(content_blocks, current_paragraph_idx, paragraph_indices, positions_to_display):
    """
    Displays content blocks, highlighting the current paragraph.
    """
    html_content = ""

    # Map from paragraph_indices to content_blocks index
    current_para_pos = paragraph_indices[current_paragraph_idx]

    # CSS styles
    styles = {
        'paragraph': """
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
        """,
        'heading': """
            font-family: Georgia, serif;
            font-weight: bold;
            font-size: 24px;
            color: var(--text-color);
            line-height: 1.6;
            max-width: 1000px;
            margin: 20px auto;
            padding: 15px;
        """,
        'caption': """
            font-family: Georgia, serif;
            font-size: 16px;
            font-style: italic;
            color: var(--text-color);
            line-height: 1.4;
            max-width: 1000px;
            margin: 10px auto;
            padding: 10px;
        """,
        'image': """
            display: block;
            margin: 20px auto;
            max-width: 100%;
            height: auto;
        """
    }

    for pos in positions_to_display:
        block = content_blocks[pos]

        if block.block_type == 'paragraph':
            # Check if this is the current paragraph to highlight
            is_highlighted = (pos == current_para_pos)
            # Parse the paragraph_html to get the text
            soup = BeautifulSoup(block.content, 'html.parser')

            # Clean text to remove references (superscripts)
            for sup in soup.find_all('sup'):
                sup.extract()
            paragraph_text = soup.get_text(separator=' ', strip=True)

            # Now split sentences
            # Split sentences using regex that tries to avoid common abbreviations
            # Note: This may not be perfect
            pattern = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s')
            sentences = pattern.split(paragraph_text)

            if is_highlighted:
                # Highlight sentences
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
                html_content += f"<div style='{styles['paragraph']}'>{paragraph_content}</div>"
            else:
                # Non-highlighted paragraph
                paragraph_content = ' '.join(sentences)
                html_content += f"<div style='{styles['paragraph']}'>{paragraph_content}</div>"
        elif block.block_type == 'heading':
            html_content += f"<div style='{styles['heading']}'>{block.content}</div>"
        elif block.block_type == 'image':
            # Include image
            # For images, adjust the src if necessary
            soup = BeautifulSoup(block.content, 'html.parser')
            img_tag = soup.find('img')
            if img_tag:
                img_tag['style'] = styles['image']
                img_html = str(img_tag)
                html_content += f"<div style='text-align:center'>{img_html}</div>"
        elif block.block_type == 'caption':
            html_content += f"<div style='{styles['caption']}'>{block.content}</div>"
        elif block.block_type in ['list', 'table']:
            # Include lists and tables
            html_content += f"<div style='{styles['paragraph']}'>{block.content}</div>"
        else:
            # Other block types
            html_content += f"<div style='{styles['paragraph']}'>{block.content}</div>"

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
            --color-5: rgba(251, 192, 45, 0.9);
        }
    }

    /* Hide the Streamlit style elements */
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
                # Get the chapter title
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

            # Use the get_content_blocks function to get content blocks
            content_blocks = get_content_blocks(soup)

            # Create a list of indices where the blocks are paragraphs
            paragraph_indices = [i for i, block in enumerate(content_blocks) if block.block_type == 'paragraph']
            
            if not paragraph_indices:
                st.error("No paragraphs found in this chapter.")
                return

            # Initialize session state for the paragraph index
            if 'current_paragraph_idx' not in st.session_state:
                st.session_state.current_paragraph_idx = 0
                st.session_state.selected_chapter = selected_chapter
            else:
                # Reset current_paragraph_idx if a new chapter is selected
                if st.session_state.selected_chapter != selected_chapter:
                    st.session_state.current_paragraph_idx = 0
                    st.session_state.selected_chapter = selected_chapter

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_idx > 0:
                        st.session_state.current_paragraph_idx -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_idx +1 < len(paragraph_indices):
                        st.session_state.current_paragraph_idx +=1

            # Get positions to display
            positions_to_display = get_display_indices(content_blocks, paragraph_indices, st.session_state.current_paragraph_idx)

            # Display the paragraphs and associated content
            display_paragraphs(content_blocks, st.session_state.current_paragraph_idx, paragraph_indices, positions_to_display)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
