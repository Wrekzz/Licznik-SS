import discord
from discord.ext import commands
import os
import json

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

KANAL_1_ID = 1530941134816153660
KANAL_2_ID = 1541126147830448168 

PLIK_BAZY = "rankingi.json"

# =========================================================================
# ⚙️ TUTAJ WPISZ AKTUALNE PUNKTY PRZED PIERWSZYM URUCHOMIENIEM NOWEGO KODU:
# Wpisz ID użytkownika (w cudzysłowie) oraz jego punkty, np. "123456789": 15
# =========================================================================
STARE_PUNKTY_KANAL_1 = {
    "576481432340267023": 19,
    "393812412752461824": 19,
    "401956994950627338": 2
}

STARE_PUNKTY_KANAL_2 = {
    "576481432340267023": 24,
    "393812412752461824": 8
}
# =========================================================================

ranking_messages = {
    KANAL_1_ID: None,
    KANAL_2_ID: None
}

def zaladuj_dane():
    """Wczytuje rankingi z pliku JSON lub tworzy nowe, jeśli plik nie istnieje"""
    if os.path.exists(PLIK_BAZY):
        with open(PLIK_BAZY, "r", encoding="utf-8") as f:
            dane = json.load(f)
            # Konwersja kluczy tekstowych z JSON na int (ID użytkowników w discord.py)
            r1 = {int(k): v for k, v in dane.get("kanal_1", {}).items()}
            r2 = {int(k): v for k, v in dane.get("kanal_2", {}).items()}
            return r1, r2
    else:
        # Jeśli plik nie istnieje, ładuje przepisane wyżej stare punkty
        r1 = {int(k): v for k, v in STARE_PUNKTY_KANAL_1.items() if k != "ID_UZYTKOWNIKA_1"}
        r2 = {int(k): v for k, v in STARE_PUNKTY_KANAL_2.items() if k != "ID_UZYTKOWNIKA_1"}
        zapisz_dane(r1, r2)
        return r1, r2

def zapisz_dane(r1, r2):
    """Zapisuje aktualny stan słowników do pliku JSON"""
    dane = {
        "kanal_1": {str(k): v for k, v in r1.items()},
        "kanal_2": {str(k): v for k, v in r2.items()}
    }
    with open(PLIK_BAZY, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4, ensure_ascii=False)

# Ładowanie danych przy starcie skryptu
ranking_kanal_1, ranking_kanal_2 = zaladuj_dane()

def generuj_ranking_embed(ranking_dict, numer_kanalu):
    """Generuje wizualną tabelę rankingu (Embed)"""
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

async def aktualizuj_ranking_na_kanale(channel_id, ranking_dict, numer_kanalu):
    """Wysyła lub edytuje istniejący post z tabelą wyników"""
    kanal = bot.get_channel(channel_id)
    if not kanal:
        return

    embed = generuj_ranking_embed(ranking_dict, numer_kanalu)

    if ranking_messages[channel_id]:
        try:
            msg = await kanal.fetch_message(ranking_messages[channel_id])
            await msg.edit(embed=embed)
            return
        except discord.NotFound:
            ranking_messages[channel_id] = None

    async for message in kanal.history(limit=50):
        if message.author == bot.user and message.embeds and message.embeds[0].title == f"🏆 RANKING SS - KANAŁ {numer_kanalu}":
            ranking_messages[channel_id] = message.id
            await message.edit(embed=embed)
            return

    nowa_wiadomosc = await kanal.send(embed=embed)
    ranking_messages[channel_id] = nowa_wiadomosc.id

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    await aktualizuj_ranking_na_kanale(KANAL_1_ID, ranking_kanal_1, 1)
    await aktualizuj_ranking_na_kanale(KANAL_2_ID, ranking_kanal_2, 2)

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
            zapisz_dane(ranking_kanal_1, ranking_kanal_2)
            await aktualizuj_ranking_na_kanale(KANAL_1_ID, ranking_kanal_1, 1)

    # KANAŁ 2
    elif message.channel.id == KANAL_2_ID and message.attachments:
        dodano_foto = False
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_2[message.author.id] = ranking_kanal_2.get(message.author.id, 0) + 1
                dodano_foto = True
                
        if dodano_foto:
            zapisz_dane(ranking_kanal_1, ranking_kanal_2)
            await aktualizuj_ranking_na_kanale(KANAL_2_ID, ranking_kanal_2, 2)

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset1(ctx):
    ranking_kanal_1.clear()
    zapisz_dane(ranking_kanal_1, ranking_kanal_2)
    await aktualizuj_ranking_na_kanale(KANAL_1_ID, ranking_kanal_1, 1)
    await ctx.send("🗑️ **Ranking dla KANAŁU 1 został wyzerowany!**", delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset2(ctx):
    ranking_kanal_2.clear()
    zapisz_dane(ranking_kanal_1, ranking_kanal_2)
    await aktualizuj_ranking_na_kanale(KANAL_2_ID, ranking_kanal_2, 2)
    await ctx.send("🗑️ **Ranking dla KANAŁU 2 został wyzerowany!**", delete_after=5)

@reset1.error
@reset2.error
async def reset_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Nie masz uprawnień, aby zresetować ten ranking!", delete_after=5)

bot.run(os.environ.get("MOJ_TAJNY_KLUCZ"))
