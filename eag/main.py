import requests as requests

from ebay_announce_generator.utils.logging import logger
from jinja2 import Template
from bs4 import BeautifulSoup
from ebay_announce_generator.config import settings


def big_image_url(ebay_image_url: str):
    to_replace = ebay_image_url.rsplit("/")[-1]
    return ebay_image_url.replace(to_replace, "s-l1600.jpg")


def create_announce(item_url: str):
    logger.debug("Working on announce: " + item_url)
    page = requests.get(item_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    # If this announce is already set, we should not process it
    description_iframe_url = soup.find('iframe', attrs={'id': 'desc_ifr'})
    description_iframe_page = requests.get(description_iframe_url.attrs['src'])
    description_iframe_soup = BeautifulSoup(description_iframe_page.content, 'html.parser')
    if description_iframe_soup.find('div', attrs={'id': 'product-description'}) is not None:
        raise ValueError("This announce has already been processed")

    # Remove <span> content to get the right announce title
    # "<span class="g-hdn">Details about </span>Announce Title" becomes "Announce Title"
    for content in soup.select('#itemTitle'):
        content.span.decompose()

    # Extract title
    announce_title = soup.find('h1', attrs={'id': 'itemTitle'}).text
    logger.debug("Title: " + str(announce_title))

    # Extract image URLs
    image_urls = []
    try:
        images = soup.find('div', attrs={'id': 'vi_main_img_fs'}).find_all('img')
        for image in images:
            logger.debug("image: " + str(image['src']))
            image_urls.append(big_image_url(image['src']))
    except AttributeError:
        # No miniature has been found so there is only one picture to get
        url = soup.find('img', attrs={'id': 'icImg'})['src']
        image_urls.append(big_image_url(url))
    logger.debug("Images for this announce: " + str(image_urls))

    # Extract text description
    # Case 1 : Description already has a known template: do not touch
    # Case 2 : Description is raw text only: this will be our announce description
    # Case 3 : Description has an unknown template: ignore this announce
    # TODO Extract data: images & URLs, Title, Text description inside the announce
    # TODO Create announce from template: filename, title, text description, photos


def main():
    with logger.catch():
        store_url = f"https://www.ebay.fr/sch/m.html?_ssn={settings.ebay_user}&_pppn=r1&scp=ce0"
        logger.debug("Looking for items in store: " + str(store_url))
        page = requests.get(store_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        store_items_div = soup.find('div', attrs={'id': 'Results'})
        item_links = store_items_div.find_all('a', attrs={'class': 'vip'})
        for item_link in item_links:
            create_announce(item_link['href'])
