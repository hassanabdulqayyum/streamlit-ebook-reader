import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os

def get_processed_paragraphs(soup):
    """
    Processes the HTML soup to generate a list of content elements.
    Separates paragraphs, titles, images, and other elements based on their HTML classes.
    """
    elements = []
    temp_content = ''
    tags = soup.find_all(['p', 'h1', 'h2', 'h3', 'img', 'div', 'ul', 'ol'])

    for tag in tags:
        tag_name = tag.name
        tag_class = tag.get('class', [])

        # Identify and process paragraphs
        if tag_name == 'p' and ('para' in tag_class or 'paraNoIndent' in tag_class or 'chapterOpenerText' in tag_class):
            elements.append({'type': 'paragraph', 'content': str(tag)})

        # Identify and process titles and headings
        elif tag_name in ['h1', 'h2', 'h3'] or ('chapterTitle' in tag_class or 'chapterSubtitle' in tag_class):
            elements.append({'type': 'title', 'content': str(tag)})

        # Identify and process images
        elif tag_name == 'img' or 'centerImage' in tag_class:
            elements.append({'type': 'image', 'content': str(tag)})

        # Identify and process lists
        elif tag_name in ['ul', 'ol']:
            elements.append({'type': 'list', 'content': str(tag)})

        # Identify and process other div elements
        elif tag_name == 'div':
            elements.append({'type': 'div', 'content': str(tag)})

        # Other content
        else:
            elements.append({'type': 'other', 'content': str(tag)})

    return elements

def display_paragraphs(paragraph_index, elements):
    """
    Displays three content elements at a time, highlighting the middle paragraph if present.
    Properly handles titles, images, and other elements.
    """
    # Extract the three elements to be displayed
    display_elements = elements[max(paragraph_index-1, 0):paragraph_index+2]

    html_content = ""

    for i, element in enumerate(display_elements):
        element_type = element['type']
        element_content = element['content']

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
            border: 1px solid var(--primary-color);
            transition: text-shadow 0.5s;
        """

        # Highlight the middle paragraph (or first if at the beginning)
        is_highlighted = (paragraph_index == 0 and i == 0) or (paragraph_index != 0 and i == 1)

        if element_type == 'paragraph' and is_highlighted:
            # Highlight sentences with different colors
            soup = BeautifulSoup(element_content, 'html.parser')
            paragraph_text = soup.get_text(separator=' ')
            sentences = paragraph_text.strip().split('. ')
            highlighted_sentence = []
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
                # Ensure punctuation is included
                if not sentence.endswith('.'):
                    sentence += '.'
                sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                highlighted_sentence.append(sentence_html)
            paragraph_content = ' '.join(highlighted_sentence)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # Use different styling for titles and other elements
            if element_type == 'title':
                element_font_style = font_style + "font-size: 24px; font-weight: bold;"
            elif element_type == 'image':
                element_font_style = font_style + "text-align: center;"
            else:
                element_font_style = font_style

            html_content += f"<div style='{element_font_style}'>{element_content}</div>"

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
                # Attempt to get the chapter title from the item's headers
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                title_tag = soup.find(['h1', 'h2'], class_='chapterTitle')
                if title_tag:
                    title = title_tag.get_text()
                else:
                    title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_content(), 'html.parser')
            # Use the get_processed_paragraphs function to get elements
            chapter_elements = get_processed_paragraphs(soup)

            # Filter only paragraphs and appropriate elements for navigation
            navigable_indices = [i for i, e in enumerate(chapter_elements) if e['type'] == 'paragraph']

            # Initialize session state for the paragraph index
            if 'current_paragraph_index' not in st.session_state:
                st.session_state.current_paragraph_index = 0
                st.session_state.paragraph_positions = navigable_indices

            # Reset index if chapter changes
            if 'last_chapter' not in st.session_state or st.session_state.last_chapter != selected_chapter:
                st.session_state.current_paragraph_index = 0
                st.session_state.paragraph_positions = navigable_indices
                st.session_state.last_chapter = selected_chapter

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_index > 0:
                        st.session_state.current_paragraph_index -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_index + 1 < len(st.session_state.paragraph_positions):
                        st.session_state.current_paragraph_index += 1

            # Get the current position
            current_position = st.session_state.paragraph_positions[st.session_state.current_paragraph_index]

            # Display the elements
            display_paragraphs(current_position, chapter_elements)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
