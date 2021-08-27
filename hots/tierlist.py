import os
import sys

import requests
import yaml
from bs4 import BeautifulSoup
from discord import Embed

from hots.function import open_hero
from hots.Hero import Hero

if not os.path.isfile("config.yaml"):
    sys.exit("'config.yaml' not found! Please add it and try again.")
else:
    with open("config.yaml") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)

short_patch = config["patch"][-5:]


def ban_heroes(hero=None, author=None):
    response = requests.get('https://www.icy-veins.com/heroes/heroes-of-the-storm-general-tier-list')
    soup = BeautifulSoup(response.text, 'html.parser')
    tier_s_html = soup.find('div', attrs={'class': 'htl'})
    ban_list = tier_s_html.find_all('span', attrs={'class': 'htl_ban_true'})
    embed = Embed(
        title="Рекомендуемый бан лист",
        color=config["info"]
    )
    text = ''
    count = 1
    for hero_name in ban_list:
        next_element = hero_name.find_next_sibling("span")
        hero = Hero(next_element.text)
        if isinstance(hero, Hero):
            text += f"· {hero.ru}\n"
            count += 1
    embed.add_field(
        name="На основе рекомендаций Icy Veins",
        value=f"{text}",
        inline=False
    )
    if author is not None:
        embed.set_footer(
            text=f"Информация для: {author}"
        )
    return embed


if __name__ == '__main__':
    pass
