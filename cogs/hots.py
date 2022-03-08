import json
from discord import Embed, Object, utils
from discord.ext.commands import command, Cog, errors
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle, InteractionType

from hots.function import open_hero, find_heroes, read_hero_from_message, hero_not_found, find_more_heroes, \
    args_not_found, get_hero, get_master_opinion, add_master_opinion
from hots.Hero import Hero
from hots.heroes import heroes_description, builds, embed_stlk_builds
from hots.nexuscompendium import weekly_rotation, sales, ranked
from hots.patchnotes import last_pn
from hots.skills import skill
from hots.talents import talents
from hots.tierlist import ban_heroes
from hots.twitch import get_streams
from hots.read_news import embed_news
from helpers import functions, check

# Only if you want to use variables that are in the config.yaml file.
config = functions.get_config()

short_patch = config["patch"][-5:]

gamestrings_json_file = 'data/gamestrings' + short_patch + '.json'
heroes_json_file = 'data/heroesdata' + short_patch + '.json'

pancho_json_file = functions.get_pancho()

with open(heroes_json_file) as heroes_json:
    heroes_data = json.load(heroes_json)
with open(gamestrings_json_file, encoding='utf-8') as ru_json:
    ru_data = json.load(ru_json)

# menu
heroes_label = 'Герой'
skills_label = 'Скиллы'
talent_label = 'Таланты'
lastpn_label = 'Патч'

# hero
descrp_label = 'Описание'
patchn_label = 'Патчноуты'
builds_label = 'Билды'

# skills
basic_label = 'Базовые'
heroic_label = "Героические"
trait_label = 'Особые'

# talents
lvl_01_label = '1'
lvl_04_label = '4'
lvl_07_label = '7'
lvl_10_label = '10'
lvl_13_label = '13'
lvl_16_label = '16'
lvl_20_label = '20'


mailing_channel_id = {
    'test_fenrir': 845658540341592098, #test
    'ru hots': 642853714515722241, #общение
    'Dungeon': 858455796412710922, #hots камеры
    'Stlk': 124864790110797824, #общие
    'Читер': 841669769115336704 #хотс
}

class Hots(Cog, name='Hots'):
    """
    — Команды связанные с хотсом помимо информации о героях
    """
    def __init__(self, bot):
        self.bot = bot

    @command(name='weekly')
    async def rotation(self, ctx):
        """
        — Список героев еженедельной ротации
        """
        embed = weekly_rotation()
        await ctx.send(
            embed=embed
        )

    @command(name="pancho")
    async def pancho(self, ctx, hero_name):
        """
        — Мнение Мастера
        """
        pancho = get_master_opinion(hero_name)
        await ctx.send(pancho)

    @command(name="pancho_add")
    @check.is_owner()
    async def pancho_add(self, ctx, hero_name, url):
        error = add_master_opinion(hero_name, url)
        if not error:
            await ctx.send("Запись была добавлена")
        else:
            await ctx.send("Ошибка при записи")


    @command(name="patchnotes")
    async def hots_notes(self, context):
        """
        — Информация по патчноутам
        """
        embed = last_pn(None, context.author)
        await context.send(embed=embed)

    @command(name='ban')
    async def ban_list(self, ctx):
        """
        — Список героев рекомендуемых к бану
        """
        embed = ban_heroes()
        await ctx.send(
            embed=embed
        )

    @command(name='sales')
    async def sales(self, ctx):
        """
        — Список скидок на героев
        """
        embed = sales()
        await ctx.send(
            embed=embed
        )

    @command(name='ranked')
    async def ranked(self, ctx):
        """
        — Информация о сроках текущего сезона
        """
        embed = ranked()
        await ctx.send(
            embed=embed
        )

    @command(name='data')
    async def data(self, ctx, hero_name):
        """
        — Полное описания героя
        """
        if hero_name is not None:
            hero = get_hero(hero_name)
            if isinstance(hero, Hero):
                embed = builds(hero, ctx.author)
                default_hero_name = hero.en.lower().replace('.', '').replace("'", "")
                heroespn_url = 'https://heroespatchnotes.com/hero/'
                heroespn_url_full = heroespn_url + default_hero_name.replace(' ', '') + '.html'
                menu_buttons = [
                    Button(style=ButtonStyle.blue, label=heroes_label, disabled=True),
                    Button(style=ButtonStyle.blue, label=skills_label),
                    Button(style=ButtonStyle.blue, label=talent_label),
                    Button(style=ButtonStyle.blue, label=lastpn_label),
                ]
                hero_buttons = [
                    Button(style=ButtonStyle.grey, label=descrp_label),
                    Button(style=ButtonStyle.grey, label=builds_label, disabled=True),
                    Button(style=ButtonStyle.URL, label=patchn_label, url=heroespn_url_full),
                ]
                await ctx.send(
                    embed=embed,
                    components=[
                        hero_buttons,
                        menu_buttons
                    ],
                )
            else:
                embed = find_more_heroes(hero, ctx.author, command='data')
                await ctx.send(embed=embed)
        else:
            embed = hero_not_found()
            await ctx.send(embed=embed)

    @command(name='streams')
    async def streams(self, ctx, count=5):
        """
        — Ссылки на запущенные стримы на твиче
        """
        if isinstance(int(count), int):
            embed = get_streams(int(count))
        else:
            embed = get_streams()
        await ctx.send(
            embed=embed
        )

    @command(name='stlk')
    async def stlk_builds(self, ctx, *hero_name):
        """
        — Авторские билды от про игрока **STLK**
        """
        name = ' '.join(hero_name)
        hero = get_hero(name)
        if isinstance(hero, Hero):
            embed = embed_stlk_builds(hero, ctx.author, ad=True)
        else:
            embed = find_more_heroes(hero, ctx.author, command="stlk")

        await ctx.send(embed=embed)

    @command(name='news')
    async def hots_news(self, ctx, *args):
        """
        — Предложить новость для публикации
        """
        if ctx.message.author.id in config["owners"]:
            for guild in self.bot.guilds:
                try:
                    channel = utils.find(lambda r: r.id in mailing_channel_id.values(), guild.text_channels)
                    if channel is not None:
                        embed = embed_news(ctx.author)
                        await channel.send(embed=embed)
                        print(f'{guild.name} : сообщение отправлено')
                except:
                    print(f'{guild.name} : недостаточно прав')
            await ctx.send('Рассылка выполнена')
        else:
            if len(args) == 0:
                await ctx.send('Добавьте описание новости после команды')
            else:
                description = ' '.join(args)
                embed = Embed(
                    title='Новая новость',
                    description=description,
                    color=config["info"]
                )
                embed.set_footer(
                    text=f"От пользователя {ctx.author}"
                )
                owner = self.bot.get_user(int(config["owner"]))
                # check if dm exists, if not create it
                if owner.dm_channel is None:
                    await owner.create_dm()
                # if creation of dm successful
                if owner.dm_channel is not None:
                    await owner.dm_channel.send(embed=embed)
                    message = 'Спасибо. Сообщение было отправлено'
                    await ctx.send(message)

    @Cog.listener()
    async def on_button_click(self, res):
        """
        Possible interaction types:
        - Pong
        - ChannelMessageWithSource
        - DeferredChannelMessageWithSource
        - DeferredUpdateMessage
        - UpdateMessage
        """
        embed = None
        components = None
        hero_name, tail = res.raw_data['d']['message']['embeds'][0]['title'].split(' / ', maxsplit=1)
        text, author = res.raw_data['d']['message']['embeds'][-1]['footer']['text'].split(': ', maxsplit=1)
        hero = Hero(hero_name)

        default_hero_name = hero_name.lower().replace('.', '').replace("'", "")
        heroespn_url = 'https://heroespatchnotes.com/hero/'
        heroespn_url_full = heroespn_url + default_hero_name.replace(' ', '') + '.html'

        menu_buttons = [
            Button(style=ButtonStyle.blue, label=heroes_label),
            Button(style=ButtonStyle.blue, label=skills_label),
            Button(style=ButtonStyle.blue, label=talent_label),
            Button(style=ButtonStyle.blue, label=lastpn_label),
        ]
        hero_buttons = [
            Button(style=ButtonStyle.grey, label=descrp_label),
            Button(style=ButtonStyle.grey, label=builds_label),
            Button(style=ButtonStyle.URL, label=patchn_label, url=heroespn_url_full),
        ]
        skill_buttons = [
            Button(style=ButtonStyle.grey, label=basic_label),
            Button(style=ButtonStyle.grey, label=heroic_label),
            Button(style=ButtonStyle.grey, label=trait_label),
        ]
        talent_buttons1 = [
            Button(style=ButtonStyle.grey, label=lvl_01_label),
            Button(style=ButtonStyle.grey, label=lvl_04_label),
            Button(style=ButtonStyle.grey, label=lvl_07_label),
            Button(style=ButtonStyle.grey, label=lvl_10_label),
        ]
        talent_buttons2 = [
            Button(style=ButtonStyle.grey, label=lvl_13_label),
            Button(style=ButtonStyle.grey, label=lvl_16_label),
            Button(style=ButtonStyle.grey, label=lvl_20_label),
        ]

        skill_components = [
            skill_buttons,
            menu_buttons
        ]
        hero_components = [
            hero_buttons,
            menu_buttons
        ]
        talent_components = [
            talent_buttons1,
            talent_buttons2,
            menu_buttons
        ]
        lastpn_components = [
            menu_buttons
        ]

        if res.component.label == descrp_label:
            embed = heroes_description(hero, author)
            components = hero_components
            components[0][0] = Button(style=ButtonStyle.grey, label=descrp_label, disabled=True)
            components[1][0] = Button(style=ButtonStyle.blue, label=heroes_label, disabled=True)
        if res.component.label == builds_label or \
                res.component.label == heroes_label:
            embed = builds(hero, author)
            components = hero_components
            components[0][1] = Button(style=ButtonStyle.grey, label=builds_label, disabled=True)
            components[1][0] = Button(style=ButtonStyle.blue, label=heroes_label, disabled=True)

        if res.component.label == skills_label:
            embed = skill(hero, author)
            components = skill_components
            components[0][0] = Button(style=ButtonStyle.grey, label=basic_label, disabled=True)
            components[1][1] = Button(style=ButtonStyle.blue, label=skills_label, disabled=True)
        if res.component.label == basic_label:
            embed = skill(hero, author, 'basic')
            components = skill_components
            components[0][0] = Button(style=ButtonStyle.grey, label=basic_label, disabled=True)
            components[1][1] = Button(style=ButtonStyle.blue, label=skills_label, disabled=True)
        if res.component.label == heroic_label:
            embed = skill(hero, author, 'heroic')
            components = skill_components
            components[0][1] = Button(style=ButtonStyle.grey, label=heroic_label, disabled=True)
            components[1][1] = Button(style=ButtonStyle.blue, label=skills_label, disabled=True)
        if res.component.label == trait_label:
            embed = skill(hero, author, 'trait')
            components = skill_components
            components[0][2] = Button(style=ButtonStyle.grey, label=trait_label, disabled=True)
            components[1][1] = Button(style=ButtonStyle.blue, label=skills_label, disabled=True)

        if res.component.label == talent_label or \
                res.component.label == lvl_01_label:
            embed = talents(hero, 1, author)
            components = talent_components
            components[0][0] = Button(style=ButtonStyle.grey, label=lvl_01_label, disabled=True)
            components[2][2] = Button(style=ButtonStyle.blue, label=talent_label, disabled=True)
        if res.component.label == lvl_04_label:
            embed = talents(hero, 4, author)
            components = talent_components
            components[0][1] = Button(style=ButtonStyle.grey, label=lvl_04_label, disabled=True)
            components[2][2] = Button(style=ButtonStyle.blue, label=talent_label, disabled=True)
        if res.component.label == lvl_07_label:
            embed = talents(hero, 7, author)
            components = talent_components
            components[0][2] = Button(style=ButtonStyle.grey, label=lvl_07_label, disabled=True)
            components[2][2] = Button(style=ButtonStyle.blue, label=talent_label, disabled=True)
        if res.component.label == lvl_10_label:
            embed = talents(hero, 10, author)
            components = talent_components
            components[0][3] = Button(style=ButtonStyle.grey, label=lvl_10_label, disabled=True)
            components[2][2] = Button(style=ButtonStyle.blue, label=talent_label, disabled=True)
        if res.component.label == lvl_13_label:
            embed = talents(hero, 13, author)
            components = talent_components
            components[1][0] = Button(style=ButtonStyle.grey, label=lvl_13_label, disabled=True)
            components[2][2] = Button(style=ButtonStyle.blue, label=talent_label, disabled=True)
        if res.component.label == lvl_16_label:
            embed = talents(hero, 16, author)
            components = talent_components
            components[1][1] = Button(style=ButtonStyle.grey, label=lvl_16_label, disabled=True)
            components[2][2] = Button(style=ButtonStyle.blue, label=talent_label, disabled=True)
        if res.component.label == lvl_20_label:
            embed = talents(hero, 20, author)
            components = talent_components
            components[1][2] = Button(style=ButtonStyle.grey, label=lvl_20_label, disabled=True)
            components[2][2] = Button(style=ButtonStyle.blue, label=talent_label, disabled=True)
        if res.component.label == lastpn_label:
            embed = last_pn(hero, author)
            components = lastpn_components
            components[0][3] = Button(style=ButtonStyle.blue, label=lastpn_label, disabled=True)
        if author == str(res.user):
            await res.respond(
                type=InteractionType.UpdateMessage, embed=embed, components=components
            )
        else:
            error_text = 'Команда вызвана другим пользователем, взаимодействие невозможно\n' \
                         'Введите /data :hero: для получения информации по герою'
            await res.respond(
                type=InteractionType.ChannelMessageWithSource, content=f"{error_text}"
            )
            # можно использовать или embed или content content=f"{res.component.label} pressed",


    @data.error
    @stlk_builds.error
    async def hots_handler(self, ctx, error):
        print("Обработка ошибок hots")
        if isinstance(error, errors.MissingRequiredArgument):
            embed = Embed(
                title="Ошибка! Введите все аргументы",
                color=config["error"]
            )
            embed.add_field(
                name="Пример:",
                value=f"_{config['bot_prefix']}{ctx.command} Самуро_",
                inline=False
            )
            embed.set_footer(
                text=f"{config['bot_prefix']}help для просмотра справки по командам"  # context.message.author если использовать без slash
            )
            await ctx.send(embed=embed)
        if isinstance(error, errors.CommandInvokeError):
            text = "Ошибка! Герой не найден"
            embed = Embed(
                title=text,
                color=config["error"]
            )
            embed.set_footer(
                text=f"{config['bot_prefix']}help для просмотра справки по командам"
                # context.message.author если использовать без slash
            )
            await ctx.send(embed=embed)

def setup(bot):
    DiscordComponents(bot)  # If you have this in an on_ready() event you can remove this line.
    bot.add_cog(Hots(bot))
