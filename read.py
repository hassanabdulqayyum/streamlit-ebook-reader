import streamlit as st
import ebooklib  # Import the ebooklib module
from ebooklib import epub
from bs4 import BeautifulSoup
import tempfile
import os

def get_theme_colors():
    theme_mode = st.get_option('theme.base')
    # Use the same light colors for both themes
    colors = ["#ffd54f", "#aed581", "#64b5f6", "#f06292", "#b39ddb"]
    return colors

def hex_to_rgba(hex_color, opacity=1):
    hex_color = hex_color.lstrip('#')
    lv = len(hex_color)
    rgb = tuple(int(hex_color[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})'

def get_color(index):
    colors = get_theme_colors()
    hex_color = colors[index % len(colors)]
    theme_mode = st.get_option('theme.base')
    opacity = 0.2 if theme_mode == 'dark' else 1  # Set lower opacity in dark mode
    rgba_color = hex_to_rgba(hex_color, opacity)
    return rgba_color

def get_processed_paragraphs(soup):
    # Existing function code remains the same
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
    
    # Handle any remaining temp_content
    if temp_content:
        if processed_paragraphs:
            processed_paragraphs[-1] += '\n' + temp_content
        else:
            processed_paragraphs.append(temp_content)
    
    return processed_paragraphs

def display_paragraphs(paragraph_index, processed_paragraphs):
    # Extract the three paragraphs to be displayed
    display_paragraphs = processed_paragraphs[max(paragraph_index-1, 0):paragraph_index+2]
    
    html_content = ""
    
    for i, paragraph_html in enumerate(display_paragraphs):
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
               background-color: var(--background-color);
               transition: text-shadow 0.5s;
        """
        highlighted_style = """
            background-color: {color};
            padding: 0 2px;
            border-radius: 3px;
            color: var(--text-color);
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
            # Use the get_processed_paragraphs function to get paragraphs
            chapter_paragraphs = get_processed_paragraphs(soup)

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

            # Display the paragraphs
            display_paragraphs(st.session_state.current_paragraph, chapter_paragraphs)
        else:
            st.error("No readable content found in the EPUB file.")
            return
    else:
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
