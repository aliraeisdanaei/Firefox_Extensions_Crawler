from bs4 import BeautifulSoup
import requests
import pandas as pd
import re

# import progressbar
from time import sleep
from progress.bar import Bar

# these values will stop the crawl after the number of times equals the cap
# turn off these cap (do all) by making this value -1
CATEGORY_CAP = 25
PAGES_CAP = 1
EXTENSIONS_CAP = -1

CATEGORIES_URL = "https://addons.mozilla.org/en-CA/firefox/extensions/categories"
BASE_URL = "https://addons.mozilla.org/"
PAGE_END_URL = "?page="

OUTPUT_FILENAME = "extensions_data.csv"

def get_extension_num_users(extension_soup: BeautifulSoup) -> str:
    """Returns the number of users of extension if found, else 'Not Found'"""
    # wrappers = list(extension_soup.findAll('div'))
    try:
        wrappers = list(extension_soup.findAll('dl', class_="MetadataCard-list"))
        for i in range(len(wrappers)):
            # print(wrappers[i].find('dt', class_="MetadataCard-title").get_text())
            if(wrappers[i].find('dt', class_="MetadataCard-title").get_text() == "Users"):
                # the title is users, so we have the previous one
                return wrappers[i].find('dd', class_="MetadataCard-content").get_text().replace(',', '')
    except Exception as e:
        print(e)
        
    return "Not Found"

def get_extension_name(extension_soup: BeautifulSoup) -> str:
    """Return is name the of the extension if found, else 'Not Found'"""
    try:
        return extension_soup.find('h1', class_="AddonTitle").get_text().split("by")[0].strip()
    except Exception as e:
        print(e)
        
    return "Not Found"

def get_extension_author(extension_soup: BeautifulSoup) -> str:
    """Return is author the of the extension if found, else 'Not Found'"""
    try:
        return extension_soup.find('h1', class_="AddonTitle").get_text().split("by")[1].strip()
    except Exception as e:
        print(e)
        
    return "Not Found"

def get_extension_rating(extension_soup: BeautifulSoup) -> str:
    """Return is rating the of the extension if found, else 'Not Found'"""
    try:
        return extension_soup.find('div', class_="AddonMeta-rating-title").get_text().replace(" Stars", "")
    except Exception as e:
        print(e)
        
    return "Not Found"

def get_extension_version(extension_soup: BeautifulSoup) -> float:
    """Return is version the of the extension as a float (other minor decmial places will be lost e.g. 7.2.13.3 --> 7.2) if found, else 'Not Found'"""
    try:
        version = extension_soup.find('dd', class_="AddonMoreInfo-version").get_text()
        # find a number or float inside version using regex
        version = re.findall("^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?", version)[0][0]
        return float(version)

    except Exception as e:
        print(e)
        
    return "Not Found"

def get_extension_size(extension_soup: BeautifulSoup) -> str:
    """Return is size the of the extension if found, else 'Not Found'"""
    try:
        return extension_soup.find('dd', class_="AddonMoreInfo-filesize").get_text()
    except Exception as e:
        print(e)
        
    return "Not Found"

def get_extension_license(extension_soup: BeautifulSoup) -> str:
    """Return is license the of the extension if found, else 'Not Found'"""
    try:
        return extension_soup.find('dd', class_="AddonMoreInfo-license").get_text()
    except Exception as e:
        print(e)
        
    return "Not Found"

def get_list_categories() -> list:
    """Return is a list of all of the categories in the CATEGORIES_URL"""
    categories_response = requests.get(CATEGORIES_URL)
    categories_soup = BeautifulSoup(categories_response.text, "html.parser")
    categories_list = list(categories_soup.findAll(class_="Categories-link"))
    return categories_list

def get_number_of_pages(category_end_URL: str) -> int:
    """Return is the number of pages in the category_end_URL page if found, else 1"""
    try:
        first_pg_response = requests.get(BASE_URL + category_end_URL)
        first_pg_soup = BeautifulSoup(first_pg_response.text, "html.parser")
        num_pgs = int(first_pg_soup.find("div", class_="Paginate-page-number").get_text().split("of")[-1].strip())
        return num_pgs
    except Exception as e:
        print(e)
    
    return 1

def get_category_extension_list(category_end_URL: str) -> list:
    """Return is a string of all of the extensions found in the category_end_URL page"""
    category_response = requests.get(BASE_URL + category_end_URL)
    category_soup = BeautifulSoup(category_response.text, "html.parser")
    category_exension_list = list(category_soup.findAll(class_="SearchResult-link"))
    return category_exension_list

def get_all_extensions() -> list:
    """
    Return is a list of dicts of the all the extensions
    Adheres to the capping rule for CATEGORY_CAP, PAGES_CAP, and EXTENSIONS_CAP
    If these values are -1 no cap will be applied, else only the value to the cap will be read for the categories, pages, and extensions
    """
    list_extensions = []
    categories_list = get_list_categories()

    print(f"\nI found {len(categories_list)} categories. I will now look through all of them.")

    for i_ctgy, category in enumerate(categories_list):
        
        # Capping
        if(CATEGORY_CAP != -1 and i_ctgy >= CATEGORY_CAP):
            break

        category_end_URL = category.attrs["href"]
        category_name = category.get_text().replace("&amp;", "&")
        
        num_pgs = get_number_of_pages(category_end_URL)


        for crnt_pg_num in range(num_pgs):
            # Capping
            if(PAGES_CAP != -1 and crnt_pg_num >= PAGES_CAP):
                break

            extension_list = get_category_extension_list(f"{category_end_URL}{PAGE_END_URL}{crnt_pg_num + 1}")
            with Bar(f"Extensions in category {i_ctgy + 1}--Page {crnt_pg_num + 1} of {num_pgs}: ", max = len(extension_list)) as extensions_bar:
                for i_extension, extension in enumerate(extension_list):

                    # Capping
                    if(EXTENSIONS_CAP != -1 and i_extension >= EXTENSIONS_CAP):
                        break

                    extension_end_URL = extension.attrs["href"]
                    # print(extension_end_URL)

                    extension_response = requests.get(BASE_URL + extension_end_URL)
                    extension_soup = BeautifulSoup(extension_response.text, "html.parser")

                    extension_name = get_extension_name(extension_soup)
                    extension_author = get_extension_author(extension_soup)
                    extension_rating = get_extension_rating(extension_soup)
                    extension_num_users = get_extension_num_users(extension_soup)
                    extension_version = get_extension_version(extension_soup)
                    extension_size = get_extension_size(extension_soup)
                    extension_license = get_extension_license(extension_soup)
                    
                    list_extensions.append({
                        "name": extension_name,
                        "author": extension_author,
                        "category": category_name,
                        "rating": extension_rating,
                        "num_users": extension_num_users,
                        "version": extension_version,
                        "size": extension_size,
                        "license": extension_license
                    })

                    extensions_bar.next()

    return list_extensions  

list_extensions = get_all_extensions()
extensions_df = pd.DataFrame(list_extensions)
extensions_df.to_csv(OUTPUT_FILENAME, index=False)