import discord
from discord.ext import commands

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Wpisz tutaj ID swoich dwóch kanałów z Discorda (same liczby, bez cudzysłowu)
KANAL_1_ID = 1530941134816153660
KANAL_2_ID = 1541126147830448168  

# Słowniki na dwa osobne rankingi
ranking_kanal_1 = {}
ranking_kanal_2 = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Jeśli wiadomość ma zdjęcie/plik i pochodzi z KANAŁU 1
    if message.channel.id == KANAL_1_ID and message.attachments:
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_1[message.author.id] = ranking_kanal_1.get(message.author.id, 0) + 1

    # Jeśli wiadomość ma zdjęcie/plik i pochodzi z KANAŁU 2
    elif message.channel.id == KANAL_2_ID and message.attachments:
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_2[message.author.id] = ranking_kanal_2.get(message.author.id, 0) + 1

    await bot.process_commands(message)

# [KOMENDA] Ranking z pierwszego kanału
@bot.command()
async def ranking1(ctx):
    posortowany = sorted(ranking_kanal_1.items(), key=lambda item: item[1], reverse=True)
    wynik = "**RANKING SS - KANAŁ 1:**\n"
    for poz, (gracz_id, pkty) in enumerate(posortowany, start=1):
        wynik += f"{poz}. <@{gracz_id}> - {pkty} SS\n"
    await ctx.send(wynik if len(posortowany) > 0 else "Brak zrzutów ekranu na tym kanale.")

# [KOMENDA] Ranking z drugiego kanału
@bot.command()
async def ranking2(ctx):
    posortowany = sorted(ranking_kanal_2.items(), key=lambda item: item[1], reverse=True)
    wynik = "**RANKING SS - KANAŁ 2:**\n"
    for poz, (gracz_id, pkty) in enumerate(posortowany, start=1):
        wynik += f"{poz}. <@{gracz_id}> - {pkty} SS\n"
    await ctx.send(wynik if len(posortowany) > 0 else "Brak zrzutów ekranu na tym kanale.")

# [KOMENDA] Reset pierwszego kanału
@bot.command()
@commands.has_permissions(administrator=True)
async def reset1(ctx):
    ranking_kanal_1.clear()
    await ctx.send("🧹 **Licznik zrzutów ekranu dla KANAŁU 1 został zresetowany do zera!**")

# [KOMENDA] Reset drugiego kanału
@bot.command()
@commands.has_permissions(administrator=True)
async def reset2(ctx):
    ranking_kanal_2.clear()
    await ctx.send("🧹 **Licznik zrzutów ekranu dla KANAŁU 2 został zresetowany do zera!**")

@reset1.error
@reset2.error
async def reset_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Nie masz uprawnień (Administratora), aby zresetować ten ranking!")

# Wklej swój skopiowany Token pomiędzy cudzysłowy poniżej:
import os
bot.run(os.environ.get("MOJ_TAJNY_KLUCZ"))
