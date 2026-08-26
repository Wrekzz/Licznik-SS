import discord
from discord.ext import commands
import os
import json
import asyncio

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Kanały, na które użytkownicy wrzucają zdjęcia (SS)
KANAL_1_ID = 1530941134816153660
KANAL_2_ID = 1541126147830448168 

# 📺 TUTAJ WPISZ ID SPECJALNEGO KANAŁU, NA KTÓRYM BOT MA POKAZYWAĆ TABELE:
KANAL_RANKINGU_ID = 1541150631623000144

PLIK_BAZY = "rankingi.json"

# Przepisane przez Ciebie aktualne punkty graczy
STARE_PUNKTY_KANAL_1 = {
    "576481432340267023": 19,
    "393812412752461824": 19,
    "401956994950627338": 2
}

STARE_PUNKTY_KANAL_2 = {
    "576481432340267023": 24,
    "393812412752461824": 8
}

# Słownik przechowujący ID wiadomości z tabelami (1 = Pierwsza tabela, 2 = Druga tabela)
ranking_messages = {
    1: None,
    2: None
}

def zaladuj_dane():
    """Wczytuje rankingi z pliku JSON lub importuje stare punkty przy pierwszym starcie"""
    if os.path.exists(PLIK_BAZY):
        with open(PLIK_BAZY, "r", encoding="utf-8") as f:
            dane = json.load(f)
            r1 = {int(k): v for k, v in dane.get("kanal_1", {}).items()}
            r2 = {int(k): v for k, v in dane.get("kanal_2", {}).items()}
            return r1, r2
    else:
        r1 = {int(k): v for k, v in STARE_PUNKTY_KANAL_1.items()}
        r2 = {int(k): v for k, v in STARE_PUNKTY_KANAL_2.items()}
        zapisz_dane(r1, r2)
        return r1, r2

def zapisz_dane(r1, r2):
    """Zapisuje aktualny stan punktów do pliku JSON"""
    dane = {
        "kanal_1": {str(k): v for k, v in r1.items()},
        "kanal_2": {str(k): v for k, v in r2.items()}
    }
    with open(PLIK_BAZY, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4, ensure_ascii=False)

# Inicjalizacja bazy danych na starcie
ranking_kanal_1, ranking_kanal_2 = zaladuj_dane()

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
    # Używamy fetch_channel jeśli get_channel zawiedzie przy starcie bota
    kanal = bot.get_channel(KANAL_RANKINGU_ID)
    if not kanal:
        try:
            kanal = await bot.fetch_channel(KANAL_RANKINGU_ID)
        except Exception:
            print(f"❌ Nie znaleziono kanału o ID {KANAL_RANKINGU_ID}. Sprawdź uprawnienia bota.")
            return

    embed = generuj_ranking_embed(ranking_dict, numer_kanalu)

    # 1. Próba edycji na podstawie pamięci podręcznej bota
    if ranking_messages[numer_kanalu]:
        try:
            msg = await kanal.fetch_message(ranking_messages[numer_kanalu])
            await msg.edit(embed=embed)
            return
        except discord.NotFound:
            ranking_messages[numer_kanalu] = None

    # 2. Próba znalezienia starej tabeli w historii (zapobiega duplikatom po restarcie)
    try:
        async for message in kanal.history(limit=50):
            if message.author == bot.user and message.embeds:
                if message.embeds[0].title == f"🏆 RANKING SS - KANAŁ {numer_kanalu}":
                    ranking_messages[numer_kanalu] = message.id
                    await message.edit(embed=embed)
                    return
    except Exception as e:
        print(f"⚠️ Nie udało się przeszukać historii kanału: {e}")

    # 3. Jeśli nie znaleziono żadnej wiadomości bota, wyślij nową
    nowa_wiadomosc = await kanal.send(embed=embed)
    ranking_messages[numer_kanalu] = nowa_wiadomosc.id

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    print("Oczekiwanie 3 sekundy na pełne załadowanie kanałów...")
    await asyncio.sleep(3)  # Dajemy botu czas na połączenie się z serwerami Discorda
    
    # Wyświetlenie tabel natychmiast po uruchomieniu bota
    await aktualizuj_ranking_na_kanale(ranking_kanal_1, 1)
    await aktualizuj_ranking_na_kanale(ranking_kanal_2, 2)
    print("✅ Tabele rankingowe zostały zainicjalizowane.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # KANAŁ 1 (Nasłuchiwanie zdjęć i aktualizacja na kanale dedykowanym)
    if message.channel.id == KANAL_1_ID and message.attachments:
        dodano_foto = False
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_1[message.author.id] = ranking_kanal_1.get(message.author.id, 0) + 1
                dodano_foto = True
        
        if dodano_foto:
            zapisz_dane(ranking_kanal_1, ranking_kanal_2)
            await aktualizuj_ranking_na_kanale(ranking_kanal_1, 1)

    # KANAŁ 2 (Nasłuchiwanie zdjęć i aktualizacja na kanale dedykowanym)
    elif message.channel.id == KANAL_2_ID and message.attachments:
        dodano_foto = False
        for zalacznik in message.attachments:
            if zalacznik.content_type and zalacznik.content_type.startswith("image/"):
                ranking_kanal_2[message.author.id] = ranking_kanal_2.get(message.author.id, 0) + 1
                dodano_foto = True
                
        if dodano_foto:
            zapisz_dane(ranking_kanal_1, ranking_kanal_2)
            await aktualizuj_ranking_na_kanale(ranking_kanal_2, 2)

    await bot.process_commands(message)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset1(ctx):
    ranking_kanal_1.clear()
    zapisz_dane(ranking_kanal_1, ranking_kanal_2)
    await aktualizuj_ranking_na_kanale(ranking_kanal_1, 1)
    await ctx.send("🗑️ **Ranking 1 na kanale dedykowanym został wyzerowany!**", delete_after=5)

@bot.command()
@commands.has_permissions(administrator=True)
async def reset2(ctx):
    ranking_kanal_2.clear()
    zapisz_dane(ranking_kanal_1, ranking_kanal_2)
    await aktualizuj_ranking_na_kanale(ranking_kanal_2, 2)
    await ctx.send("🗑️ **Ranking 2 na kanale dedykowanym został wyzerowany!**", delete_after=5)

@reset1.error
@reset2.error
async def reset_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Nie masz uprawnień administratora!", delete_after=5)

bot.run(os.environ.get("MOJ_TAJNY_KLUCZ"))
