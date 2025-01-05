import requests
from bs4 import BeautifulSoup
import os
import time
from ebooklib import epub
import subprocess
from tqdm import tqdm

class NovelCrawler:
    def __init__(self, base_url, start_chapter, end_chapter, chapters_per_file=10):
        self.base_url = base_url
        self.start_chapter = start_chapter
        self.end_chapter = end_chapter
        self.chapters_per_file = chapters_per_file
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_chapter_content(self, chapter_num, max_retries=3):
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/chuong-{chapter_num}.html"
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Get title
                title = f"Chương {chapter_num}: {soup.find('h2', class_='heading-font mt-2').text.strip()}"
                
                # Get content and preserve <br> tags
                content_div = soup.find('div', id='inner_chap_content_1')
                
                # Replace <br> tags with newlines before getting text
                for br in content_div.find_all('br'):
                    br.replace_with('\n\n')  # Double newline for better spacing
                
                # Handle paragraph tags
                for p in content_div.find_all('p'):
                    p.insert_after(soup.new_string('\n\n'))
                
                content = content_div.get_text()
                # Clean up multiple newlines
                content = '\n'.join(line.strip() for line in content.splitlines() if line.strip())
                
                time.sleep(2)  # Be nice to the server
                
                return {
                    'title': title,
                    'content': content,
                    'chapter_num': chapter_num
                }
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to fetch chapter {chapter_num} after {max_retries} attempts: {str(e)}")
                    return None
                print(f"Attempt {attempt + 1} failed for chapter {chapter_num}. Retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
                continue

    def create_epub(self, chapters, book_num):
        book = epub.EpubBook()
        
        # Set metadata
        book.set_identifier(f'novel{book_num}')
        book.set_title(f'Bắt Đầu Mười Liên Rút Sau Đó Vô Địch - Tập {book_num}')
        book.set_language('vi')
        
        # Create chapters
        epub_chapters = []
        toc = []
        
        for chapter in chapters:
            if chapter:
                # Convert newlines to HTML paragraphs
                content_html = ''.join([f'<p>{para}</p>' for para in chapter['content'].split('\n') if para.strip()])
                
                c = epub.EpubHtml(
                    title=chapter['title'],
                    file_name=f'chap_{chapter["chapter_num"]}.xhtml',
                    content=f'<h1>{chapter["title"]}</h1><div>{content_html}</div>'
                )
                book.add_item(c)
                epub_chapters.append(c)
                toc.append(c)

        # Add default NCX and Nav file
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define Table of Contents
        book.toc = toc

        # Add chapters to book spine
        book.spine = ['nav'] + epub_chapters

        # Create output directory if it doesn't exist
        os.makedirs('output', exist_ok=True)
        
        # Save epub
        epub_path = f'output/bat-dau-muoi-lien-rut-sau-do-vo-dich-{book_num}.epub'
        epub.write_epub(epub_path, book)
        

    def crawl_and_convert(self):
        current_chapters = []
        book_num = 1
        
        for chapter_num in tqdm(range(self.start_chapter, self.end_chapter + 1)):
            chapter = self.get_chapter_content(chapter_num)
            if chapter:
                current_chapters.append(chapter)
                
                # When we have enough chapters, create a new MOBI file
                if len(current_chapters) >= self.chapters_per_file:
                    self.create_epub(current_chapters, book_num)
                    current_chapters = []
                    book_num += 1
        
        # Create final MOBI file with remaining chapters
        if current_chapters:
            self.create_epub(current_chapters, book_num)

def main():
    base_url = "https://truyenyy.app/truyen/bat-dau-muoi-lien-rut-sau-do-vo-dich"
    start_chapter = 1
    end_chapter = 499
    chapters_per_file = 500
    #sau này crawl lại từ 1-500, từ 2000-2515
    crawler = NovelCrawler(base_url, start_chapter, end_chapter, chapters_per_file)
    crawler.crawl_and_convert()

if __name__ == "__main__":
    main()