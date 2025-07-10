# %%
import re
from bs4 import BeautifulSoup
#from eurlex import get_data_by_celex_id #pip install eurlex-parser
#from eurlex import get_html_by_celex_id #pip install eurlex
import requests
import pandas as pd
import urllib.parse
import json
from tqdm import tqdm
import ast
import os

# %%
def get_html_by_celex_id(celex_id: str) -> str:
    """Retrieve HTML by CELEX ID.

    Parameters
    ----------
    celex_id : str
        The CELEX ID to find HTML for.

    Returns
    -------
    str
        HTML found using the CELEX ID.
    """
    url = "http://publications.europa.eu/resource/celex/" + str(
        celex_id
    )  # pragma: no cover
    response = requests.get(
        url,
        allow_redirects=True,
        headers={  # pragma: no cover
            "Accept": "text/html,application/xhtml+xml,application/xml",  # pragma: no cover
            "Accept-Language": "en",  # pragma: no cover
        },
    )  # pragma: no cover
    html = response.content.decode("utf-8")  # pragma: no cover
    return html  # pragma: no cover

# %%
#URL encode the celex_id
def url_encode_celex_id(celex_id):
    """
    URL encode the CELEX ID to ensure it is safe for web requests.
    
    Args:
        celex_id (str): The CELEX ID to encode
        
    Returns:
        str: URL encoded CELEX ID
    """
    return urllib.parse.quote(celex_id, safe='')

# %%
def parse_search_results(soap_response):
    """Parse the SOAP response to extract search results"""
    import xml.etree.ElementTree as ET
    
    try:
        root = ET.fromstring(soap_response)
        
        # Define namespaces
        namespaces = {
            'soap12': 'http://www.w3.org/2003/05/soap-envelope',
            'elx': 'http://eur-lex.europa.eu/search'
        }
        
        # Find search results
        search_results = root.find('.//elx:searchResults', namespaces)
        
        if search_results is not None:
            # Extract document information
            documents = search_results.findall('.//elx:document', namespaces)
            return documents
        else:
            raise Exception("No search results found in response")
            
    except ET.ParseError as e:
        raise Exception(f"Failed to parse SOAP response: {e}")

def extract_eu_law_text(html_content):
    """
    Extract clean, structured text from EU legal document HTML.
    
    Args:
        html_content (str): Raw HTML content of the EU law document
        
    Returns:
        str: Clean, structured text with titles, articles, and appendices
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'link', 'meta', 'hr']):
        element.decompose()
    
    extracted_text = []
    
    # Extract document header information
    header_info = extract_header_info(soup)
    if header_info:
        extracted_text.append(header_info)
    
    # Extract main title and regulation info
    main_title = extract_main_title(soup)
    if main_title:
        extracted_text.append(main_title)
    
    # Extract preamble/whereas clauses
    preamble = extract_preamble(soup)
    if preamble:
        extracted_text.append(preamble)
    
    # Extract main articles
    articles = extract_articles(soup)
    if articles:
        extracted_text.append(articles)
    
    # Extract annexes
    annexes = extract_annexes(soup)
    if annexes:
        extracted_text.append(annexes)
    
    # Extract appendices
    appendices = extract_appendices(soup)
    if appendices:
        extracted_text.append(appendices)
    
    return '\n\n'.join(filter(None, extracted_text))

def extract_header_info(soup):
    """Extract document header with date and publication info"""
    header_text = []
    
    # Extract date and language info
    header_table = soup.find('table', width="100%")
    if header_table:
        for row in header_table.find_all('tr'):
            cells = row.find_all('td')
            if cells:
                row_text = ' | '.join(cell.get_text(strip=True) for cell in cells if cell.get_text(strip=True))
                if row_text:
                    header_text.append(row_text)
    
    return '\n'.join(header_text) if header_text else None

def extract_main_title(soup):
    """Extract the main regulation title and basic info"""
    title_text = []
    
    # Main title
    main_title = soup.find(class_='eli-main-title')
    if main_title:
        for p in main_title.find_all('p'):
            text = p.get_text(strip=True)
            if text:
                title_text.append(text)
    
    return '\n'.join(title_text) if title_text else None

def extract_preamble(soup):
    """Extract the preamble including 'Whereas' clauses"""
    preamble_text = []
    
    # Look for preamble section
    preamble_section = soup.find('div', id='pbl_1')
    if preamble_section:
        preamble_text.append("PREAMBLE")
        
        # Extract "THE EUROPEAN COMMISSION" and "Having regard to" sections
        for p in preamble_section.find_all('p', class_='oj-normal', recursive=False):
            text = p.get_text(strip=True)
            if text:
                preamble_text.append(text)
        
        # Extract "Whereas" clauses (recitals)
        whereas_clauses = preamble_section.find_all('div', id=re.compile(r'rct_\d+'))
        if whereas_clauses:
            preamble_text.append("\nWHEREAS:")
            for clause in whereas_clauses:
                table = clause.find('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 2:
                            number = cells[0].get_text(strip=True)
                            content = cells[1].get_text(strip=True)
                            if number and content:
                                preamble_text.append(f"({number}) {content}")
    
    return '\n\n'.join(preamble_text) if preamble_text else None

def extract_articles(soup):
    """Extract all articles with their content"""
    articles_text = []
    
    # Find all article divisions
    articles = soup.find_all('div', id=re.compile(r'art_\d+'))
    
    for article in articles:
        article_content = []
        
        # Article title
        article_title = article.find(class_='oj-ti-art')
        if article_title:
            article_content.append(article_title.get_text(strip=True))
        
        # Article subtitle
        article_subtitle = article.find(class_='oj-sti-art')
        if article_subtitle:
            article_content.append(article_subtitle.get_text(strip=True))
        
        # Article paragraphs
        paragraphs = extract_article_paragraphs(article)
        if paragraphs:
            article_content.extend(paragraphs)
        
        if article_content:
            articles_text.append('\n'.join(article_content))
    
    return '\n\n'.join(articles_text) if articles_text else None

def extract_article_paragraphs(article):
    """Extract paragraphs and structured content from an article"""
    paragraphs = []
    
    # Direct paragraphs
    for p in article.find_all('p', class_='oj-normal'):
        text = p.get_text(strip=True)
        if text and not text.startswith('(') and ')' not in text[:5]:
            paragraphs.append(text)
    
    # Numbered paragraphs in tables
    for table in article.find_all('table'):
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                number = cells[0].get_text(strip=True)
                content = cells[1].get_text(strip=True)
                if number and content and re.match(r'\([a-z0-9]+\)', number):
                    paragraphs.append(f"{number} {content}")
    
    # Numbered divisions within article
    for div in article.find_all('div', id=re.compile(r'\d{3}\.\d{3}')):
        div_paragraphs = div.find_all('p', class_='oj-normal')
        for p in div_paragraphs:
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)
        
        # Tables within divisions
        for table in div.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    number = cells[0].get_text(strip=True)
                    content = cells[1].get_text(strip=True)
                    if number and content:
                        paragraphs.append(f"{number} {content}")
    
    return paragraphs

def extract_annexes(soup):
    """Extract annex content"""
    annex_text = []
    
    # Find annex container
    annex = soup.find('div', id='anx_1')
    if annex:
        # Annex title
        annex_title = annex.find('p', class_='oj-doc-ti')
        if annex_title:
            annex_text.append(f"ANNEX\n{annex_title.get_text(strip=True)}")
        
        # Extract all sections within annex
        sections = extract_annex_sections(annex)
        if sections:
            annex_text.extend(sections)
    
    return '\n\n'.join(annex_text) if annex_text else None

def extract_annex_sections(annex):
    """Extract sections from annex (Parts A, B, C, etc.)"""
    sections = []
    
    # Find all part titles and UAS sections
    part_titles = annex.find_all('p', class_='oj-ti-grseq-1')
    
    current_section = []
    
    for element in annex.find_all(['p', 'table']):
        if element.name == 'p':
            text = element.get_text(strip=True)
            if text:
                # Check if it's a section title
                if 'PART' in text or 'UAS.' in text:
                    if current_section:
                        sections.append('\n'.join(current_section))
                        current_section = []
                    current_section.append(text)
                else:
                    current_section.append(text)
        
        elif element.name == 'table':
            # Extract table content
            rows = element.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    number = cells[0].get_text(strip=True)
                    content = cells[1].get_text(strip=True)
                    if number and content:
                        current_section.append(f"{number} {content}")
    
    # Add the last section
    if current_section:
        sections.append('\n'.join(current_section))
    
    return sections

def extract_appendices(soup):
    """Extract appendix content"""
    appendix_text = []
    
    # Find appendix
    appendix = soup.find('div', id='anx_1.app_1')
    if appendix:
        appendix_title = appendix.find('p', class_='oj-doc-ti')
        if appendix_title:
            appendix_text.append(f"APPENDIX\n{appendix_title.get_text(strip=True)}")
        
        # Extract appendix content
        for p in appendix.find_all('p'):
            text = p.get_text(strip=True)
            if text and text not in appendix_text:
                appendix_text.append(text)
    
    return '\n\n'.join(appendix_text) if appendix_text else None

# %%
def extract_articles_json(soup):
    """Extract all articles as a list of dictionaries with full text in a single property"""
    articles_list = []
    
    # Find all article divisions
    articles = soup.find_all('div', id=re.compile(r'art_\d+'))
    
    for article in articles:
        article_data = {}
        
        # Extract article ID from the div id
        article_id = article.get('id', '').replace('art_', '')
        if article_id:
            article_data['id'] = article_id
        
        # Article title
        article_title = article.find(class_='oj-ti-art')
        if article_title:
            article_data['title'] = article_title.get_text(strip=True)
        
        # Article subtitle
        article_subtitle = article.find(class_='oj-sti-art')
        if article_subtitle:
            article_data['subtitle'] = article_subtitle.get_text(strip=True)
        
        # Get full text content of the article div
        full_text = article.get_text(separator='\n', strip=True)
        article_data['text'] = full_text
        
        articles_list.append(article_data)
    
    return articles_list if articles_list else None

def extract_annexes_json(soup):
    """Extract annex content as structured data with full text in a single property"""
    annexes_list = []
    
    # Find annex container
    annex = soup.find('div', id='anx_1')
    if annex:
        annex_data = {
            "id": "anx_1",
            "type": "annex"
        }
        
        # Annex title
        annex_title = annex.find('p', class_='oj-doc-ti')
        if annex_title:
            annex_data['title'] = annex_title.get_text(strip=True)
        
        # Get full text content of the annex div
        full_text = annex.get_text(separator='\n', strip=True)
        annex_data['text'] = full_text
        
        annexes_list.append(annex_data)
    
    return annexes_list if annexes_list else None

def extract_appendices_json(soup):
    """Extract appendix content as structured data with full text in a single property"""
    appendices_list = []
    
    # Find appendix
    appendix = soup.find('div', id='anx_1.app_1')
    if appendix:
        appendix_data = {
            "id": "anx_1.app_1",
            "type": "appendix"
        }
        
        appendix_title = appendix.find('p', class_='oj-doc-ti')
        if appendix_title:
            appendix_data['title'] = appendix_title.get_text(strip=True)
        
        # Get full text content of the appendix div
        full_text = appendix.get_text(separator='\n', strip=True)
        appendix_data['text'] = full_text
        
        appendices_list.append(appendix_data)
    
    return appendices_list if appendices_list else None

# %%
def parse_legacy_format(soup, texte_only_div):
    """
    Parse the older EUR-Lex HTML format found in TexteOnly div.
    """
    # Extract title from outside TexteOnly div
    title_element = soup.find('h1')
    title = title_element.get_text(strip=True) if title_element else None
    
    # Extract the main regulation title
    strong_element = soup.find('strong')
    regulation_title = strong_element.get_text(strip=True) if strong_element else None
    
    # Get all paragraphs within TexteOnly
    paragraphs = texte_only_div.find_all('p')
    
    # Parse the content
    articles = []
    annexes = []
    current_article = None
    current_annex = None
    
    for p in paragraphs:
        text = p.get_text(strip=True)
        
        if not text:
            continue
            
        # Check if this is an article
        if text.startswith('Article '):
            # Save previous article if exists
            if current_article:
                articles.append(current_article)
            
            # Extract article number
            article_match = re.match(r'Article (\d+)', text)
            if article_match:
                current_article = {
                    "id": article_match.group(1),
                    "title": text,
                    "text": text
                }
            current_annex = None
            
        # Check if this is an annex
        elif text.startswith('ANNEX '):
            # Save previous article if exists
            if current_article:
                articles.append(current_article)
                current_article = None
            
            # Save previous annex if exists
            if current_annex:
                annexes.append(current_annex)
            
            # Extract annex identifier
            annex_match = re.match(r'ANNEX ([IVX]+)', text)
            if annex_match:
                current_annex = {
                    "id": f"anx_{annex_match.group(1)}",
                    "type": "annex",
                    "title": text,
                    "text": text
                }
            
        # Add content to current article or annex
        elif current_article:
            current_article["text"] += "\n\n" + text
        elif current_annex:
            current_annex["text"] += "\n\n" + text
    
    # Don't forget the last article/annex
    if current_article:
        articles.append(current_article)
    if current_annex:
        annexes.append(current_annex)
    
    # Build the document structure
    document_data = {
        "title": regulation_title or title,
        "articles": articles if articles else None,
        "annexes": annexes if annexes else None
    }
    
    return document_data

def parse_legacy_format_enhanced(soup, texte_only_div):
    """
    Enhanced parser for older EUR-Lex HTML format with better content detection.
    """
    # Extract metadata
    title_element = soup.find('h1')
    title = title_element.get_text(strip=True) if title_element else None
    
    strong_element = soup.find('strong')
    regulation_title = strong_element.get_text(strip=True) if strong_element else None
    
    # Get full text content and split into logical sections
    full_text = texte_only_div.get_text(separator='\n', strip=True)
    
    # Split by known patterns
    articles = []
    annexes = []
    
    # Find all article sections
    article_pattern = r'Article (\d+)\s*\n(.*?)(?=Article \d+|ANNEX|$)'
    article_matches = re.findall(article_pattern, full_text, re.DOTALL)
    
    for article_num, article_content in article_matches:
        articles.append({
            "id": article_num,
            "title": f"Article {article_num}",
            "text": f"Article {article_num}\n\n{article_content.strip()}"
        })
    
    # Find all annex sections
    annex_pattern = r'ANNEX ([IVX]+)\s*\n(.*?)(?=ANNEX [IVX]+|$)'
    annex_matches = re.findall(annex_pattern, full_text, re.DOTALL)
    
    for annex_num, annex_content in annex_matches:
        annexes.append({
            "id": f"anx_{annex_num}",
            "type": "annex",
            "title": f"ANNEX {annex_num}",
            "text": f"ANNEX {annex_num}\n\n{annex_content.strip()}"
        })
    
    # Build the document structure
    document_data = {
        "title": regulation_title or title,
        "articles": articles if articles else None,
        "annexes": annexes if annexes else None
    }
    
    return document_data

def extract_eu_law_text_json(html_content):
    """
    Extract clean, structured data from EU legal document HTML.
    Handles both modern and legacy HTML formats.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove unwanted elements
    for element in soup(['script', 'style', 'link', 'meta', 'hr']):
        element.decompose()
    
    # Check if this is the modern format or legacy format
    modern_articles = soup.find_all('div', id=re.compile(r'art_\d+'))
    texte_only_div = soup.find('div', id='TexteOnly')
    
    if modern_articles or not texte_only_div:
        # Use modern parsing
        document_data = {
            "header": extract_header_info(soup),
            "title": extract_main_title(soup),
            "preamble": extract_preamble(soup),
            "articles": extract_articles_json(soup),
            "annexes": extract_annexes_json(soup),
            "appendices": extract_appendices_json(soup)
        }
    else:
        # Use legacy parsing for older HTML format
        document_data = parse_legacy_format(soup, texte_only_div)
    
    # Remove None values
    return {k: v for k, v in document_data.items() if v is not None}

# %%
def load_cache():

    #Read all the cached laws CSV files from the data directory
    cacheFiles = os.listdir('data')
    cacheFiles = [f for f in cacheFiles if f.startswith('cachedLawsTexts_') and f.endswith('.csv')]
    cacheFiles.sort()  # Sort to ensure consistent order

    # Read the cached laws CSV files into dataframes
    df_cache = pd.DataFrame()
    for cache_file in cacheFiles:
        file_path = os.path.join('data', cache_file)
        df_temp = pd.read_csv(file_path, encoding='utf-8')
        df_cache = pd.concat([df_cache, df_temp], ignore_index=True)

    return df_cache

# %%
def getFullText(dfToGet, dfCache):

    for i, row in dfToGet.iterrows():
        #Get the CELEX ID
        celex_id = row['celex_id']

        # If the CELEX ID is not in the cache
        if row['structured_json'] is None or \
        dfCache[dfCache['celex_id'] == celex_id].empty or \
        dfCache[dfCache['celex_id'] == celex_id]['structured_json'].isnull().all() or \
        dfCache[dfCache['celex_id'] == celex_id]['structured_json'].isna().all() or \
        dfCache[dfCache['celex_id'] == celex_id]['structured_json'].apply(lambda x: x == {}).all():
                        
            encoded_celex_id = url_encode_celex_id(celex_id)
            
            # Get the HTML content
            html = get_html_by_celex_id(encoded_celex_id)
            
            # Extract structured JSON
            structured_json = extract_eu_law_text_json(html)
            
            # Store JSON
            dfToGet.at[i, 'structured_json'] = structured_json
        else:
            try:
                cacheJson = dfCache[dfCache['celex_id'] == celex_id]['structured_json'].values[0]

                #Convert it to a JSON object
                if isinstance(cacheJson, str):
                    json_data = ast.literal_eval(cacheJson)
                    dfToGet.at[i, 'structured_json'] = json_data

                else:
                    # If it's already a JSON object, just assign it
                    dfToGet.at[i, 'structured_json'] = cacheJson

            except:
                print("Exception parsing JSON for CELEX ID:", celex_id, " in row:", i)
                dfToGet.at[i, 'structured_json'] = None
                

    return dfToGet


def clean_articles(structured_json):
    if structured_json is not None and 'articles' in structured_json:
        filtered_articles = []
        for article in structured_json['articles']:
            # Ensure ID exists and convert to string for dot checking
            if 'id' not in article:
                print("Skipping article without ID")
                continue
                
            article_id = str(article['id'])
            
            # Skip articles with dots in ID
            if '.' in article_id:
                continue
                
            # Skip articles where subtitle equals text
            if ('subtitle' in article and 'text' in article and 
                article['subtitle'] == article['text']):
                continue
                
            filtered_articles.append(article)
        
        structured_json['articles'] = filtered_articles
    return structured_json

# %%
def mod3_response(lawsToConsider):
    # Add this column to store JSON data
    lawsToConsider['structured_json'] = None

    #Remove erovoc_concepts
    lawsToConsider = lawsToConsider.drop(columns=['eurovoc_concepts'], errors='ignore')

    df_cache = load_cache()
    print("Running module 3: API Law")

    dfFullText = getFullText(lawsToConsider, df_cache)

    dfFullText['structured_json'] = dfFullText['structured_json'].apply(clean_articles)

    return dfFullText