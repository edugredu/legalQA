# %%
import re
from bs4 import BeautifulSoup
#from eurlex import get_data_by_celex_id #pip install eurlex-parser
from eurlex import get_html_by_celex_id #pip install eurlex
import requests
import pandas as pd
import urllib.parse

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
def get_html_by_celex_id_webservice(celex_id, username, password):
    """
    Retrieve EU law document using EUR-Lex web service.
    Handles special characters in CELEX IDs properly.
    """
    # Escape special characters for EUR-Lex query syntax
    escaped_celex_id = celex_id.replace('(', '\\(').replace(')', '\\)')
    
    soap_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap12:Envelope xmlns:soap12="http://www.w3.org/2003/05/soap-envelope" 
                 xmlns:sear="http://eur-lex.europa.eu/search"
                 xmlns:wsse="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
                 xmlns:wsu="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd">
  <soap12:Header>
    <wsse:Security soap12:mustUnderstand="true">
      <wsse:UsernameToken wsu:Id="UsernameToken-1">
        <wsse:Username>{username}</wsse:Username>
        <wsse:Password Type="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordText">{password}</wsse:Password>
      </wsse:UsernameToken>
    </wsse:Security>
  </soap12:Header>
  <soap12:Body>
    <sear:searchRequest>
      <sear:expertQuery>DN={escaped_celex_id}</sear:expertQuery>
      <sear:page>1</sear:page>
      <sear:pageSize>1</sear:pageSize>
      <sear:searchLanguage>en</sear:searchLanguage>
    </sear:searchRequest>
  </soap12:Body>
</soap12:Envelope>"""
    
    headers = {
        'Content-Type': 'application/soap+xml; charset=utf-8',
        'SOAPAction': 'https://eur-lex.europa.eu/EURLexWebService/doQuery'
    }
    
    response = requests.post(
        'https://eur-lex.europa.eu/EURLexWebService',
        data=soap_body,
        headers=headers,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.text}")
        raise Exception(f"SOAP request failed: {response.status_code}")
    
    return parse_search_results(response.text)

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
#Load to a dataframe the lawsToBeConsidered.csv
df = pd.read_csv('lawsToBeConsidered.csv', encoding='utf-8')

# %%
for i, row in df.iterrows():
    #Get the CELEX ID
    celex_id = row['celex_id']


    #If the CELEX ID contains (), remove it. For example, '32023R1234(1)' should become '32023R1234'
    #celex_id = re.sub(r'\(\d+\)$', '', celex_id)

    encoded_celex_id = url_encode_celex_id(celex_id)
    
    print("Looking for CELEX ID:", celex_id)

    #Get the HTML content
    html = get_html_by_celex_id(encoded_celex_id)

    # Extract structured text
    structured_text = extract_eu_law_text(html)

    # Append the structured text to the DataFrame
    df.at[i, 'structured_text'] = structured_text

# %%
#Export the dataframe to a CSV file
df.to_csv('lawsWithText.csv', index=False)


