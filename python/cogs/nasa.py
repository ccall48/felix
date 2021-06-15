"""This is a cog for a discord.py bot
It will add commands for anybody to use to search one of NASA's most
popular sites APOD (Astronomy Picture of The Day).

Commands:
    apod        Shows todays APOD picture
    └ date      YYYY-MM-DD shows APOD for date (starting 1995-16-06)
"""

import random
from discord.ext import commands
from discord import Embed


class Nasa(commands.Cog, name='Nasa'):
    def __init__(self, client):
        self.client = client

    @commands.command(name='nasa',
        aliases=['apod', 'space']
        )
    async def apod_day(self, ctx, date: str = ''):
        """Show todays APOD picture/video link if no date selected"""
        async with self.client.session.get(
            'https://api.nasa.gov/planetary/apod'
            + f'?api_key={self.client.config["nasa_key"]}&date={date}'
        ) as response:

            apod_data = await response.json()
            if apod_data.get('code', 200) != 200:
                raise commands.BadArgument(apod_data.get('msg', 'Error'))
            embed = Embed(description=apod_data['explanation'],
                          color=random.randint(0, 0xFFFFFF))

            if apod_data['media_type'] == 'image':
                embed.set_image(url=apod_data['hdurl'])
            else:
                embed.add_field(name='Video URI', value=apod_data['url'])
            embed.set_author(
                name=apod_data['title'],
                icon_url='https://api.nasa.gov/assets/img/favicons/favicon-192.png')

            if 'copyright' in apod_data:
                embed.set_footer(
                    text=f'Copyright: {apod_data["copyright"]}\n'
                    + f'Date: {apod_data["date"]}\n'
                    + 'Provided By: https://api.nasa.gov/')
            else:
                embed.set_footer(
                    text=f'Date: {apod_data["date"]}\n'
                    + 'Provided By: https://api.nasa.gov/')

            await ctx.send(embed=embed)


def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Nasa(client))
