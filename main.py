"""
Manga Post Discord Bot by dmellogu, special thanks to MangadexAPI and Cubari
"""
import os
import asyncio
import requests
import discord
import inflect
from ratelimit import limits, RateLimitException
from backoff import on_exception, expo
from dotenv import load_dotenv

load_dotenv()

client = discord.Client()


@client.event
async def on_ready():
    """On start up."""
    print('We have logged in as {0.user}'.format(client))

@on_exception(expo, RateLimitException, max_time=30)
@limits(calls=15, period=1)
def request_data(title):
    """Gets data from Mangadex API."""
    payload = {'title': title}
    response = requests.get('https://api.mangadex.org/manga', params=payload)
    return response.json()


@client.event
async def on_message(message):
    """Answers user messages."""
    if message.author.bot:
        return

    p = inflect.engine()

    if message.content == '!start':
        await message.author.send(
            '-' * 25 + '\n' +
            ('Hello %s\n' % message.author.name) +
            '-' * 25 + '\n' +
            ('Enter ***!search*** along with the name\nof a manga for me to find.')
        )

    if message.content.startswith('!search') and message.channel == message.author.dm_channel:
        ids = {}
        r = request_data(message.content.lstrip('!search'))
        results = []
        counter = 1
        for entry in r['data']:
            print(entry['attributes']['title']['en'])
            results.append(str(counter) + '. ' + entry['attributes']['title']['en'])
            ids[str(counter)] = {
                'id': entry['id'],
                'title': entry['attributes']['title']['en'],
                'description': entry['attributes']['description']['en']
            }
            counter += 1
        results_str = "\n".join(results)
        if len(ids) == 1:
            await message.author.send('**One** result found:')
        else:
            await message.author.send('**%s** results found:\n' \
                % p.number_to_words(len(ids)).capitalize())

        if counter != 1:
            await message.author.send('-' * 25)
            await message.author.send(results_str)
            await message.author.send('-' * 25)
            await message.author.send('Enter index to read manga now.')

        def check(m):
            return bool(m.content in ids and m.channel == m.author.dm_channel \
                        or m.content.startswith('!'))

        try:
            msg = await client.wait_for('message', check=check, timeout=120.0)
        except asyncio.TimeoutError:
            return
        else:
            if msg.content.startswith('!'):
                return
            url = "https://cubari.moe/read/mangadex/{}/".format(ids[msg.content]['id'])
            embed = discord.Embed(title=ids[msg.content]['title'],
                                  url=url,
                                  description=ids[msg.content]['description'],
                                  color=discord.Color.blue())
        await message.author.send(embed=embed)


client.run(os.getenv('TOKEN'))
