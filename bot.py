import discord
from discord.ext import commands
import os
import asyncio

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Kanały, na które użytkownicy wrzucają zdjęcia (SS)
KANAL_1_ID = 1530941134816153660
KANAL_2_ID = 1541126147830448168 

# 📺 SPECJALNY KANAŁ, NA KTÓRYM BOT MA POKAZYWAĆ TABELE:
KANAL_RANKINGU_ID = 1541150631623000144

ranking_kanal_1 = {
    576481432340267023: 19,
    393812412752461824: 19,
    401956994950627338: 2
}

ranking_kanal_2 = {
    576481432340267023: 24,
    393812412752461824: 8
}

ranking_messages = {1: None, 2: None}

def generuj_ranking_tekst(ranking_dict, numer_kanalu):
    """Generuje zwykły tekst zamiast kafelka Embed (na wypadek blokady uprawnień)"""
    posortowany = sorted(ranking_dict.items(), key=lambda item: item[1], reverse=True)
    wynik = f"🏆 **RANKING SS - KANAŁ {numer_kanalu}**\n"
    if not posortowany:
        wynik += "*Brak zrzutów ekranu.*"
    else:
        for poz, (gracz_id, pkty) in enumerate(posortowany, start=1):
            wynik += f"{poz}. <@{gracz_id}> — {pkty} SS\n"
    return wynik

async def aktualizuj_ranking_na_kanale(ranking_dict, numer_kanalu):
    await bot.wait_until_ready()
    print(f"🔄 Próba aktualizacji rankingu {numer_kanalu}...")
    
    kanal = bot.get_channel(KANAL_RANKINGU_ID)
    if not kanal:
        try:
            print(f"🛰️ Próba awaryjnego pobrania kanału {KANAL_RANKINGU_ID} przez fetch...")
            kanal = await bot.fetch_channel(KANAL_RANKINGU_ID)
        except Exception as e:
            print(f"❌ [BŁĄD] Bot całkowicie nie widzi kanału {KANAL_RANKINGU_ID}! Szczegóły: {e}")
            return

    tekst = generuj_ranking_tekst(ranking_dict, numer_kanalu)

    try:
        nowa_wiadomosc = await kanal.send(tekst)
        ranking_messages[numer_kanalu] = nowa_wiadomosc.id
        print(f"✅ Pomyślnie wysłano ranking {numer_kanalu} na Discorda!")
    except discord.Forbidden:
        print(f"❌ [BŁĄD] Discord zablokował wysyłanie! Bot NIE MA UPRAWNIEŃ (Send Messages) na kanale {KANAL_RANKINGU_ID}!")
    except Exception as e:
        print(f"❌ [BŁĄD] Nieznany błąd podczas wysyłania: {e}")

@bot.event
async def on_ready():
    print(f"🤖 Zalogowano jako {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == KANAL_1_ID and message.attachments:
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_1[message.author.id] = ranking_kanal_1.get(message.author.id, 0) + 1
        await aktualizuj_ranking_na_kanale(ranking_kanal_1, 1)

    elif message.channel.id == KANAL_2_ID and message.attachments:
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_2[message.author.id] = ranking_kanal_2.get(message.author.id, 0) + 1
        await aktualizuj_ranking_na_kanale(ranking_kanal_2, 2)

    await bot.process_commands(message)

async def main():
    async with bot:
        bot.loop.create_task(aktualizuj_ranking_na_kanale(ranking_kanal_1, 1))
        bot.loop.create_task(aktualizuj_ranking_na_kanale(ranking_kanal_2, 2))
        await bot.start(os.environ.get("MOJ_TAJNY_KLUCZ"))

import asyncio
asyncio.run(main())
