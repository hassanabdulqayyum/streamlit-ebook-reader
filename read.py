import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, Tag, NavigableString
import tempfile
import os
import nltk

# Download the necessary data for sentence tokenization
nltk.download('punkt')

def parse_chapter_content(soup):
    """
    Parses the chapter content and returns a list of content elements, maintaining their order.
    Each element is a dictionary with 'type' and 'content' keys.
    """
    content_elements = []
    
    # Get the content within the body tag
    body = soup.find('body')
    if not body:
        body = soup  # Fallback to the whole soup
    
    # Iterate over the direct children of the body
    for element in body.contents:
        if isinstance(element, Tag):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                content_elements.append({'type': 'heading', 'content': element.get_text(strip=True)})
            elif element.name == 'p':
                # Accept all 'p' tags as paragraphs
                content_elements.append({'type': 'paragraph', 'content': element.get_text(separator=' ', strip=True)})
            elif element.name == 'img':
                # Handle images
                content_elements.append({'type': 'image', 'content': element})
            elif element.name == 'figure':
                # Handle figures, may contain images and captions
                content_elements.append({'type': 'figure', 'content': element})
            elif element.name == 'table':
                # Handle tables if needed
                content_elements.append({'type': 'table', 'content': element})
            else:
                # Handle other tags or skip
                pass
        elif isinstance(element, NavigableString):
            # Handle navigable strings if they contain meaningful text
            text = element.strip()
            if text:
                content_elements.append({'type': 'text', 'content': text})
    return content_elements

def split_into_sentences(text):
    from nltk.tokenize import sent_tokenize
    sentences = sent_tokenize(text)
    return sentences

def display_paragraph(paragraph_text, is_current_paragraph):
    """
    Displays a paragraph.
    If is_current_paragraph is True, highlights sentences with different colors.
    """
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
        overflow-wrap: break-word;
    """
    
    if is_current_paragraph:
        # Split paragraph into sentences
        sentences = split_into_sentences(paragraph_text)
        highlighted_sentences = []
        for idx, sentence in enumerate(sentences):
            color_variable = f"var(--color-{idx % 5 +1})"
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
    else:
        paragraph_content = paragraph_text

    html_content = f"<div style='{font_style}'>{paragraph_content}</div>"
    
    st.write(html_content, unsafe_allow_html=True)

def display_heading(heading_text):
    """
    Displays a heading.
    """
    # Define heading style
    heading_style = """
        font-family: Georgia, serif;
        font-weight: bold;
        font-size: 24px;
        color: var(--text-color);
        line-height: 1.6;
        margin: 20px 0 10px 0;
        padding: 0;
    """
    html_content = f"<h2 style='{heading_style}'>{heading_text}</h2>"
    st.write(html_content, unsafe_allow_html=True)

def display_image(image_element):
    """
    Displays an image.
    """
    # Extract the 'src' attribute
    src = image_element.get('src')
    if src:
        # Handle data URIs or base64 images if needed
        html_content = str(image_element)
        st.write(html_content, unsafe_allow_html=True)

def display_figure(figure_element):
    """
    Displays a figure, including images and captions.
    """
    html_content = str(figure_element)
    st.write(html_content, unsafe_allow_html=True)

def display_paragraphs(paragraph_number, content_elements, paragraph_indices):
    """
    Displays three paragraphs at a time, with the current paragraph highlighted.
    Also displays other content elements appropriately.
    """
    # Get the indices of the paragraphs to display
    paragraph_numbers_to_display = []
    if paragraph_number > 0:
        paragraph_numbers_to_display.append(paragraph_number - 1)
    paragraph_numbers_to_display.append(paragraph_number)
    if paragraph_number + 1 < len(paragraph_indices):
        paragraph_numbers_to_display.append(paragraph_number + 1)
    
    # Get the content_elements indices of the paragraphs
    indices_to_display = [paragraph_indices[num] for num in paragraph_numbers_to_display]
    
    # Find the minimal and maximal indices to determine the range
    min_index = min(indices_to_display)
    max_index = max(indices_to_display)
    
    # Display content_elements from min_index to max_index inclusive
    for i in range(min_index, max_index + 1):
        element = content_elements[i]
        is_current_paragraph = (i == paragraph_indices[paragraph_number])
        
        if element['type'] == 'paragraph':
            display_paragraph(element['content'], is_current_paragraph)
        elif element['type'] == 'heading':
            display_heading(element['content'])
        elif element['type'] == 'image':
            display_image(element['content'])
        elif element['type'] == 'figure':
            display_figure(element['content'])
        else:
            # Handle other types or ignore
            pass

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
        --text-color: #f0f0f0;
        --primary-color: #ffffff;
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
            --primary-color: #000000;
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

            # Use the parse_chapter_content function to get content elements
            content_elements = parse_chapter_content(soup)
            paragraph_indices = [i for i, elem in enumerate(content_elements) if elem['type'] == 'paragraph']

            if not paragraph_indices:
                st.error("No paragraphs found in this chapter.")
                return

            # Initialize session state for current paragraph number
            if 'current_paragraph_number' not in st.session_state:
                st.session_state.current_paragraph_number = 0
            else:
                # Reset paragraph number if a new chapter is selected
                if st.session_state.get('last_selected_chapter') != selected_chapter:
                    st.session_state.current_paragraph_number = 0

            st.session_state['last_selected_chapter'] = selected_chapter

            # Display navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph_number > 0:
                        st.session_state.current_paragraph_number -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph_number + 1 < len(paragraph_indices):
                        st.session_state.current_paragraph_number += 1

            # Display the paragraphs and other content
            display_paragraphs(st.session_state.current_paragraph_number, content_elements, paragraph_indices)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
