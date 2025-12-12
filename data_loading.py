import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from io import StringIO
import time
import matplotlib.pyplot as plt
import seaborn as sns
import os


if os.path.exists("enrollment_data_combined.csv"):
    print("Combined enrollment data file already exists. Skipping download.")
    combined_df = pd.read_csv("enrollment_data_combined.csv", dtype=str)
else:
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
    all_dataframes_cols = []
    semester_info = []

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

        df = pd.read_csv(StringIO(csv_response.text), dtype=str, on_bad_lines='skip')

        df.columns = df.columns.str.strip()
        all_dataframes_cols.append(df.columns.tolist())
        semester_info.append({'Year': link_info['year'], 'Semester': link_info['semester']})

        # Standardize column names
        column_mapping = {
            'Dept': 'Subject',
            'Subj': 'Subject',
        }
        df = df.rename(columns=column_mapping)

        # Handle instructor name variations
        if 'Instructor First' in df.columns and 'Instructor Last' in df.columns and 'Instructor' not in df.columns:
            # Combine into single Instructor column for consistency
            df['Instructor'] = df['Instructor Last'].fillna('') + ', ' + df['Instructor First'].fillna('')
            df['Instructor'] = df['Instructor'].str.strip(', ')
            df.drop(columns=['Instructor First', 'Instructor Last'], inplace=True)

        df['Year'] = link_info['year']
        df['Semester'] = link_info['semester']

        all_dataframes.append(df)

        time.sleep(0.5) # appearently important to avoid overwhelming the server

    combined_df = pd.concat(all_dataframes, ignore_index=True)

    # Split instructor column into first and last name (for rows that have combined format)
    if 'Instructor' in combined_df.columns:
        instructor_split = combined_df['Instructor'].str.split(',', n=1, expand=True)
        combined_df['Instructor Last'] = instructor_split[0].str.strip() if 0 in instructor_split.columns else None
        combined_df['Instructor First'] = instructor_split[1].str.strip() if 1 in instructor_split.columns else None

    output_file = 'enrollment_data_combined.csv'
    combined_df.to_csv(output_file, index=False)

    print(f"\nSaved {len(combined_df)} rows to '{output_file}'")

    # Create dataframe of column headers for each semester
    max_cols = max(len(cols) for cols in all_dataframes_cols)
    cols_data = []
    for idx, cols in enumerate(all_dataframes_cols):
        row = list(cols) + [None] * (max_cols - len(cols))
        cols_data.append(row)

    cols_df = pd.DataFrame(cols_data, columns=[f'Col_{i}' for i in range(max_cols)])
    cols_df.insert(0, 'Year', [info['Year'] for info in semester_info])
    cols_df.insert(1, 'Semester', [info['Semester'] for info in semester_info])
    cols_df.to_csv('semester_columns.csv', index=False)
    print(f"\nSaved column headers to 'semester_columns.csv'")

print(f"\nNull counts per column:")
print(combined_df.isnull().sum())

plt.figure(figsize=(12, 8))
sns.heatmap(combined_df.isnull(), cbar=True, yticklabels=False, cmap='Blues')
plt.title('Null Values Heatmap')
plt.xlabel('Columns')
plt.ylabel('Rows')
plt.tight_layout()
plt.savefig('null_values_heatmap.png', dpi=300)
print(f"\nSaved null values heatmap to 'null_values_heatmap.png'")
plt.close()  # Close the figure instead of showing it