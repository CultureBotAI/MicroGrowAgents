#!/usr/bin/env python
"""Debug script to examine Sci-Hub HTML structure."""

import requests
import re

# Test DOI that Sci-Hub loaded successfully but we couldn't extract PDF from
doi = "10.1111/1462-2920.13023"
scihub_url = f"https://sci-hub.se/{doi}"

print(f"Fetching Sci-Hub page for {doi}...")
print(f"URL: {scihub_url}\n")

try:
    response = requests.get(scihub_url, timeout=10, allow_redirects=True)
    print(f"Status: {response.status_code}")
    print(f"Final URL: {response.url}")
    print(f"Content-Type: {response.headers.get('Content-Type')}\n")

    if response.status_code == 200:
        html = response.text
        print(f"HTML length: {len(html)} characters\n")

        # Save HTML to file for inspection
        with open("/tmp/scihub_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("✓ HTML saved to /tmp/scihub_page.html\n")

        # Look for various patterns
        print("=" * 70)
        print("Pattern matching results:")
        print("=" * 70)

        # 1. Embed tags
        embed_matches = re.findall(r'<embed[^>]+>', html, re.IGNORECASE)
        print(f"\n1. <embed> tags found: {len(embed_matches)}")
        for match in embed_matches[:3]:
            print(f"   {match}")

        # 2. Iframe tags
        iframe_matches = re.findall(r'<iframe[^>]+>', html, re.IGNORECASE)
        print(f"\n2. <iframe> tags found: {len(iframe_matches)}")
        for match in iframe_matches[:3]:
            print(f"   {match}")

        # 3. PDF links
        pdf_matches = re.findall(r'https?://[^\s"\'<>]+\.pdf', html)
        print(f"\n3. Direct PDF links found: {len(pdf_matches)}")
        for match in pdf_matches[:3]:
            print(f"   {match}")

        # 4. JavaScript redirects
        js_matches = re.findall(r'location\.href\s*=\s*["\']([^"\']+)["\']', html)
        print(f"\n4. JavaScript location.href found: {len(js_matches)}")
        for match in js_matches[:3]:
            print(f"   {match}")

        # 5. Button onclick
        button_matches = re.findall(r'<button[^>]+onclick[^>]+>', html, re.IGNORECASE)
        print(f"\n5. Buttons with onclick found: {len(button_matches)}")
        for match in button_matches[:3]:
            print(f"   {match}")

        # 6. Save button
        save_matches = re.findall(r'<button[^>]*id=["\']?save[^>]*>', html, re.IGNORECASE)
        print(f"\n6. Save button found: {len(save_matches)}")
        for match in save_matches[:3]:
            print(f"   {match}")

        # 7. Look for any src= attributes
        src_matches = re.findall(r'src=["\']([^"\']+)["\']', html)
        print(f"\n7. All src= attributes: {len(src_matches)}")
        for match in src_matches[:10]:
            print(f"   {match}")

except Exception as e:
    print(f"Error: {e}")
