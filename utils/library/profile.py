import requests
import psycopg2.extras
import itertools as it
import discord
from discord import Member, utils
from bs4 import BeautifulSoup
from utils.classes.Player import Player
from utils.classes.Stats import Stats
from collections.abc import MutableMapping
from utils.classes import Const
from utils import exceptions, sql, library

leagues = {
    "Bronze": "Бронза",
    "Silver": "Серебро",
    "Gold": "Золото",
    "Platinum": "Платина",
    "Diamond": "Алмаз",
    "Master": "Мастер",
    "Grandmaster": "Грандмастер"
}


async def add_role(ctx, player: Player, role_name='5x5 player', message=True):
    try:
        member = ctx.guild.get_member(player.id)
        role = discord.utils.get(member.guild.roles, name=role_name)
        if role is None and role_name in leagues.items():
            role = discord.utils.get(member.guild.roles, name=leagues[role_name])
        await member.add_roles(role)
        if message:
            await ctx.send(f"Присвоена роль *{role.name}*")
    except Exception as e:
        #await ctx.send(f"Произошла ошибка. Обратитесь к <@{Const.config.owners[0]}>")
        #print(f"Вероятно не создана роль {role_name}")
        #print(e)
        pass


async def remove_role(ctx, player, role_name=Const.events.role):
    try:
        member = ctx.guild.get_member(player.id)
        role = utils.get(member.guild.roles, name=role_name)
        await member.remove_roles(role)
    except Exception as e:
        print(e)
        print(f"Нет роли {role_name} чтобы ее снять")


async def team_change_stats(ctx, team: list, guild_id, delta=6, points=1, winner=True):
    con, cur = library.get.con_cur()
    placeholder = '%s'
    placeholders = ', '.join(placeholder for unused in team)
    select = Const.selects.PlayersInBtag % placeholders
    cur.execute(select, team)
    records = cur.fetchall()
    for record in records:
        player = library.get.player(record)
        await remove_role(ctx, player)  # снятие роли если это возможно
        select = Const.selects.USIdGuild
        cur.execute(select, (player.id, guild_id))
        stats_rec = cur.fetchone()
        if stats_rec is None:
            player_stats = Stats(player.id, guild_id, player.btag)
            insert = Const.inserts.UserStats
            cur.execute(insert, (player_stats.id, player_stats.guild_id, player_stats.win,
                                 player_stats.lose, player_stats.points, player_stats.btag))
        else:
            player_stats = library.get.stats(stats_rec)
        player_stats.winstreak = winstreak_change(player_stats, winner)
        player_stats.max_ws = max_ws_change(player_stats)
        print(f"{player.btag}: mmr={player.mmr}, win={winner}, ws={player_stats.winstreak}", sep=" -> ")
        player.mmr = winstreak_mmr_change(player, player_stats.winstreak, winner)
        print(f"ws_mmr={player.mmr}", sep=' -> ')
        if player.mmr > 2900:
            delta = int(delta / 2)
        if winner:
            player.mmr += int(delta)
            player_stats.win += 1
            player_stats.points += points + 3
        else:
            player.mmr -= int(delta)
            player_stats.lose += 1
            player_stats.points += points
        print(f"new_mmr={player.mmr}")
        old_league = player.league
        player.league, player.division = library.get.league_division_by_mmr(player.mmr)
        if old_league != player.league:
            try:
                await remove_role(ctx, player, old_league)
                await add_role(ctx, player, player.league, message=False)
            except Exception:
                print(f"Не созданы роли {old_league}, {player.league}")
        updateUS = Const.updates.USPointWinLoseWinStr
        updateP = Const.updates.PlayerMMR
        cur.execute(updateUS, (player_stats.points, player_stats.win, player_stats.lose,
                               player_stats.winstreak, player_stats.max_ws,
                               player_stats.id, player_stats.guild_id))
        cur.execute(updateP, (player.mmr, player.league, player.division,
                              player.id))
    commit(con)


def winstreak_change(stats: Stats, winner):
    winstreak = stats.winstreak
    if winner:
        if stats.winstreak >= 0:
            winstreak += 1
        else:
            winstreak = 1
    else:
        if stats.winstreak >= 0:
            winstreak = -1
        else:
            winstreak -= 1
    return winstreak


def winstreak_mmr_change(profile: Player, winstreak, winner):
    mmr = profile.mmr
    if mmr > 2900:
        fix = 2
    else:
        fix = 1
    if winner and (winstreak > 2):
        mmr += int((winstreak * 2) / fix)
    if (not winner) and (winstreak < -2):
        mmr += int((winstreak * 2) / fix)  # + потому что winstreak уже отрицательный
    return mmr


def max_ws_change(stats: Stats):
    if stats.winstreak > stats.max_ws:
        return stats.winstreak
    else:
        return stats.max_ws


def flatten_dict(d: MutableMapping, parent_key: str = '', sep: str = '.') -> MutableMapping:
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + str(k) if parent_key else str(k)
        if isinstance(v, MutableMapping):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def min_diff_sets(data):
    """
        Parameters:
        - `data`: input list.
        Return:
        - min diff between sum of numbers in two sets
    """
    #print(data)
    if len(data) == 1:
        return data[0]
    s = sum(data)
    # `a` is list of all possible combinations of all possible lengths (from 1
    # to len(data) )
    a = []
    for i in range(1, len(data)):
        a.extend(list(it.combinations(data, i)))
    # `b` is list of all possible pairs (combinations) of all elements from `a`
    b = it.combinations(a, 2)
    # `c` is going to be final correct list of combinations.
    # Let apply 2 filters:
    # 1. leave only pairs where: sum of all elements == sum(data)
    # 2. leave only pairs where: flat list from pairs == data
    c = filter(lambda x: sum(x[0]) + sum(x[1]) == s, b)
    c = filter(lambda x: sorted([i for sub in x for i in sub]) == sorted(data), c)
    # `res` = [min_diff_between_sum_of_numbers_in_two_sets,
    #           ((set_1), (set_2))
    #         ]
    #print(c)
    res = sorted([(abs(sum(i[0]) - sum(i[1])), i) for i in c],
                 key=lambda x: x[0])
    # print(res)
    # return min([i[0] for i in res])
    min_mmr = min([i[0] for i in res])
    for i in res:
        if i[0] == min_mmr:
            red_team = i[1][0]
            blue_team = i[1][1]
            return red_team, blue_team


def profile_not_found(user) -> str:
        return f"Профиль {user} не найден в базе. Используйте команду */login* или */profile_add*"


def get_heroesprofile_data(btag, user_id, guild_id):
    try:
        #print("get_data")
        bname = btag.replace('#', '%23')
        base_url = 'https://www.heroesprofile.com'
        url = 'https://www.heroesprofile.com/Search/?searched_battletag=' + bname
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                     'Chrome/42.0.2311.135 Safari/537.36 Edge/12.246 '
        response = requests.get(url, headers={"User-Agent": f"{user_agent}"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        #print(url)
        error = soup.find('div', attrs={'id': 'choose_battletag'})
        if error is not None:
            links = error.find_all('a')
            for link in links:
                region = 'ion=2'
                if region in link['href']:
                    url_new = base_url + link['href'].replace('®', '&reg')
                    # print(url_new)
                    response = requests.get(url_new, headers={"User-Agent": f"{user_agent}"})
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')

        mmr_container = soup.find('section', attrs={'class': 'mmr-container'})
        mmr_info = mmr_container.find_all('div', attrs={'class': 'league-element'})
        storm_flag = False
        for elem in mmr_info:
            if elem.h3.text == 'Storm League':
                storm_flag = True
                tags = elem.find_all('div')
                for tag in tags[:1]:
                    profile_data = (" ".join(tag.text.split())).split()
                    #print(profile_data)
                    profile_wr = profile_data[2]
                    if profile_data[3] == 'Master':
                        profile_league = profile_data[3]
                        profile_division = 0
                        profile_mmr = int(''.join([i for i in profile_data[5] if i.isdigit()]))
                    else:
                        profile_league = profile_data[3]
                        profile_division = int(profile_data[4])
                        profile_mmr = int(''.join([i for i in profile_data[6] if i.isdigit()]))
                    if profile_mmr < 2200:
                        profile_mmr = 2200
                    return Player(btag=btag, id=user_id, guild_id=guild_id, mmr=profile_mmr, league=profile_league,
                                  division=profile_division)
        if not storm_flag:
            raise exceptions.LeagueNotFound
        return None
    except:
        print(f"Нет игр в hots")


def get_profile_by_id(id):
    sql.sql_init()
    con = sql.get_connect()
    cur = con.cursor(cursor_factory=psycopg2.extras.NamedTupleCursor)
    select = Const.selects.PlayersId
    cur.execute(select, (id,))
    record = cur.fetchone()
    player = library.get.player(record)
    return player, con, cur


def get_profile_by_id_or_btag(id_or_btag):
    con, cur = library.get.con_cur()
    user_id = library.get.user_id(id_or_btag)
    select = Const.selects.PlayersIdOrBtag
    cur.execute(select, (user_id, id_or_btag,))
    player = library.get.player(cur.fetchone())
    return player


def avatar(ctx, avamember: Member = None):
    try:  # discord
        return avamember.avatar_url
    except:  # pycord
        return avamember.avatar


def check_user(ctx):
    user_id = library.get.author_id(ctx)
    con, cur = library.get.con_cur()
    select = Const.selects.PlayersId
    cur.execute(select, (user_id,))
    player = library.get.player(cur.fetchone())
    return player


def change_mmr(player: Player, delta: int, plus=True):
    if plus:
        return player.mmr + delta
    else:
        return player.mmr - delta


def commit(con):
    con.commit()
    con.close()


def sort_by_mmr(player):
    return player.mmr
