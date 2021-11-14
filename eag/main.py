import os
import shutil
from pathlib import Path

import requests as requests

from eag.constants import APP_ROOT_DIR, PROJECT_ROOT_DIR, ANNOUNCES_PATH, OLD_ANNOUNCES_PATH
from eag.exceptions import AnnounceAlreadyProcessedException, UnknownTemplateException
from eag.utils.logging import logger
from jinja2 import Template
from bs4 import BeautifulSoup
from eag.config import settings


def get_announce_template():
    with open(os.path.join(APP_ROOT_DIR, "templates/announce.html"), 'r', encoding='utf-8') as f:
        template = f.read()
        return template


def archive_old_announces():
    file_names = os.listdir(ANNOUNCES_PATH)
    for file_name in file_names:
        shutil.move(os.path.join(ANNOUNCES_PATH, file_name), OLD_ANNOUNCES_PATH)


"""
Create announce folders if not already created
"""


def create_announce_folders():
    Path(ANNOUNCES_PATH).mkdir(parents=True, exist_ok=True)
    Path(OLD_ANNOUNCES_PATH).mkdir(parents=True, exist_ok=True)


def write_announce(title: str, content: str):
    output_path = os.path.join(ANNOUNCES_PATH, title + settings.announces_file_extension)
    with open(output_path, 'w', encoding='utf-8') as f:
        logger.debug(f"Writing announce to {output_path}")
        f.write(content)


def big_image_url(ebay_image_url: str):
    to_replace = ebay_image_url.rsplit("/")[-1]
    return ebay_image_url.replace(to_replace, "s-l1600.jpg")


def create_announce(item_url: str):
    logger.debug("Working on announce: " + item_url)
    page = requests.get(item_url)
    soup = BeautifulSoup(page.content, 'html.parser')
    # If this announce is already set, we should not process it
    description_iframe = soup.find('iframe', attrs={'id': 'desc_ifr'})
    description_iframe_url = description_iframe.attrs['src']
    description_iframe_page = requests.get(description_iframe_url)
    description_iframe_soup = BeautifulSoup(description_iframe_page.content, 'html.parser')
    if description_iframe_soup.find('div', attrs={'id': 'product-description'}) is not None:
        raise AnnounceAlreadyProcessedException("This announce has already been processed")

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
    # Case 1 : Description has an unknown template (eg: contains images)
    # Remember: Alread processed announces contain images
    # but they are already excluded at the beginning of this function call.
    if description_iframe_soup.find_all('img'):
        raise UnknownTemplateException(
            f"Not processed announces should not include images."
            f"Image found in article description. Please check your announce: {item_url}")
    # Case 2 : Description is raw text only: this will be our announce description
    else:
        logger.debug(f"description iframe url: {description_iframe_url}")
        content = description_iframe_soup.find('div', attrs={'id': 'ds_div'})
        # Remove excess new lines at the beginning and at the end
        announce_description = content.get_text(separator="\n").rstrip().lstrip()
        logger.trace(announce_description)
    # TODO Create announce from template: filename, title, text description, photos

    # Now that we have all the required information, let's create the announce
    # Load the template
    announce_template = Template(get_announce_template())

    # Prepare all the template parameters
    store_name = settings.store_name
    store_slogan = settings.store_slogan
    # Images
    number_of_images = len(image_urls)
    img_inputs = []
    img_div_images = []
    img_labels = []
    for i in range(number_of_images):
        # inputs
        img_index = i + 1
        if img_index == 1:
            checked = "checked"
        else:
            checked = ""
        img_input = f'<input id="img{img_index}" type="radio" name="img" {checked}>\n'
        img_inputs.append(img_input)
        # images
        img_div_image = f'<div class="image" id="show{img_index}">\n<img src="' \
                        f'{image_urls[i]}">\n</div>\n'
        img_div_images.append(img_div_image)
        # thumbmails
        img_label = f'<label for="img{img_index}">\n<div class="thumbnail">\n<img src="' \
                    f'{image_urls[i]}">\n</div></label>\n '
        img_labels.append(img_label)
    # Concatenate each table in one stirng. Performant stirng concatenation
    img_inputs = ''.join(img_inputs)
    img_div_images = ''.join(img_div_images)
    img_labels = ''.join(img_labels)

    # Announce description
    announce_description = announce_description.replace("\n", "\n<br/>")
    logger.debug(f"announce_description:\n{announce_description}")
    # Generate the final HTML announce
    announce_html = announce_template.render(store_name=store_name, store_slogan=store_slogan,
                                             img_inputs=img_inputs, img_div_images=img_div_images,
                                             img_labels=img_labels, title=announce_title,
                                             description=announce_description)
    logger.trace(announce_html)
    write_announce(announce_title, announce_html)


def main():
    with logger.catch():
        logger.info("eBay Announce Generator started!")
        create_announce_folders()
        logger.info(f"Moving announces to archive folder: {OLD_ANNOUNCES_PATH}")
        archive_old_announces()
        store_url = f"https://www.{settings.ebay_website}/sch/m.html?_ssn=" \
                    f"{settings.ebay_user}&_pppn=r1&scp=ce0"
        logger.debug("Looking for items in store: " + str(store_url))
        page = requests.get(store_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        store_items_div = soup.find('div', attrs={'id': 'Results'})
        item_links = store_items_div.find_all('a', attrs={'class': 'vip'})
        for item_link in item_links:
            url = item_link['href']
            try:
                create_announce(url)
            except AnnounceAlreadyProcessedException:
                logger.info(f"Announce already created for url {url}. Ignoring it.")
