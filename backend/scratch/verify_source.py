from bs4 import BeautifulSoup

with open('bajarkochirfar.html', 'r') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# Find first article
article = soup.find('article', class_='group')
if article:
    print("--- Article Container ---")
    print(article.prettify()[:1000])
    
    title_tag = article.find('h2') or article.find('h3')
    if title_tag:
        a_tag = title_tag.find('a')
        if a_tag:
            print("\n--- Title & Link ---")
            print(f"Title: {a_tag.get_text(strip=True)}")
            print(f"Link: {a_tag['href']}")
            
    img_tag = article.find('img')
    if img_tag:
        print("\n--- Image ---")
        print(f"Image Source: {img_tag.get('src') or img_tag.get('data-src') or img_tag.get('srcset')}")
else:
    print("No <article class='group'> found.")
