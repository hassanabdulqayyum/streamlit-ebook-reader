import streamlit as st
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os

# Colors for highlighting sentences
colors = ["#ffd54f", "#aed581", "#64b5f6", "#f06292", "#ba68c8"]  # Lighter pastel shades

def get_color(index):
    # Cycle through the color list based on the sentence index
    return colors[index % len(colors)]

def get_processed_paragraphs(soup):
    """
    Processes the HTML soup to generate a list of paragraph contents.
    Non-paragraph elements like captions and images are appended to the next paragraph.
    """
    processed_paragraphs = []
    temp_content = ''
    p_tags = soup.find_all('p')
    
    for p in p_tags:
        p_class = p.get('class', [])
        is_paragraph = 'para' in p_class or 'chapterOpenerText' in p_class

        if is_paragraph:
            # Append temp content to this paragraph if temp_content is not empty
            if temp_content:
                full_content = temp_content + '\n' + str(p)
                temp_content = ''
            else:
                full_content = str(p)
            processed_paragraphs.append(full_content)
        else:
            # Collect the content in temp_content to be added to the next paragraph
            temp_content += str(p) + '\n'
    
    # Handle any remaining temp_content (if last elements are not paragraphs)
    if temp_content:
        # Append to the last paragraph if exists, else add as a new paragraph
        if processed_paragraphs:
            processed_paragraphs[-1] += '\n' + temp_content
        else:
            processed_paragraphs.append(temp_content)
    
    return processed_paragraphs

def display_paragraphs(paragraph_index, processed_paragraphs):
    """
    Displays three paragraphs at a time, highlighting the middle one.
    Other elements like captions and images are displayed as part of the paragraph.
    """
    # Extract the three paragraphs to be displayed
    display_paragraphs = processed_paragraphs[max(paragraph_index-1, 0):paragraph_index+2]
    
    html_content = ""

    for i, paragraph_html in enumerate(display_paragraphs):
        # Define base font style for readability
        font_style = """
            font-family: Georgia, serif;
            font-weight: 400;
            font-size: 20px;  /* Adjusted font size for better readability */
            color: #333333;
            line-height: 1.6;
            max-width: 1000px;
            margin: 20px auto;
            padding: 15px;
            border: 1px solid #ddd;
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.1);
            background-color: #f7f7f7;
            transition: text-shadow 0.5s;
        """
        highlighted_style = """
                background-color: {color};
                padding: 2px 5px;
                border-radius: 5px;
        """
        
        # Parse the paragraph_html to get the text
        soup = BeautifulSoup(paragraph_html, 'html.parser')
        
        # Get the combined text of the paragraph and any associated elements
        paragraph_text = ''
        for content in soup.contents:
            if content.name == 'p':
                paragraph_text += content.get_text(separator=' ') + ' '
            else:
                paragraph_text += str(content) + ' '  # Include images or other tags
        
        # Highlight the middle paragraph (or first if at the beginning)
        is_highlighted = (paragraph_index == 0 and i == 0) or (paragraph_index != 0 and i == 1)
        
        if is_highlighted:
            sentences = paragraph_text.strip().split('. ')
            highlighted_sentence = [
                f'<span style="{highlighted_style.format(color=get_color(j))}">{sentence.strip()}{"." if not sentence.strip().endswith(".") else ""}</span>'
                for j, sentence in enumerate(sentences)]
            paragraph_content = ' '.join(highlighted_sentence)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            # Include any images or captions in the paragraph_html
            html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
    
    # Display the HTML content using Streamlit
    st.write(html_content, unsafe_allow_html=True)

def main():
    st.title("EPUB Reader")

    # Initialize session state variables
    if 'file_uploaded' not in st.session_state:
        st.session_state.file_uploaded = False
    if 'chapter_selected' not in st.session_state:
        st.session_state.chapter_selected = False
    if 'book' not in st.session_state:
        st.session_state.book = None
    if 'chapter_paragraphs' not in st.session_state:
        st.session_state.chapter_paragraphs = []
    if 'current_paragraph' not in st.session_state:
        st.session_state.current_paragraph = 0

    # File uploader allows users to select an EPUB file
    if not st.session_state.file_uploaded:
        uploaded_file = st.file_uploader("Choose an EPUB file", type="epub")
        if uploaded_file is not None:
            # Create a temporary file to store the EPUB file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name

            try:
                # Load the EPUB file from the temporary file path
                st.session_state.book = epub.read_epub(tmp_file_path)
                st.session_state.file_uploaded = True
            except Exception as e:
                st.error(f"An error occurred while reading the EPUB file: {e}")
                return
            finally:
                # Clean up the temporary file
                os.remove(tmp_file_path)
    elif not st.session_state.chapter_selected:
        # Initialize the chapter content
        chapters = []
        chapter_titles = []
        for item in st.session_state.book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                chapters.append(item)
                # Attempt to get the chapter title
                title = item.get_name()
                # Alternatively, use item.get_title() if available
                chapter_titles.append(title)
        
        if chapters:
            selected_chapter = st.selectbox("Select a chapter", chapter_titles)
            if st.button("Load Chapter"):
                chapter_index = chapter_titles.index(selected_chapter)
                selected_item = chapters[chapter_index]
                # Parse the HTML content of the chapter
                soup = BeautifulSoup(selected_item.get_body_content(), 'html.parser')
                # Use the get_processed_paragraphs function to get paragraphs
                st.session_state.chapter_paragraphs = get_processed_paragraphs(soup)
                
                if not st.session_state.chapter_paragraphs:
                    st.error("No readable content found in the selected chapter.")
                    return
                st.session_state.chapter_selected = True
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        # Display navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Previous"):
                if st.session_state.current_paragraph > 0:
                    st.session_state.current_paragraph -= 1
        with col3:
            if st.button("Next"):
                if st.session_state.current_paragraph + 1 < len(st.session_state.chapter_paragraphs):
                    st.session_state.current_paragraph += 1

        # Display the paragraphs
        display_paragraphs(st.session_state.current_paragraph, st.session_state.chapter_paragraphs)
        
        # Add a Restart button
        if st.button("Restart"):
            # Reset the session state
            st.session_state.file_uploaded = False
            st.session_state.chapter_selected = False
            st.session_state.book = None
            st.session_state.chapter_paragraphs = []
            st.session_state.current_paragraph = 0
            st.experimental_rerun()  # Rerun the app to reset

if __name__ == "__main__":
    main()
