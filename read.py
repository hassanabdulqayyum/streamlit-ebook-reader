import streamlit as st
import ebooklib  # Import the ebooklib module
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

def display_paragraphs(paragraph_index, processed_paragraphs, mode):
    """
    Displays three paragraphs at a time with mode-adjusted styling.
    """
    # Define styles based on the mode
    if mode == 'Light Mode':
        font_style = """
            font-family: Georgia, serif;
            font-weight: 400;
            font-size: 20px;
            color: #333333;
            line-height: 1.6;
            max-width: 1000px;
            margin: 40px auto;
            padding: 15px;
            border: 1px solid #ddd;
            background-color: #f7f7f7;
        """
        highlighted_style = """
            background-color: {color};
            padding: 2px 5px;
            border-radius: 5px;
        """
        colors = ["#ffd54f", "#aed581", "#64b5f6", "#f06292", "#ba68c8"]
    else:  # Dark Mode
        font_style = """
            font-family: Georgia, serif;
            font-weight: 400;
            font-size: 20px;
            color: #f0f0f0;
            line-height: 1.6;
            max-width: 1000px;
            margin: 40px auto;
            padding: 15px;
            border: 1px solid #444;
            background-color: #1e1e1e;
        """
        highlighted_style = """
            background-color: {color};
            padding: 2px 5px;
            border-radius: 5px;
        """
        colors = ["#ffa500", "#90ee90", "#1e90ff", "#ff69b4", "#9370db"]
    
    # Extract the paragraphs to display
    display_paragraphs = processed_paragraphs[max(paragraph_index - 1, 0):paragraph_index + 2]
    
    html_content = ""

    for i, paragraph_html in enumerate(display_paragraphs):
        # Parse the paragraph HTML
        soup = BeautifulSoup(paragraph_html, 'html.parser')
        
        # Get the text content
        paragraph_text = ''
        for content in soup.contents:
            if content.name == 'p':
                paragraph_text += content.get_text(separator=' ') + ' '
            else:
                paragraph_text += str(content) + ' '
        
        # Determine if this paragraph is highlighted
        is_highlighted = (paragraph_index == 0 and i == 0) or (paragraph_index != 0 and i == 1)
        
        if is_highlighted:
            sentences = paragraph_text.strip().split('. ')
            highlighted_sentence = [
                f'<span style="{highlighted_style.format(color=get_color(j, colors))}">{sentence.strip()}{"." if not sentence.strip().endswith(".") else ""}</span>'
                for j, sentence in enumerate(sentences)
            ]
            paragraph_content = ' '.join(highlighted_sentence)
            html_content += f"<div style='{font_style}'>{paragraph_content}</div>"
        else:
            html_content += f"<div style='{font_style}'>{paragraph_text}</div>"
    
    # Display the content
    st.write(html_content, unsafe_allow_html=True)

def main():
    st.title("EPUB Reader")

    # Move file uploader to sidebar
    uploaded_file = st.sidebar.file_uploader("Choose an EPUB file", type="epub")

    # Add mode selector in the sidebar
    mode = st.sidebar.selectbox('Display Mode', ['Light Mode', 'Dark Mode'])

    if uploaded_file is not None:
        # [Code for handling the EPUB file remains the same]

        if chapters:
            # Move chapter selector to sidebar
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]

            # [Code to process the chapter remains the same]

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
                    if st.session_state.current_paragraph + 1 < len(chapter_paragraphs):
                        st.session_state.current_paragraph += 1

            # Display the paragraphs with the selected mode
            display_paragraphs(st.session_state.current_paragraph, chapter_paragraphs, mode)
        else:
            st.error("No readable content found in the EPUB file.")
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
