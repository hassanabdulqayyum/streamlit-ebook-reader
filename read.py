import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, Tag
import html2text
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
        if isinstance(element, Tag):
            # Identify the content type
            content_type = None
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                content_type = 'heading'
            elif element.name == 'p':
                p_class = element.get('class', [])
                if not p_class:
                    p_class = []
                # Check for special paragraph classes
                if 'caption' in p_class:
                    content_type = 'caption'
                elif 'centerImage' in p_class:
                    content_type = 'image'
                elif 'chapterSubtitle' in p_class or 'chapterSubtitle1' in p_class or 'chapterOpenerText' in p_class:
                    content_type = 'heading'
                elif 'spaceBreak1' in p_class:
                    # Skip or handle as needed
                    return
                else:
                    content_type = 'paragraph'
            elif element.name in ['ul', 'ol']:
                content_type = 'list'
            elif element.name == 'div':
                # Process children of the div
                for child in element.contents:
                    process_element(child)
                return
            else:
                # For other tags, treat them based on their content
                content_type = 'other'

            # Convert the HTML element to Markdown using html2text
            html_content = str(element)
            content_markdown = html2text.html2text(html_content)

            # Append the content unit
            content_units.append({'type': content_type, 'content': content_markdown})
        else:
            # Ignore NavigableString and other types
            pass

    # Start processing from the body
    body = soup.find('body')
    if body:
        for elem in body.contents:
            process_element(elem)
    else:
        # Start from the soup if body is not found
        for elem in soup.contents:
            process_element(elem)

    return content_units

def get_display_content(paragraph_index, content_units):
    """
    Given the current paragraph index, return the content units to display.
    Includes the headings associated with each paragraph, and ensures three paragraphs are displayed.
    """
    # Build a list of indices of paragraphs
    paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']

    num_paragraphs = len(paragraph_indices)

    # Handle the case where no paragraphs are found
    if num_paragraphs == 0:
        return [], paragraph_index

    # Ensure paragraph_index is within bounds
    if paragraph_index < 0:
        paragraph_index = 0
    elif paragraph_index >= num_paragraphs:
        paragraph_index = num_paragraphs - 1

    # Get indices for the three paragraphs
    indices_to_show = []
    for offset in [-1, 0, 1]:
        para_idx = paragraph_index + offset
        if 0 <= para_idx < num_paragraphs:
            indices_to_show.append(para_idx)

    display_units = []
    for para_idx in indices_to_show:
        paragraph_pos = paragraph_indices[para_idx]

        # Collect any headings immediately preceding the paragraph
        idx = paragraph_pos - 1
        # Collect headings in reverse order until we hit a non-heading or non-caption element
        headings = []
        while idx >= 0 and content_units[idx]['type'] in ['heading', 'caption']:
            if content_units[idx]['type'] == 'heading':
                headings.insert(0, content_units[idx])  # Insert at the beginning
            idx -= 1

        # Add headings to display units
        display_units.extend(headings)

        # Add the paragraph
        display_units.append(content_units[paragraph_pos])

        # Collect any content units immediately after the paragraph that are not paragraphs
        idx = paragraph_pos + 1
        while idx < len(content_units) and content_units[idx]['type'] != 'paragraph':
            display_units.append(content_units[idx])
            idx += 1

    return display_units, paragraph_index

def display_paragraphs(display_units, paragraph_index, content_units):
    """
    Displays the content units, highlighting the current paragraph.
    """
    # Build a list of indices of paragraphs
    paragraph_indices = [i for i, cu in enumerate(content_units) if cu['type'] == 'paragraph']

    # Handle the case where no paragraphs are found
    if not paragraph_indices:
        st.warning("No paragraphs found in this chapter.")
        return

    curr_para_pos = paragraph_indices[paragraph_index]

    # Prepare the content for display
    for cu in display_units:
        content_type = cu['type']
        content = cu['content']

        if content_type == 'heading':
            # Apply heading styles
            st.markdown(f"## {content}", unsafe_allow_html=True)
        elif content_type == 'paragraph':
            # Determine if this is the current paragraph to highlight
            if cu == content_units[curr_para_pos]:
                # Highlight the paragraph
                # Split the paragraph into sentences
                sentences = content.strip().split('. ')
                highlighted_sentences = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{(j%5)+1})"
                    highlighted_style = f"background-color: {color_variable}; border-radius:5px; padding:2px;"
                    if not sentence.endswith('.'):
                        sentence += '.'
                    highlighted_sentences.append(f"<span style='{highlighted_style}'>{sentence.strip()}</span>")
                paragraph_content = ' '.join(highlighted_sentences)
                st.markdown(paragraph_content, unsafe_allow_html=True)
            else:
                # Regular paragraph
                st.markdown(content, unsafe_allow_html=True)
        elif content_type == 'list':
            # Display list
            st.markdown(content, unsafe_allow_html=True)
        elif content_type == 'caption':
            # Display caption
            st.markdown(f"*{content}*", unsafe_allow_html=True)
        elif content_type == 'image':
            # Display image (you may need additional logic to display images)
            st.markdown(content, unsafe_allow_html=True)
        else:
            # Other content
            st.markdown(content, unsafe_allow_html=True)

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
