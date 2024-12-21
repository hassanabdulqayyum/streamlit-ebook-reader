import streamlit as st
import ebooklib
from ebooklib import epub
import bs4
from bs4 import BeautifulSoup, NavigableString, Tag
import tempfile
import os

def get_content_units(soup):
    """
    Processes the HTML content and returns a list of content units in the order they appear.
    Each content unit is a dictionary with 'type' and 'content' keys.
    """
    content_units = []

    def process_element(element):
        """Recursively process element and its children."""
        if isinstance(element, NavigableString):
            # Ignore strings directly under body/div, unless they contain meaningful text
            if element.strip():
                # Wrap the text in a paragraph unit if it's significant
                content_units.append({'type': 'text', 'content': str(element)})
            return
        elif isinstance(element, Tag):
            # Process the element based on its tag
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                # Heading
                content_units.append({'type': 'heading', 'content': str(element)})
            elif element.name == 'p':
                p_class = element.get('class', [])
                if not p_class:
                    p_class = []
                if 'para' in p_class or 'chapterOpenerText' in p_class:
                    # Regular paragraph
                    content_units.append({'type': 'paragraph', 'content': str(element)})
                elif 'caption' in p_class:
                    # Caption
                    content_units.append({'type': 'caption', 'content': str(element)})
                elif 'centerImage' in p_class:
                    # Image (wrapped in a <p> tag)
                    content_units.append({'type': 'image', 'content': str(element)})
                else:
                    # Other paragraph types
                    content_units.append({'type': 'other_p', 'content': str(element)})
            elif element.name == 'div':
                # Process children of the div
                for child in element.contents:
                    process_element(child)
            elif element.name == 'img':
                # Image
                content_units.append({'type': 'image', 'content': str(element)})
            elif element.name in ['ul', 'ol']:
                # List
                content_units.append({'type': 'list', 'content': str(element)})
            else:
                # Other tags
                pass  # Ignore or handle as needed
        else:
            # Other element types
            pass

    # Start processing from the body
    body = soup.find('body')
    if body:
        for elem in body.contents:
            process_element(elem)
    else:
        # Start from the root if body is not found
        for elem in soup.contents:
            process_element(elem)

    return content_units

def get_display_content(paragraph_index, content_units):
    """
    Given the current paragraph index, return the content units to display.
    Includes the previous, current, and next paragraphs, along with any associated non-paragraph content units.
    """
    # Build a list of indices of paragraphs
    paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']

    num_paragraphs = len(paragraph_indices)

    # Ensure paragraph_index is within bounds
    if paragraph_index < 0:
        paragraph_index = 0
    elif paragraph_index >= num_paragraphs:
        paragraph_index = num_paragraphs - 1

    # Get the positions in content_units for the previous, current, and next paragraphs
    curr_para_pos = paragraph_indices[paragraph_index]
    prev_para_pos = paragraph_indices[paragraph_index - 1] if paragraph_index > 0 else None
    next_para_pos = paragraph_indices[paragraph_index + 1] if paragraph_index + 1 < num_paragraphs else None

    # Determine start and end indices for slicing content_units
    start_idx = prev_para_pos if prev_para_pos is not None else curr_para_pos
    end_idx = next_para_pos if next_para_pos is not None else curr_para_pos

    # Collect content units from start_idx to end_idx inclusive
    display_units = content_units[start_idx:end_idx + 1]

    return display_units, paragraph_index

def display_paragraphs(display_units, paragraph_index, content_units):
    """
    Displays the content units, highlighting the current paragraph.
    """
    # Build a list of indices of paragraphs
    paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']
    curr_para_pos = paragraph_indices[paragraph_index]

    # Prepare the HTML content
    html_content = ""

    for cu in display_units:
        content_type = cu['type']
        content_html = cu['content']
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
        if content_type == 'heading':
            # Apply heading styles
            heading_style = font_style + "font-size: 24px; font-weight: bold;"
            html_content += f"<div style='{heading_style}'>{content_html}</div>"
        elif content_type == 'paragraph':
            # Determine if this is the current paragraph to highlight
            if content_units.index(cu) == curr_para_pos:
                # Highlight the paragraph
                sentences = BeautifulSoup(content_html, 'html.parser').get_text().split('. ')
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
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}{"." if not sentence.strip().endswith(".") else ""}</span>'
                    highlighted_sentences.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentences)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Regular paragraph style
                html_content += f"<div style='{font_style}'>{content_html}</div>"
        elif content_type == 'caption':
            # Apply caption style
            caption_style = font_style + "font-size: 18px; font-style: italic;"
            html_content += f"<div style='{caption_style}'>{content_html}</div>"
        elif content_type == 'image':
            # Apply image style
            image_style = "display: flex; justify-content: center; margin: 20px 0;"
            html_content += f"<div style='{image_style}'>{content_html}</div>"
        elif content_type == 'list':
            # Apply list style
            list_style = font_style
            html_content += f"<div style='{list_style}'>{content_html}</div>"
        else:
            # Default style for other content
            html_content += f"<div style='{font_style}'>{content_html}</div>"

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
            --color-5: rgba(251, 192, 45, 0.9);
            --text-color: #000000;
            --primary-color: #FFFFFF;
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
            # Use the get_content_units function to get content units
            content_units = get_content_units(soup)

            # Build a list of indices of paragraphs
            paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']

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

            # Get the display content units
            display_units, para_idx = get_display_content(st.session_state.current_paragraph, content_units)

            # Display the content units
            display_paragraphs(display_units, st.session_state.current_paragraph, content_units)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
