import requests
import pandas as pd
from urllib.parse import urljoin
import os
from bs4 import BeautifulSoup
import re

def download_excel_from_github(repo_url, output_dir="downloaded_files"):
    """
    Download Excel files from a GitHub repository and convert them to CSV.
    
    Args:
        repo_url (str): URL of the GitHub repository
        output_dir (str): Directory to save the downloaded files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    # Get the raw content URL
    if "github.com" in repo_url:
        raw_base_url = repo_url.replace("github.com", "raw.githubusercontent.com")
        if not raw_base_url.endswith("/"):
            raw_base_url += "/"
        if "/blob/" in raw_base_url:
            raw_base_url = raw_base_url.replace("/blob/", "/")
    
    try:
        # Get repository content
        response = requests.get(repo_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links that might contain Excel files
        excel_links = []
        for link in soup.find_all('a'):
            href = link.get('href', '')
            if href.endswith(('.xlsx', '.xls')):
                excel_links.append(href)
        
        if not excel_links:
            print("No Excel files found in the repository.")
            return
        
        # Download each Excel file and convert to CSV
        for link in excel_links:
            # Clean up the link and get the full URL
            file_name = os.path.basename(link)
            if link.startswith('/'):
                link = link[1:]
            file_url = urljoin(raw_base_url, link)
            
            try:
                # Download the Excel file
                print(f"Downloading: {file_name}")
                response = requests.get(file_url, stream=True)
                response.raise_for_status()
                
                # Save the Excel file temporarily
                temp_excel_path = os.path.join(output_dir, file_name)
                with open(temp_excel_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Convert to CSV
                csv_file_name = os.path.splitext(file_name)[0] + '.csv'
                csv_path = os.path.join(output_dir, csv_file_name)
                
                # Read Excel and save as CSV
                df = pd.read_excel(temp_excel_path)
                df.to_csv(csv_path, index=False)
                
                # Remove the temporary Excel file
                os.remove(temp_excel_path)
                
                print(f"Successfully converted {file_name} to {csv_file_name}")
                
            except Exception as e:
                print(f"Error processing {file_name}: {str(e)}")
                continue
    
    except Exception as e:
        print(f"Error accessing repository: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Replace with your GitHub repository URL
    repo_url = "https://github.com/username/repo/tree/main/path/to/excel/files"
    download_excel_from_github(repo_url)
