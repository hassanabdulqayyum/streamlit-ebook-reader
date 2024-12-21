import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, Tag, NavigableString
import tempfile
import os

def process_chapter_content(soup):
    """
    Processes the soup and returns a list of content elements in order.
    Each element is a dictionary with 'type' and 'content' keys.
    """
    content_list = []
    body = soup.find('body')
    if body is None:
        body = soup  # Sometimes, body might be missing; use the whole soup

    for element in body.contents:
        if isinstance(element, Tag):
            # Skip elements that are empty or whitespace
            if not element.text.strip() and not element.find('img'):
                continue

            if element.name == 'p':
                p_class = element.get('class', [])
                is_paragraph = 'para' in p_class or 'chapterOpenerText' in p_class or 'paraNoIndent' in p_class

                if is_paragraph:
                    content_list.append({'type': 'paragraph', 'content': str(element)})
                elif 'chapterSubtitle' in p_class or 'chapterSubtitle1' in p_class:
                    content_list.append({'type': 'subtitle', 'content': str(element)})
                else:
                    # Other types of paragraphs (e.g., captions)
                    content_list.append({'type': 'other', 'content': str(element)})
            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                content_list.append({'type': 'title', 'content': str(element)})
            elif element.name == 'img':
                content_list.append({'type': 'image', 'content': str(element)})
            elif element.name in ['ul', 'ol']:
                content_list.append({'type': 'list', 'content': str(element)})
            elif element.name == 'div':
                # Process divs if necessary
                content_list.append({'type': 'div', 'content': str(element)})
            else:
                # Other elements
                content_list.append({'type': element.name, 'content': str(element)})
        elif isinstance(element, NavigableString):
            # Handle text nodes
            text = element.strip()
            if text:
                content_list.append({'type': 'text', 'content': text})

    # Remove empty or whitespace-only elements
    content_list = [item for item in content_list if item['content'].strip()]

    return content_list

def display_elements(current_index, content_list):
    """
    Displays three elements at a time, centering on the current_index.
    Highlights the middle element if it's a paragraph.
    """
    # Extract the three elements to be displayed
    start_index = max(current_index - 1, 0)
    end_index = min(current_index + 2, len(content_list))
    display_elements = content_list[start_index:end_index]

    html_content = ""

    for i, element in enumerate(display_elements):
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

        # Highlight the middle element (or first if at the beginning)
        is_highlighted = (current_index == 0 and i == 0) or (current_index != 0 and i == 1)

        if is_highlighted and element['type'] == 'paragraph':
            # Highlight sentences with different colors
            paragraph_text = BeautifulSoup(element['content'], 'html.parser').get_text(separator=' ')
            sentences = paragraph_text.strip().split('. ')
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
                sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}{"." if not sentence.strip().endswith(".") else ""}</span>'
                highlighted_sentence.append(sentence_html)
            paragraph_content = ' '.join(highlighted_sentence)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # Include any images or captions in the element['content']
            html_content += f"<div style='{font_style}'>{element['content']}</div>"

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
        --text-color: #ffffff;
        --primary-color: #333333;
    }

    @media (prefers-color-scheme: light) {
        :root {
            /* Light theme colors */
            --color-1: #ffd54f;
            --color-2: #aed581;
            --color-3: #64b5f6;
            --color-4: #f06292;
            --color-5: rgba(251, 192, 45, 0.9); /* Adjust opacity here */
            --text-color: #000000;
            --primary-color: #dddddd;
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
                # Attempt to get the chapter title
                # If 'title' is not available, use the file name
                title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # Parse the HTML content of the chapter
            soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
            # Process the chapter content
            content_list = process_chapter_content(soup)

            if not content_list:
                st.error("No content to display in this chapter.")
                return

            # Initialize session state for the current index
            if 'current_index' not in st.session_state or st.session_state.chapter_index != chapter_index:
                st.session_state.current_index = 0
                st.session_state.chapter_index = chapter_index  # Track the current chapter

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_index > 0:
                        st.session_state.current_index -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_index + 1 < len(content_list):
                        st.session_state.current_index += 1

            # Display the elements
            display_elements(st.session_state.current_index, content_list)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
