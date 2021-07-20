import os
import sys

import discord
import yaml
from discord.ext import commands

if not os.path.isfile("config.yaml"):
    sys.exit("'config.yaml' not found! Please add it and try again.")
else:
    with open("config.yaml") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)


class Help(commands.Cog, name="help"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help(self, context):
        """
        - Список всех команд из каждого модуля
        """
        prefix = config["bot_prefix"]
        descr = "Дополнительные параметры:\n" \
                "**:hero:** - имя героя (ru|eng)\n" \
                "**:lvl:** - уровень героя\n" \
                "**:btn:** - клавиши способности (q|w|e|r|d)\n" \
                "**:cnt:** - количество (необ.)"
        if not isinstance(prefix, str):
            prefix = prefix[0]
        embed = discord.Embed(title="Help", description=f"{descr}", color=config["success"])
        for i in self.bot.cogs:
            if i != 'slash' and i != 'owner':
                cog = self.bot.get_cog(i.lower())
                commands = cog.get_commands()
                command_list = [command.name for command in commands]
                command_description = [command.help for command in commands]
                help_text = '\n'.join(f'{prefix}{n} {h}' for n, h in zip(command_list, command_description))
                embed.add_field(name=i.capitalize(), value=f'```{help_text}```', inline=False)
        await context.send(embed=embed)


def setup(bot):
    bot.add_cog(Help(bot))
