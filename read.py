import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os
import re

def get_processed_elements(soup):
    """
    Processes the HTML soup to generate a list of elements with type and content.
    Types: heading, paragraph, image, caption, others.
    """
    elements = []

    for elem in soup.body.children:
        if isinstance(elem, bs4.element.Tag):
            if elem.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                elements.append({'type': 'heading', 'content': str(elem)})
            elif elem.name == 'p':
                p_class = elem.get('class', [])
                if 'caption' in p_class or 'image-caption' in p_class:
                    elements.append({'type': 'caption', 'content': str(elem)})
                elif elem.find('img'):
                    elements.append({'type': 'image', 'content': str(elem)})
                else:
                    elements.append({'type': 'paragraph', 'content': str(elem)})
            elif elem.name == 'img':
                elements.append({'type': 'image', 'content': str(elem)})
            else:
                elements.append({'type': 'other', 'content': str(elem)})
        elif isinstance(elem, bs4.element.NavigableString):
            text = elem.strip()
            if text:
                elements.append({'type': 'text', 'content': text})
    return elements

def split_sentences(paragraph_text):
    # Define a pattern for sentence splitting that avoids splitting on common abbreviations and references
    pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(pattern, paragraph_text.strip())
    return sentences

def display_paragraphs(paragraph_idx, all_elements, paragraph_indices):
    """
    Displays three paragraphs at a time, highlighting the middle one.
    Other elements like headings, captions, images are displayed appropriately.
    """
    num_paragraphs = len(paragraph_indices)

    # Get indices of previous, current, next paragraphs
    prev_paragraph_idx = paragraph_idx - 1 if paragraph_idx > 0 else None
    next_paragraph_idx = paragraph_idx + 1 if paragraph_idx + 1 < num_paragraphs else None

    # Get element indices
    indices = []
    if prev_paragraph_idx is not None:
        indices.append(paragraph_indices[prev_paragraph_idx])
    indices.append(paragraph_indices[paragraph_idx])
    if next_paragraph_idx is not None:
        indices.append(paragraph_indices[next_paragraph_idx])

    # Now find the start and end element indices to include all elements between them
    start_elem_idx = indices[0]
    end_elem_idx = indices[-1] + 1  # +1 because slicing in Python is exclusive at end

    # Get elements to display
    elements_to_display = all_elements[start_elem_idx:end_elem_idx]

    html_content = ""

    # The indices of paragraphs among the elements_to_display
    paragraph_positions = [i for i, elem in enumerate(elements_to_display) if elem['type'] == 'paragraph']

    for i, elem in enumerate(elements_to_display):
        elem_type = elem['type']
        elem_content = elem['content']

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
            /* Remove or set background-color to transparent */
            /* background-color: transparent; */
            transition: text-shadow 0.5s;
        """
        
        # Adjust font style based on element type
        if elem_type == 'heading':
            # Display heading
            heading_style = font_style + """
                font-size: 24px;
                font-weight: bold;
                text-align: center;
            """
            html_content += f"<div style='{heading_style}'>{elem_content}</div>"
        elif elem_type == 'paragraph':
            # Check if this is the current paragraph to highlight
            para_position_in_elements = paragraph_positions.index(i)
            is_highlighted = (paragraph_idx == 0 and para_position_in_elements == 0) \
                             or (paragraph_idx != 0 and para_position_in_elements == 1)
            if is_highlighted:
                # Highlight the paragraph by coloring sentences
                paragraph_text = BeautifulSoup(elem_content, 'html.parser').get_text()

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
                
                # Use the HTML paragraph tags
                paragraph_style = font_style + """
                    /* Additional styles if needed */
                """
                html_content += f"<div style='{paragraph_style}'>{paragraph_content}</div>"
            else:
                # Regular paragraph
                html_content += f"<div style='{font_style}'>{elem_content}</div>"
        elif elem_type == 'image':
            # Display image
            html_content += f"<div style='text-align:center;'>{elem_content}</div>"
        elif elem_type == 'caption':
            # Display caption
            caption_style = font_style + """
                font-style: italic;
                font-size: 16px;
                text-align: center;
            """
            html_content += f"<div style='{caption_style}'>{elem_content}</div>"
        else:
            # Other types, display normally
            html_content += f"<div style='{font_style}'>{elem_content}</div>"

    # Display the HTML content
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
        --highlight-color: rgba(251, 192, 45, 0.3);
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9);
            --highlight-color: rgba(251, 192, 45, 0.3);
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
            all_elements = get_processed_elements(soup)
            paragraph_indices = [i for i, elem in enumerate(all_elements) if elem['type'] == 'paragraph']

            # Initialize session state for the current paragraph index (among paragraphs)
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
                    if st.session_state.current_paragraph_idx + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph_idx += 1

            # Display the paragraphs
            display_paragraphs(st.session_state.current_paragraph_idx, all_elements, paragraph_indices)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
