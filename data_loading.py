import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from io import StringIO
import time

base_url = "https://serval.uvm.edu/~rgweb/batch/enrollment/"
main_url = base_url + "enrollment_tab.html"

response = requests.get(main_url)
response.raise_for_status()

soup = BeautifulSoup(response.content, 'html.parser')

semester_links = []
for link in soup.find_all('a', href=True):
    link_text = link.get_text()
    href = link.get('href')
    
    if any(keyword in link_text.lower() for keyword in ['spring', 'fall', 'summer']):
        text = link_text.strip()
        
        semester = None
        if 'spring' in text.lower():
            semester = 'Spring'
        elif 'fall' in text.lower():
            semester = 'Fall'
        elif 'summer' in text.lower():
            semester = 'Summer'
        
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        year = year_match.group(0) if year_match else None
        
        if year and semester:
            if not href.startswith('http'):
                full_url = base_url + href
            else:
                full_url = href
            
            semester_links.append({
                'url': full_url,
                'year': year,
                'semester': semester,
                'text': link_text.strip()
            })

all_dataframes = []

for idx, link_info in enumerate(semester_links, 1):
    print(f"[{idx}/{len(semester_links)}] Processing {link_info['semester']} {link_info['year']}")
    
    response = requests.get(link_info['url'])
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    csv_link = None
    for link in soup.find_all('a'):
        link_text = link.get_text().lower()
        if 'comma delimited format' in link_text or 'comma-delimited format' in link_text:
            csv_link = link.get('href')
            break
    
    if not csv_link:
        raise Exception(f"No CSV link found on page: {link_info['url']}")
    
    if not csv_link.startswith('http'):
        csv_link = base_url + csv_link
    
    csv_response = requests.get(csv_link)
    csv_response.raise_for_status()
    
    df = pd.read_csv(StringIO(csv_response.text), on_bad_lines='skip', engine='python')
    
    df['Year'] = link_info['year']
    df['Semester'] = link_info['semester']
    
    all_dataframes.append(df)
    
    time.sleep(0.5) # appearently important to avoid overwhelming the server

combined_df = pd.concat(all_dataframes, ignore_index=True)

output_file = 'enrollment_data_combined.csv'
combined_df.to_csv(output_file, index=False)

print(f"\nSaved {len(combined_df)} rows to '{output_file}'")
