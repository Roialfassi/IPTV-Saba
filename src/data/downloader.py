#!/usr/bin/env python3
import requests
import os
import sys
from tqdm import tqdm

def download_mp4(url, output_filename=None):
    """
    Download an MP4 file from a URL and save it to disk with progress bar

    Args:
        url (str): URL of the MP4 file to download
        output_filename (str, optional): Name to save the file as. If None, extracts from URL.

    Returns:
        str: Path to the downloaded file
    """
    try:
        # If no output filename provided, extract from URL
        if not output_filename:
            output_filename = url.split('/')[-1]
            if '?' in output_filename:
                output_filename = output_filename.split('?')[0]
            if not output_filename.endswith('.mp4'):
                output_filename += '.mp4'

        # Send a streaming GET request
        print(f"Downloading {url}...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()  # Raise exception for HTTP errors

        # Get file size if available
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte

        # Create progress bar
        progress_bar = tqdm(total=total_size, unit='iB', unit_scale=True)

        # Write the file to disk
        with open(output_filename, 'wb') as file:
            for data in response.iter_content(block_size):
                progress_bar.update(len(data))
                file.write(data)

        progress_bar.close()

        # Verify download
        if total_size != 0 and progress_bar.n != total_size:
            print("WARNING: Downloaded file size doesn't match expected size")

        print(f"Download complete: {os.path.abspath(output_filename)}")
        return os.path.abspath(output_filename)

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        sys.exit(1)

if __name__ == "__main__":
    download_mp4("http://worldiptv.me:8080/movie/fwNqqZfSrZWf/jAQCcnHh5rWr/161851.mkv", "uncharted.mkv")
    download_mp4("http://worldiptv.me:8080/movie/fwNqqZfSrZWf/jAQCcnHh5rWr/171541.mkv", "inception.mkv")
    download_mp4("http://worldiptv.me:8080/movie/fwNqqZfSrZWf/jAQCcnHh5rWr/184016.mp4", "anora.mp4")


