import streamlit as st
import ebooklib
from ebooklib import epub
import bs4
from bs4 import BeautifulSoup
import tempfile
import os
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt')
import re
from io import BytesIO

def main():
    # Inject CSS styles
    st.markdown("""
    <style>
    :root {
        /* Define color variables */
        --color-1: #d32f2f;
        --color-2: #1976d2;
        --color-3: #388e3c;
        --color-4: #512da8;
        --color-5: rgba(251, 192, 45, 0.9);
    }

    /* Hide the Streamlit style elements */
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
    
    st.title("EPUB Reader")
    
    uploaded_file = st.sidebar.file_uploader("Choose an EPUB file", type="epub")
    
    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_file_path = tmp_file.name
        
        try:
            book = epub.read_epub(tmp_file_path)
        except Exception as e:
            st.error(f"An error occurred while reading the EPUB file: {e}")
            return
        finally:
            os.remove(tmp_file_path)
        
        # Build chapters and chapter_titles lists
        chapters = []
        chapter_titles = []
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                chapters.append(item)
                # Use the title from the item metadata if available
                title = item.get_name()
                chapter_titles.append(title)
        
        if chapters:
            # Image items mapping
            image_items = {}
            for item in book.get_items():
                if item.get_type() == ebooklib.ITEM_IMAGE:
                    image_items[item.get_name()] = item  # Use get_name() which returns the path/href
            
            # Chapter selector
            selected_chapter = st.sidebar.selectbox("Select a chapter", chapter_titles)
            chapter_index = chapter_titles.index(selected_chapter)
            selected_item = chapters[chapter_index]
            
            # Parse content
            elements_list, para_positions = parse_chapter_content(selected_item.get_content())
            
            if 'current_para_idx' not in st.session_state:
                st.session_state.current_para_idx = 0
            
            # Navigation buttons
            col1, col2, col3 = st.columns([1,1,1])
            with col1:
                if st.button("Previous"):
                    if st.session_state.current_para_idx > 0:
                        st.session_state.current_para_idx -=1
            with col3:
                if st.button("Next"):
                    if st.session_state.current_para_idx +1 < len(para_positions):
                        st.session_state.current_para_idx +=1
            
            # Display content
            display_content(st.session_state.current_para_idx, elements_list, para_positions, image_items)
        else:
            st.error("No readable content found in the EPUB file.")
    else:
        st.info("Please upload an EPUB file to begin reading.")

def parse_chapter_content(chapter_content):
    elements = []
    para_positions = []
    soup = BeautifulSoup(chapter_content, 'html.parser')

    body = soup.body or soup

    para_counter = 0
    def process_elements(element):
        for child in element.children:
            if isinstance(child, bs4.element.Tag):
                if child.name in ['script', 'style']:
                    continue
                elif child.name in ['h1','h2','h3','h4','h5','h6']:
                    elements.append({'type': 'heading', 'content': child.get_text(strip=True)})
                elif child.name == 'p':
                    elements.append({'type': 'paragraph', 'content': child.get_text(), 'para_idx': para_counter})
                    para_positions.append(len(elements) -1)
                    para_counter +=1
                elif child.name == 'img':
                    src = child.get('src')
                    elements.append({'type': 'image', 'src': src})
                elif child.name == 'figcaption':
                    elements.append({'type': 'caption', 'content': child.get_text()})
                else:
                    process_elements(child)
            elif isinstance(child, bs4.element.NavigableString):
                text = str(child).strip()
                if text:
                    elements.append({'type': 'text', 'content': text})
    process_elements(body)
    return elements, para_positions

def display_content(current_para_idx, elements_list, para_positions, image_items):
    num_paragraphs = len(para_positions)
    start_para_idx = max(0, current_para_idx -1)
    end_para_idx = min(num_paragraphs -1, current_para_idx +1)
    
    # Positions in elements_list
    start_pos = para_positions[start_para_idx]
    if end_para_idx +1 < len(para_positions):
        end_pos = para_positions[end_para_idx +1]
    else:
        end_pos = len(elements_list)
    
    display_elements = elements_list[start_pos:end_pos]
    
    for elem in display_elements:
        elem_type = elem['type']
        content = elem.get('content', '')
        if elem_type == 'heading':
            st.markdown(f"### {content}")
        elif elem_type == 'paragraph':
            is_current_para = (elem.get('para_idx') == current_para_idx)
            if is_current_para:
                display_highlighted_paragraph(content)
            else:
                st.write(content)
        elif elem_type == 'image':
            src = elem.get('src')
            image_data = get_image_data(src, image_items)
            if image_data:
                image = BytesIO(image_data)
                st.image(image)
            else:
                st.write(f"Image not found: {src}")
        elif elem_type == 'caption':
            st.write(f"*{content}*")
        elif elem_type == 'text':
            st.write(content)

def display_highlighted_paragraph(paragraph_text):
    # Remove references
    clean_text = re.sub(r'\[.*?\]', '', paragraph_text)
    sentences = sent_tokenize(clean_text)
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
        sentence_html = f'<span style="{highlighted_style}">{sentence.strip()}</span>'
        highlighted_sentences.append(sentence_html)
    paragraph_content = ' '.join(highlighted_sentences)
    st.markdown(paragraph_content, unsafe_allow_html=True)

def get_image_data(src, image_items):
    # Try to resolve the src
    if src in image_items:
        image_item = image_items[src]
        return image_item.get_content()
    else:
        # Try to adjust the src
        # Remove leading './' or '/'
        src_key = src.lstrip('./').lstrip('/')
        if src_key in image_items:
            image_item = image_items[src_key]
            return image_item.get_content()
        else:
            # Try other methods as needed
            return None

if __name__ == "__main__":
    main()
