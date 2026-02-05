#!/usr/bin/env python3
"""
Breathscape Webflow Migration Script
Downloads all CDN assets and rewrites HTML to use local paths
"""

import os
import re
import requests
from urllib.parse import urlparse
from pathlib import Path

# The HTML content (we'll read from file)
HTML_FILE = "index.html"
OUTPUT_DIR = "breathscape-site"

def extract_cdn_urls(html_content):
    """Extract all Webflow CDN URLs from HTML"""
    # Match cdn.prod.website-files.com URLs
    pattern = r'https://cdn\.prod\.website-files\.com/[^"\s\)>]+'
    urls = set(re.findall(pattern, html_content))
    
    # Also grab d3e54v103j8qbb.cloudfront.net (Webflow's jQuery CDN)
    pattern2 = r'https://d3e54v103j8qbb\.cloudfront\.net/[^"\s\)>]+'
    urls.update(re.findall(pattern2, html_content))
    
    return urls

def url_to_local_path(url):
    """Convert CDN URL to local file path"""
    parsed = urlparse(url)
    path = parsed.path.lstrip('/')
    
    # Simplify the path structure
    if 'website-files.com' in url:
        # Extract just the filename/path after the site ID
        parts = path.split('/')
        if len(parts) >= 2:
            # Keep structure: assets/css/*, assets/js/*, assets/images/*
            if '/css/' in path:
                return f"assets/css/{parts[-1].split('?')[0]}"
            elif '/js/' in path:
                return f"assets/js/{parts[-1].split('?')[0]}"
            else:
                # Images and other files
                filename = parts[-1].split('?')[0]
                return f"assets/images/{filename}"
    elif 'cloudfront.net' in url:
        filename = path.split('/')[-1].split('?')[0]
        return f"assets/js/{filename}"
    
    return f"assets/{path.split('/')[-1].split('?')[0]}"

def download_asset(url, local_path, output_dir):
    """Download a single asset"""
    full_path = os.path.join(output_dir, local_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(full_path, 'wb') as f:
            f.write(response.content)
        return True, len(response.content)
    except Exception as e:
        return False, str(e)

def main():
    # Read HTML
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Extract URLs
    urls = extract_cdn_urls(html)
    print(f"Found {len(urls)} CDN URLs to download\n")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Download each asset and build URL mapping
    url_mapping = {}
    total_size = 0
    
    for url in sorted(urls):
        local_path = url_to_local_path(url)
        success, result = download_asset(url, local_path, OUTPUT_DIR)
        
        if success:
            url_mapping[url] = local_path
            total_size += result
            print(f"✓ {local_path} ({result:,} bytes)")
        else:
            print(f"✗ FAILED: {url[:60]}... - {result}")
    
    # Rewrite HTML with local paths
    new_html = html
    for old_url, new_path in url_mapping.items():
        new_html = new_html.replace(old_url, new_path)
    
    # Save new HTML
    output_html = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(new_html)
    
    print(f"\n{'='*50}")
    print(f"Downloaded {len(url_mapping)} assets ({total_size:,} bytes total)")
    print(f"Output directory: {OUTPUT_DIR}/")
    print(f"HTML saved to: {output_html}")

if __name__ == "__main__":
    main()