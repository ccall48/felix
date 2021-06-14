"""This is a cog for a discord.py bot
It will add commands for anybody to use to search one of NASA's most
popular sites APOD (Astronomy Picture of The Day).

Commands:
    apod
    ├ today     Todays NASA Astronomy Picture of the day
    ├ random    A random picture since 1995-16-06 until today.
    └ date      Date for APOD picture YYYY-MM-DD format starting 1995-16-06
"""

import re
import random
from datetime import datetime as dt, timedelta
import calendar
import discord
from discord.ext import commands#, tasks
from discord import Embed#, DMChannel, Member


class Nasa(commands.Cog, name='Nasa'):
    def __init__(self, client):
        self.client = client
        self.date_check = re.compile(
            r'^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])$'
        )


    @commands.command(name='apod',
        aliases=['space']
        )
    async def apod_day(self, ctx, fordate: str = None):
        """Show todays APOD picture/video link if no date selected"""
        def validate_date(year, month, date):
            """Returns True if valid date else False"""
            try:
                dt(year, month, date)
                return True
            except ValueError:
                return False

        if fordate == None:
            fordate = dt.utcnow().strftime('%Y-%m-%d')

        date_check = fordate.split('-')

        if fordate >= '1995-06-16' and\
             fordate <= dt.utcnow().strftime('%Y-%m-%d') and\
                 validate_date(int(date_check[0]), int(date_check[1]), int(date_check[2])):
                 #self.date_check.match(fordate):

            async with self.client.session.get(
                            f'https://api.nasa.gov/planetary/apod'
                          + f'?api_key={self.client.config["nasa_key"]}'
                          + f'&date={fordate}') as response:
                apod = await response.json()

                embed = Embed(description=apod['explanation'],
                            color=random.randint(0, 0xFFFFFF))

                if apod['media_type'] == 'image':
                    embed.set_image(url=apod['url'])
                else:
                    embed.add_field(name='Video URI', value=apod['url'])

                embed.set_author(
                    name=apod['title'],
                    icon_url='https://api.nasa.gov/assets/img/favicons/favicon-192.png')

                if 'copyright' in apod:
                    embed.set_footer(
                        text=f'Copyright: {apod["copyright"]}\n'
                        + f'Date: {apod["date"]}\n'
                        + f'Provided By: https://api.nasa.gov/')
                else:
                    embed.set_footer(
                        text=f'Date: {apod["date"]}\n'
                        + f'Provided By: https://api.nasa.gov/')

                await ctx.send(embed=embed)

        else:
            embed = Embed(description=f'APOD valid date format YYYY-MM-DD\n\n'
                                    + f'Valid search dates start from 16th June 1995 (1995-06-16)\n'
                                    + f'until Today {dt.utcnow().strftime("%Y-%m-%d")}.\n\n'
                                    + f'Todays date will be used if not specified.',
                            color=random.randint(0, 0xFFFFFF))
            embed.set_author(
                    name=f'NASA Astronomy Picture of the Day',
                    icon_url='https://api.nasa.gov/assets/img/favicons/favicon-192.png')

            await ctx.send(embed=embed)

# date with no known copyright for testing
# 2013-09-23

# date with long copyright description...
# 2014-09-25
'''
    @commands.command(name='apodr',
        aliases=['spacer']
        )
    async def apod_random(self, ctx):
        #async with self.client.session.get(f'https://api.nasa.gov/planetary/apod?api_key={self.client.config["nasa_key"]}&count=1') as response:
        async with self.client.session.get(f'https://api.nasa.gov/planetary/apod?api_key={self.client.config["nasa_key"]}') as response:
            today = await response.json()
            taken = today["date"]
            explanation = today["explanation"]
            img_title = today["title"]
            image_url = today["url"]
            
            if today["media_type"] == 'image':
                embed=discord.Embed(
                    title=img_title,
                    icon_url='https://api.nasa.gov/assets/img/favicons/favicon-192.png',
                    url="https://realdrewdata.medium.com/",
                    description=explanation,
                    color=random.randint(0, 0xFFFFFF)
                )
                await ctx.send(embed=embed)
            else: # video
                embed=discord.Embed(
                title=img_title,
                icon_url='https://api.nasa.gov/assets/img/favicons/favicon-192.png',
                url="https://realdrewdata.medium.com/",
                description=explanation,
                color=random.randint(0, 0xFFFFFF)
            )
            await ctx.send(embed=embed)
'''

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Nasa(client))
