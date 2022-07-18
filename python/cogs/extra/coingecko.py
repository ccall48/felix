"""This is a cog for a discord.py bot.
it collects current crypto prices from coingecko simple api

Commands:
    coin
    ├ price         full name of token eg. bitcoin for multiple leave a space
    ├ value         current market price for token
    ├ graph         price graph for token 
    ├ tokens        WIP > list of all tokens on coingeko
    └ currencies    WIP > all conversion possible currencies for comparisons (default USD)
"""

import asyncio
from datetime import datetime as dt

import pandas as pd
import matplotlib.pyplot as plt

from discord.ext import commands, tasks
from discord import Embed, File


class Coingecko(commands.Cog, name='Coin'):
    API_URL_BASE = 'https://api.coingecko.com/api/v3'
    CG_ICON = 'https://cdn.discordapp.com/attachments/788621973709127693/988362901213548604/cg.webp'

    def __init__(self, client, currency='usd', api_base=API_URL_BASE, cg_icon=CG_ICON):
        self.client = client
        self.currency = currency
        self.api_base = api_base
        self.cg_icon = cg_icon

        self.supported_currencies.start()
        self.supported_tokens.start()


    @tasks.loop(count=1)
    async def supported_currencies(self):
        """list of all supported currencies - list"""
        async with self.client.session.get(
            f'{self.api_base}/simple/supported_vs_currencies'
        ) as response:
            self.currencies = await response.json()

    @tasks.loop(count=1)
    async def supported_tokens(self):
        async with self.client.session.get(f'{self.api_base}/coins/list') as response:
            self.tokens = [(token['id'], token['symbol']) for token in await response.json()]

    def get_token(self, token: str):
        for (token_id, token_symbol) in self.tokens:
            if token.lower() in (token_id.lower(), token_symbol.lower()):
                return token_id

    async def create_token_graph(self, num_days: int, token: str, vs_currency: str):
        async with self.client.session.get(
            f'{self.api_base}/coins/{token}/market_chart?vs_currency={vs_currency}'+
            f'&days={num_days}&interval=daily'
        ) as response:
            data = await response.json()

            df = pd.DataFrame(data['prices'])
            df['dt'] = pd.to_datetime((df[0] // 1000), unit='s')
            df[1] = round(df[1], 2)

            heading_font = {'family': 'serif', 'color': 'green', 'size': 25}
            label_font = {'family': 'serif', 'color': 'red', 'size': 15}

            plt.title(f'{token.title()} Price Graph', fontdict=heading_font)
            plt.ylabel(f'Price {vs_currency.upper()}', fontdict=label_font)

            plt.plot(df['dt'], df[1])
            plt.grid(axis='y')
            plt.tick_params(axis='x', rotation=25)
            plt.savefig('token_graph.png')
            plt.cla()
            return True


    # ----------------------------------------------
    # coingecko simple api cog commands
    # ----------------------------------------------
    @commands.group(
        pass_context=True,
        name='coingecko',
        aliases=['cg'],
        hidden=True,
        invoke_without_command=True,
    )
    async def coin(self, ctx):
        "Commands to view current token prices"
        await ctx.send_help('coingecko')


    @coin.command(
        name='ping',
        hidden=True
    )
    async def coingecko_ping(self, ctx):
        async with self.client.session.get(f'{self.api_base}/ping') as response:
            data = await response.json()

            embed = Embed(
                        color=0xFFFF00,
                        title=[x for x in data.keys()][0].replace('_', ' ').title(),
                        description=f'{[x for x in data.values()][0]} :rocket:',
                    )
            embed.set_thumbnail(
                url=self.cg_icon
            )
            embed.set_footer(
                text=f'https://coingecko.com/',
                icon_url=self.cg_icon
                )
            await ctx.send(embed=embed)


    @coin.command(
        name='price',
        aliases=['$']
    )
    async def token_price(self, ctx, *token):
        """Current price for {token} or {token1} {token2} {token3}"""
        tokens = ','.join((str(self.get_token(x)) for x in token))

        async with self.client.session.get(
            f'{self.api_base}/simple/price?ids={tokens}&vs_currencies={self.currency}'+
            f'&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true'
        ) as response:
            data = await response.json()

            for tokens, prices in data.items():
                embed = Embed(
                        color=0xFFFF00,
                        title=f'{tokens.title()} Price',
                        url=f'https://www.coingecko.com/en/coins/{tokens}'
                    )
                embed.set_thumbnail(
                    url=self.cg_icon
                )
                for desc, value in prices.items():
                    match desc:
                        case 'usd':
                            value = round(value, 2)
                            embed.add_field(
                                name='Price (USD)',
                                value='$' + '{:,}'.format(value),
                                inline=True
                            )
                        case 'usd_market_cap':
                            value = int(round(value, 0))
                            embed.add_field(
                                name='Market Cap (USD)',
                                value='{:,}'.format(value),
                                inline=True
                            )
                        case 'usd_24h_vol':
                            value = int(round(value, 0))
                            embed.add_field(
                                name='24hr Volume (USD)',
                                value='{:,}'.format(value),
                                inline=True
                            )
                        case 'usd_24h_change':
                            value = round(value, 2)
                            embed.add_field(
                                name='24hr Change (USD)',
                                value='{:,}'.format(value) + '%',
                                inline=True
                            )
                embed.set_footer(
                text=f'https://coingecko.com/',
                icon_url=self.cg_icon
                )
                await ctx.send(embed=embed)
                await asyncio.sleep(1)


    @coin.command(
        name='value',
        aliases=['val', 'howmuch']
    )
    async def token_amount(self, ctx, token: str, currency: str, amt:float=None):
        """Current value for X amount of tokens. {token} {currency} {amount}"""
        token_err = token
        token = self.get_token(token.lower())

        async with self.client.session.get(
            f'{self.api_base}/simple/price?ids={token}&vs_currencies={currency}'
        ) as response:
            data = await response.json()

            if not token:
                embed = Embed(
                        color=0xFFFF00,
                        title='Error',
                        description=f'Token: `{token_err}` invalid or not found!'
                    )
                embed.set_footer(
                    text=f'https://coingecko.com/',
                    icon_url=self.cg_icon
                )
                return await ctx.send(embed=embed)

            if currency not in self.currencies:
                embed = Embed(
                        color=0xFFFF00,
                        title='Error',
                        description=f"{currency.upper()} not found, supported currencies:\n"+
                                    f"```{', '.join([x for x in self.currencies])}```"
                    )
                embed.set_footer(
                    text=f'https://coingecko.com/',
                    icon_url=self.cg_icon
                )
                return await ctx.send(embed=embed)

            if not amt:
                embed = Embed(
                        color=0xFFFF00,
                        title='Error',
                        description=f'Amount `{amt}` not a valid amount.'
                    )
                embed.set_footer(
                    text=f'https://coingecko.com/',
                    icon_url=self.cg_icon
                )
                return await ctx.send(embed=embed)

            embed = Embed(
                        color=0xFFFF00,
                        title=f'{token.title()} Price',
                        url=f'https://www.coingecko.com/en/coins/{token}'
                    )
            embed.set_thumbnail(
                url=self.cg_icon
            )
            embed.add_field(
                name='Token Amt',
                value=amt,
                inline=True
            )
            embed.add_field(
                name=f'Price ({currency.upper()})',
                value='$' + '{:,}'.format(data[token][currency] * amt),
                inline=True
            )
            embed.set_footer(
                text=f'https://coingecko.com/',
                icon_url=self.cg_icon
            )
        await ctx.send(embed=embed)


    @coin.command(
        name='graph',
        aliases=['g', 'chart']
    )
    async def token_graph(self, ctx, num_days: int, token: str, vs_currency: str):
        """Price graph for token, {num_days} {token} {vs_currency}"""
        token_err = token
        token = self.get_token(token)

        if not token:
            embed = Embed(
                    color=0xFFFF00,
                    title='Error',
                    description=f'Token: `{token_err}` invalid or not found!'
                )
            embed.set_footer(
                text=f'https://coingecko.com/',
                icon_url=self.cg_icon
            )
            return await ctx.send(embed=embed)

        if vs_currency not in self.currencies:
            embed = Embed(
                    color=0xFFFF00,
                    title='Error',
                    description=f"{vs_currency.upper()} not found, supported currencies:\n"+
                                f"```{', '.join([x for x in self.currencies])}```"
                )
            embed.set_footer(
                text=f'https://coingecko.com/',
                icon_url=self.cg_icon
            )
            return await ctx.send(embed=embed)

        await ctx.typing()
        if await self.create_token_graph(num_days, token, vs_currency):
            with open('token_graph.png', 'rb') as token_graph:
                file_to_send = File(token_graph)
            await ctx.send(file=file_to_send)
        else:
            await ctx.send('Nothing found')


    # ----------------------------------------------
    # Cog Tasks
    # ----------------------------------------------
async def setup(client):
    """This is called when the cog is loaded via load_extension"""
    await client.add_cog(Coingecko(client))
