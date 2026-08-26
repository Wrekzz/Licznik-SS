import discord
from discord.ext import commands
import os
import asyncio

# Definiujemy klasę bota, aby poprawnie zainicjalizować zadania startowe w tle
class KlasaBota(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all())

    async def setup_hook(self):
        # setup_hook gwarantuje, że te zadania uruchomią się we właściwym momencie życia bota
        self.loop.create_task(aktualizuj_ranking_na_kanale(ranking_kanal_1, 1))
        self.loop.create_task(aktualizuj_ranking_na_kanale(ranking_kanal_2, 2))

bot = KlasaBota()

# Kanały, na które użytkownicy wrzucają zdjęcia (SS)
KANAL_1_ID = 1530941134816153660
KANAL_2_ID = 1541126147830448168 

# 📺 SPECJALNY KANAŁ, NA KTÓRYM BOT MA POKAZYWAĆ TABELE:
KANAL_RANKINGU_ID = 1541150631623000144

# Punkty graczy jako klucze int
ranking_kanal_1 = {
    576481432340267023: 19,
    393812412752461824: 19,
    401956994950627338: 2
}

ranking_kanal_2 = {
    576481432340267023: 24,
    393812412752461824: 8
}

# Słownik przechowujący ID wiadomości z tabelami
ranking_messages = {
    1: None,
    2: None
}

def generuj_ranking_embed(ranking_dict, numer_kanalu):
    """Tworzy estetyczną ramkę (Embed) z posortowanymi wynikami"""
    posortowany = sorted(ranking_dict.items(), key=lambda item: item[1], reverse=True)
    
    embed = discord.Embed(
        title=f"🏆 RANKING SS - KANAŁ {numer_kanalu}", 
        color=discord.Color.gold()
    )
    
    opis = ""
    if not posortowany:
        opis = "*Brak zrzutów ekranu na tym kanale.*"
    else:
        for poz, (gracz_id, pkty) in enumerate(posortowany, start=1):
            opis += f"**{poz}.** <@{gracz_id}> — `{pkty}` SS\n"
            
    embed.description = opis
    embed.set_footer(text="Aktualizowane automatycznie w czasie rzeczywistym")
    return embed

async def aktualizuj_ranking_na_kanale(ranking_dict, numer_kanalu):
    """Wysyła nową tabelę lub edytuje już istniejącą na dedykowanym kanale"""
    await bot.wait_until_ready()
    print(f"🔄 [START] Uruchamianie procedury dla tabeli kanału {numer_kanalu}...")
    
    kanal = bot.get_channel(KANAL_RANKINGU_ID)
    if not kanal:
        try:
            kanal = await bot.fetch_channel(KANAL_RANKINGU_ID)
        except Exception as e:
            print(f"❌ [BŁĄD] Bot nie ma dostępu do kanału {KANAL_RANKINGU_ID}: {e}")
            return

    embed = generuj_ranking_embed(ranking_dict, numer_kanalu)

    # 1. Próba edycji z pamięci podręcznej
    if ranking_messages[numer_kanalu]:
        try:
            msg = await kanal.fetch_message(ranking_messages[numer_kanalu])
            await msg.edit(embed=embed)
            print(f"✅ Wyedytowano istniejącą tabelę dla kanału {numer_kanalu} z pamięci.")
            return
        except discord.NotFound:
            ranking_messages[numer_kanalu] = None

    # 2. Szukanie starej tabeli w historii (zapobiega duplikatom)
    try:
        async for message in kanal.history(limit=50):
            if message.author == bot.user and message.embeds:
                if message.embeds[0].title == f"🏆 RANKING SS - KANAŁ {numer_kanalu}":
                    ranking_messages[numer_kanalu] = message.id
                    await message.edit(embed=embed)
                    print(f"✅ Znaleziono i wyedytowano starą tabelę dla kanału {numer_kanalu} z historii.")
                    return
    except Exception as e:
        print(f"⚠️ Nie udało się przeszukać historii kanału: {e}")

    # 3. Jeśli nie ma wiadomości bota, wyślij nową
    try:
        nowa_wiadomosc = await kanal.send(embed=embed)
        ranking_messages[numer_kanalu] = nowa_wiadomosc.id
        print(f"✅ Wysłano zupełnie nową tabelę dla kanału {numer_kanalu}!")
    except discord.Forbidden:
        print(f"❌ [BŁĄD] Brak uprawnień do wysyłania wiadomości/embedów na kanale {KANAL_RANKINGU_ID}!")
    except Exception as e:
        print(f"❌ [BŁĄD] Nieznany problem: {e}")

@bot.event
async def on_ready():
    print(f"🤖 Zalogowano jako {bot.user}")
    print("✅ Bot działa i nasłuchuje.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # KANAŁ 1
    if message.channel.id == KANAL_1_ID and message.attachments:
        dodano_foto = False
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_1[message.author.id] = ranking_kanal_1.get(message.author.id, 0) + 1
                dodano_foto = True
        
        if dodano_foto:
            await aktualizuj_ranking_na_kanale(ranking_kanal_1, 1)

    # KANAŁ 2
    elif message.channel.id == KANAL_2_ID and message.attachments:
        dodano_foto = False
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_2[message.author.id] = ranking_kanal_2.get(message.author.id, 0) + 1
                dodano_foto = True
                
        if dodano_foto:
            await aktualizuj_ranking_na_kanale(ranking_kanal_2, 2)

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset1(ctx):
    ranking_kanal_1.clear()
    await aktualizuj_ranking_na_kanale(ranking_kanal_1, 1)
    await ctx.send("🗑️ **Ranking 1 został wyzerowany!**", delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset2(ctx):
    ranking_kanal_2.clear()
    await aktualizuj_ranking_na_kanale(ranking_kanal_2, 2)
    await ctx.send("🗑️ **Ranking 2 został wyzerowany!**", delete_after=5)

@reset1.error
@reset2.error
async def reset_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Nie masz uprawnień administratora!", delete_after=5)

# Prawidłowy start bota dla discord.py v2
bot.run(os.environ.get("MOJ_TAJNY_KLUCZ"))
