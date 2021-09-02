"""This is a cog for a discord.py bot.
It will interact with a chirpstack lorawan server

Commands:
    applications|apps   Show all applications registered on network server
    devicedata|dd       device information for organization ID
    devices|dev         Show device data for available devices by application ID
    devicekeys|dk       device keys for device EUI
    deviceprofile|dp    Show setup profile for device UUID for device profile
    networkserver|ns    network server information for given ID
    gateways|gw         gateway stats for organization ID
    gateway_stat|gstat gateway stats for number of days specified
     ├
     └
"""
import random
import json
from datetime import datetime as dt, timedelta as td
from discord.ext import commands
from discord import Embed, DMChannel, Member


class Lorawan(commands.Cog, name='Lorawan'):
    def __init__(self, client):
        self.client = client
        self.api_url = 'https://chirpstack.dred.net.au/api'
        self.headers = {
            "content-type": "application/json",
            "Grpc-Metadata-Authorization": self.client.config['chirpstack_token']
        }

    @commands.command(name='applications',
        aliases=['apps']
        )
    async def applications(self, ctx):
        """Show all applications registered on network server"""
        async with self.client.session.get(
            f'{self.api_url}/applications?limit=100',
            headers=self.headers
            ) as response:

            lora = await response.json()

            if lora['totalCount'] == '0':
                raise commands.BadArgument(f'No Applications Found')

            embed = Embed(description="",
                          color=random.randint(0, 0xFFFFFF))

            text = ''
            for app in lora['result']:
                # text += f"Organization ID: {app['organizationID']}\nName: {app['name']}\nDesc: {app['description']}\nProfile ID: {app['serviceProfileID']}\nProfile Name: {app['serviceProfileName']}\n\n"
                text += f"{app['description']}\nProfile ID: {app['serviceProfileID']}\n\n"

            embed.add_field(name='Applications', value=text)
            embed.set_author(
            name=f'Chirpstack Dred Applications',
            url='https://chirpstack.dred.net.au',
            icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)

    @commands.command(name='devicedata',
        aliases=['dd'])
    async def devicedata(self, ctx, id: int):
        """Show device information for given organization ID"""
        async with self.client.session.get(
            f'{self.api_url}/internal/devices/summary?organizationID={id}',
            headers=self.headers) as response:

            lora = await response.json()

            embed = Embed(description=f'Device Data for Organization {id}',
                          color=random.randint(0, 0xFFFFFF))
            embed.add_field(name='Active', value=lora['activeCount'], inline=False)
            embed.add_field(name='Inactive', value=lora['inactiveCount'], inline=False)
            if '0' in lora['drCount']:
                embed.add_field(name='DR0', value=lora['drCount']['0'], inline=True)
            if '1' in lora['drCount']:
                embed.add_field(name='DR1', value=lora['drCount']['1'], inline=True)
            if '2' in lora['drCount']:
                embed.add_field(name='DR2', value=lora['drCount']['2'], inline=True)
            if '3' in lora['drCount']:
                embed.add_field(name='DR3', value=lora['drCount']['3'], inline=True)
            if '4' in lora['drCount']:
                embed.add_field(name='DR4', value=lora['drCount']['4'], inline=True)
            if '5' in lora['drCount']:
                embed.add_field(name='DR5', value=lora['drCount']['5'], inline=True)
            embed.add_field(name='Never Seen', value=lora['neverSeenCount'], inline=False)
            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)


    @commands.command(name='devices',
        aliases=['dev']
        )
    async def devices(self, ctx, id: int):
        """Show device data for available devices by application ID"""
        async with self.client.session.get(
            f'{self.api_url}/devices?limit=100&applicationID={id}',
            headers=self.headers
            ) as response:

            lora = await response.json()

            if lora['totalCount'] == '0':
                raise commands.BadArgument(f'No Application for ID {id}')

            embed = Embed(description=f"UUID: {lora['result'][0]['deviceProfileID']}",
                          color=random.randint(0, 0xFFFFFF))

            dateObj = lambda x: (dt.strptime(x, '%Y-%m-%dT%H:%M:%S') + td(hours=10)).strftime('%d-%m-%Y %H:%M:%S')
            text = ''
            for dev in lora['result']:
                text += f"{dev['name']} | {dev['devEUI']}\nLast Seen {dateObj(dev['lastSeenAt'][:-8])}\n\n"

            embed.add_field(name='Application Device Information', value=text)
            embed.set_author(
            name=f'Chirpstack Dred Application {id}',
            url='https://chirpstack.dred.net.au',
            icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)


    @commands.command(name='deviceprofile',
        aliases=['dp']
        )
    async def deviceprofile(self, ctx, uuid: str):
        """Show setup profile for device UUID for device profile"""
        async with self.client.session.get(
            f'{self.api_url}/device-profiles/{uuid}',
            headers=self.headers
            ) as response:

            lora = await response.json()

            if 'deviceProfile' not in lora:
                raise commands.BadArgument(f'No Profile or invalid device profile UUID {uuid}')

            text = ''
            for k, v in lora['deviceProfile'].items():
                if v == '' or k == 'payloadDecoderScript':
                    pass
                else:
                    text += f"{k}: {v}\n"

            embed = Embed(description=f'Device profile setup',
                          color=random.randint(0, 0xFFFFFF))

            embed.add_field(name='Device Profile Information', value=text[:1024], inline=False)
            
            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)


    @commands.command(name='applicationid',
        aliases=['appid']
        )
    async def applicationid(self, ctx, id: int):
        """Show application information for ID"""
        async with self.client.session.get(
            f'{self.api_url}/applications/{id}',
            headers=self.headers
            ) as response:

            lora = await response.json()

            if 'application' not in lora:
                raise commands.BadArgument(f'No Application for ID {id}')

            text = ''
            for k, v in lora['application'].items():
                if v == '' or None:
                    pass
                else:
                    text += f"{k}: {v}\n"

            embed = Embed(description=f'Application {id} Information',
                          color=random.randint(0, 0xFFFFFF))

            embed.add_field(name='Application Information', value=text[:1024], inline=False)
            
            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)


    @commands.command(name='devicekeys',
        aliases=['devkey', 'dk']
        )
    async def devicekeys(self, ctx, dev_eui: str):
        """Show device keys for device (HEX encoded) for device"""
        async with self.client.session.get(
            f'{self.api_url}/devices/{dev_eui}/keys',
            headers=self.headers
            ) as response:

            lora = await response.json()

            embed = Embed(description=f'Key data for device.',
                          color=random.randint(0, 0xFFFFFF))
            embed.add_field(name='Device EUI', value=lora['deviceKeys']['devEUI'], inline=False)
            embed.add_field(name='Net Key', value=lora['deviceKeys']['nwkKey'], inline=False)
            embed.add_field(name='App Key', value=lora['deviceKeys']['appKey'], inline=False)
            embed.add_field(name='Gen Key', value=lora['deviceKeys']['genAppKey'], inline=False)
            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)


    @commands.command(name='networkserver',
        aliases=['ns']
        )
    async def network_servers(self, ctx, id: int):
        """Show information for given network-server ID"""
        async with self.client.session.get(
            f'{self.api_url}/network-servers/{id}',
            headers=self.headers
            ) as response:

            lora = await response.json()

            embed = Embed(description=f'Dred Network-Server {id}',
                          color=random.randint(0, 0xFFFFFF))
            embed.add_field(name='Server Name', value=lora['networkServer']['name'], inline=False)
            embed.add_field(name='Discovery Enabled', value=lora['networkServer']['gatewayDiscoveryEnabled'], inline=False)
            embed.add_field(name='Discovery Interval', value=lora['networkServer']['gatewayDiscoveryInterval'], inline=False)
            embed.add_field(name='Discovery TX Freq', value=lora['networkServer']['gatewayDiscoveryTXFrequency'], inline=False)
            embed.add_field(name='Discovery DR', value=lora['networkServer']['gatewayDiscoveryDR'], inline=False)
            embed.add_field(name='Created', value=lora['createdAt'], inline=False)
            embed.add_field(name='Version', value=lora['version'], inline=True)
            embed.add_field(name='Region', value=lora['region'], inline=True)
            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)


    @commands.command(name='gateways',
        aliases=['gw']
        )
    async def gateways(self, ctx, id: int):
        """Show gateway information for organization ID"""
        async with self.client.session.get(
            f'{self.api_url}/internal/gateways/summary?organizationID={id}',
            headers=self.headers
            ) as response:

            lora = await response.json()

            embed = Embed(description=f'Organization {id} Gateways',
                          color=random.randint(0, 0xFFFFFF))

            embed.add_field(name='Active', value=lora['activeCount'], inline=True)
            embed.add_field(name='Inactive', value=lora['inactiveCount'], inline=True)
            embed.add_field(name='Never Seen', value=lora['neverSeenCount'], inline=True)

            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)


    @commands.command(name='gateway_stat',
        aliases=['gstat']
        )
    async def gateway_stats(self, ctx, gw_id, num_days: int):
        """Show a gateway stats for number of given days"""
        dt_from = (dt.utcnow() - td(days=(num_days-1))).strftime('%Y-%m-%dT00:00:00Z')
        dt_now = (dt.utcnow() + td(hours=10)).strftime('%Y-%m-%dT%H:%M:%SZ')
        dt_test = datetime.utcnow() - timedelta(minutes=5)

        async with self.client.session.get(
            f'{self.api_url}/gateways/{gw_id}/stats?interval=day&startTimestamp={dt_from}&endTimestamp={dt_now}',
            headers=self.headers
            ) as response:

            gw_stats = await response.json()

            gw_data = {}
            for data in gw_stats['result']:
                for key, value in data.items():
                    if key != 'timestamp':
                        if key not in gw_data.keys():
                            gw_data[key] = value
                        else:
                            gw_data[key] += value

            embed = Embed(description=f'{gw_id} Gateway Stats',
                        color=random.randint(0, 0xFFFFFF))

            embed.add_field(name='RX Packets', value=gw_data['rxPacketsReceived'], inline=False)
            embed.add_field(name='RX Packets OK', value=gw_data['rxPacketsReceivedOK'], inline=False)
            embed.add_field(name='TX Received', value=gw_data['txPacketsReceived'], inline=False)
            embed.add_field(name='TX Sent', value=gw_data['txPacketsEmitted'], inline=False)

            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)

'''
    @commands.command(name='organizations',
        aliases=['org']
        )
    async def organizations(self, ctx, id: int):
        """Show organization information for given ID"""
        async with self.client.session.get(
            f'{self.api_url}<END_POINT>',
            headers=self.headers
            ) as response:

            lora = await response.json()

            embed = Embed(description=f'Organization {id}',
                          color=random.randint(0, 0xFFFFFF))

            embed.add_field(name='Organization Name', value=lora['displayName'], inline=False)
            embed.add_field(name='Created', value=lora['createdAt'], inline=False)
            
            embed.set_author(
                name='Chirpstack Dred',
                url='https://chirpstack.dred.net.au',
                icon_url='https://dred.net.au/static/csw_icon.png')

            await ctx.send(embed=embed)
'''

def setup(client):
    """This is called when the cog is loaded via load_extension"""
    client.add_cog(Lorawan(client))
