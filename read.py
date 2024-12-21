import streamlit as st
import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, NavigableString
import tempfile
import os

def parse_body(element, content_elements):
    """
    Recursively parse an element, collecting paragraphs and images into content_elements.
    """
    for child in element.children:
        if isinstance(child, NavigableString):
            text = child.strip()
            if text:
                content_elements.append(('text', text))
        elif child.name == 'p':
            content = child.get_text(" ", strip=True)
            if content:
                content_elements.append(('text', content))
            # Process any images inside the paragraph
            for img in child.find_all('img'):
                content_elements.append(('image', str(img)))
        elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Skip headings
            continue
        elif child.name == 'img':
            # Handle images
            content_elements.append(('image', str(child)))
        else:
            # Recursively process the child element
            parse_body(child, content_elements)

def extract_content_elements(soup):
    """
    Extract content elements like paragraphs and images from the BeautifulSoup object,
    maintaining the order and skipping headings.
    """
    content_elements = []
    body = soup.find('body')
    if body is None:
        return content_elements
    parse_body(body, content_elements)
    return content_elements

def display_paragraphs(paragraph_index, content_elements):
    """
    Displays three content elements at a time, highlighting the middle one.
    """
    display_elements = content_elements[max(paragraph_index-1, 0):paragraph_index+2]
    html_content = ""

    for i, (content_type, content) in enumerate(display_elements):
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

        # Highlight the middle element
        is_highlighted = (paragraph_index == 0 and i == 0) or (paragraph_index != 0 and i == 1)

        if content_type == 'text':
            if is_highlighted:
                # Highlight the content
                sentences = content.strip().split('. ')
                highlighted_sentence = []
                for j, sentence in enumerate(sentences):
                    color_variable = f"var(--color-{j%5 +1})"
                    highlighted_style = f"""
                        background-color: {color_variable};
                        padding: 2px 5px;
                        border-radius: 5px;
                        color: var(--text-color);
                    """
                    # Ensure sentence ends with a period
                    if not sentence.endswith('.'):
                        sentence += '.'
                    sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
                    highlighted_sentence.append(sentence_html)
                paragraph_content = ' '.join(highlighted_sentence)
                html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
            else:
                # Display normally
                html_content += f"<div style='{font_style}'>{content}</div>"
        elif content_type == 'image':
            html_content += f"<div style='{font_style}'>{content}</div>"

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
        --primary-color: #FFFFFF;
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

    /* Hide Streamlit style elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Responsive font sizes */
    @media only screen and (max-width: 600px) {
        div[style] {
            font-size: 5vw !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("Reader")

    # File uploader in sidebar
    uploaded_file = st.sidebar.file_uploader("Choose an EPUB file", type="epub")

    if uploaded_file is not None:
        # Session state variables
        if 'selected_chapter' not in st.session_state:
            st.session_state.selected_chapter = None
        if 'content_elements' not in st.session_state:
            st.session_state.content_elements = []
        if 'current_paragraph' not in st.session_state:
            st.session_state.current_paragraph = 0

        # Temporary file for EPUB
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name

        try:
            # Load EPUB
            book = epub.read_epub(tmp_file_path)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return
        finally:
            os.remove(tmp_file_path)

        # Chapters and titles
        chapters = []
        chapter_titles = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item)
                # Get chapter title
                try:
                    soup = BeautifulSoup(item.content, 'html.parser')
                    title_tag = soup.find('title')
                    title = title_tag.string.strip() if title_tag else item.get_name()
                except:
                    title = item.get_name()
                chapter_titles.append(title)

        if chapters:
            # Chapter selector in sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)

            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            if selected_chapter != st.session_state.selected_chapter:
                st.session_state.selected_chapter = selected_chapter
                st.session_state.current_paragraph = 0
                soup = BeautifulSoup(selected_item.content, 'html.parser')
                st.session_state.content_elements = extract_content_elements(soup)

            content_elements = st.session_state.content_elements

            # Navigation buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_paragraph > 0:
                        st.session_state.current_paragraph -= 1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_paragraph + 1 < len(content_elements):
                        st.session_state.current_paragraph += 1

            # Display content
            display_paragraphs(st.session_state.current_paragraph, content_elements)
        else:
            st.error("No readable content found.")
    else:
        st.info("Please upload an EPUB file.")

if __name__ == "__main__":
    main()
