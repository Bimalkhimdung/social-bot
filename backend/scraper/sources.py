"""
Source configurations for the 3 default NEPSE news sources.

Each source config is a dict matching the Source ORM model fields.
selector_config JSON fields:
  - For HTML sources: {"title_selector": "css", "link_selector": "css", "summary_selector": "css", "image_selector": "css"}
  - For API sources: {"data_path": "dot.notation.path", "title_field": "...", "url_field": "...", ...}
"""

DEFAULT_SOURCES = [
    {
        "name": "ShareHub Nepal",
        "url": "https://sharehubnepal.com/account/api/v1/khula-manch/post?MediaType=News&Size=20",
        "source_type": "api",
        "is_active": True,
        "selector_config": {
            "data_path": "data",            # array is directly under 'data' key
            "title_field": "title",         # Nepali article headline
            "url_field": "launchUrl",       # direct article URL (no template needed)
            "url_template": "",             # empty = use url_field as-is
            "image_field": "mediaUrl",      # article thumbnail
            "summary_field": "summary",     # article summary snippet
            "source_label_field": "profileName",  # publisher name, e.g. "Corporate Samachar"
        },
    },
    {
        "name": "Arthasarokar",
        "url": "https://arthasarokar.com/category/market-affairs",
        "source_type": "html",
        "is_active": True,
        "selector_config": {
            "title_selector": "h3 a, h5 a",    # article title + link
            "link_attr": "href",
            "summary_selector": "p",           # first <p> after title
            "image_selector": "img",
            "image_attr": "src",
            "base_url": "https://arthasarokar.com",
        },
    },
    {
        "name": "Corporate Nepal",
        "url": "https://www.corporatenepal.com/category/capital",
        "source_type": "html",
        "is_active": True,
        "selector_config": {
            "title_selector": "h1 a, h5 a",
            "link_attr": "href",
            "summary_selector": "p",
            "image_selector": "img",
            "image_attr": "src",
            "base_url": "https://www.corporatenepal.com",
        },
    },
]
