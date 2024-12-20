import streamlit as st
from ebooklib import epub
from bs4 import BeautifulSoup
import io  # Import io for BytesIO

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
            max-width: 800px;
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

    # File uploader allows users to select an EPUB file
    uploaded_file = st.file_uploader("Choose an EPUB file", type="epub")

    if uploaded_file is not None:
        # Read the bytes from the uploaded file
        file_bytes = uploaded_file.read()
        # Create a BytesIO object
        epub_file = io.BytesIO(file_bytes)
        # Load the EPUB file
        book = epub.read_epub(epub_file)

        # Initialize the chapter content
        chapter_paragraphs = []

        # You might want to allow the user to select a chapter here
        # For the example, we'll process the first chapter available
        for item in book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                # Parse the HTML content of the chapter
                soup = BeautifulSoup(item.get_body_content(), 'html.parser')
                # Use the get_processed_paragraphs function to get paragraphs
                chapter_paragraphs = get_processed_paragraphs(soup)
                break  # Stop after processing the first chapter

        if not chapter_paragraphs:
            st.error("No readable content found in the EPUB file.")
            return

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
        st.info("Please upload an EPUB file to begin reading.")

if __name__ == "__main__":
    main()
