import asyncio, aiohttp, json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def subtract_dictionaries_list(list1, list2):
    # Crea un set di tuple (tutte_le_chiavi, valori) per ciascun dizionario in list2
    set2 = {(tuple(dct.items())) for dct in list2}
    # Filtra i dizionari in list1 che non sono presenti in set2
    result_list = [dct for dct in list1 if tuple(dct.items()) not in set2]
    return result_list

async def cercaAggiornamenti(update: Update, context: ContextTypes.DEFAULT_TYPE):
    aggiornamento = True
    counter = 0

    token = context.user_data["token"]
    studentId = context.user_data["stID"]

    url = f"https://web.spaggiari.eu/rest/v1/students/{studentId}/grades"
    headers = {
        "User-Agent": "CVVS/std/4.1.7 Android/10",
        "Z-Dev-Apikey": "Tg1NWEwNGIgIC0K",
        "ContentsDiary-Type": "application/json",
        "Z-Auth-Token": token
    }

    global voti, database
    while aggiornamento:
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers = headers) as risposta:
                voti = await risposta.json()
                voti = sorted(voti["grades"], key = lambda x: x["evtDate"])
                voti = [num for num in reversed(voti)]

            with open(f"./database/{update.effective_chat.id}.json", "r") as db:
                database = json.loads(db.read())
            
            await session.close()

        if database == voti:
            print("Nessun aggiornamento..")
        else:
            voti_diversi = await subtract_dictionaries_list(voti, database)
            print(voti_diversi)
            
            for ultimo_voto in voti_diversi:
            # mo qui dovrei fare che mi prende il nuovo voto e mi da le info del caso
            # ultimo_voto = voti[0]
                materia = ultimo_voto["subjectDesc"]
                valutazione = ultimo_voto["decimalValue"]
                periodo = ultimo_voto["periodDesc"]
                tipo = ultimo_voto["componentDesc"]

                bottone = InlineKeyboardButton("Vedi la media di questa materia!", callback_data = f"{materia}")

                await update.message.reply_text(
                    text = f"""
<b>Nuovo voto di</b>: <code>{materia}</code>
Hai preso un bellissimo: <span class='tg-spoiler'> &gt; {valutazione} &lt; </span>
<b>Periodo</b>: <em>{periodo}</em> 
<b>Tipologia</b>: <em>{tipo}</em> 
""",
                    parse_mode = "HTML",
                    reply_markup = InlineKeyboardMarkup([[bottone]])
                )



                if ultimo_voto["color"] == "green":
                    await update.message.reply_video_note(
                        video_note = open("gg.gif.mp4", "rb")
                    )
                else:
                    await update.message.reply_video_note(
                        video_note = open("spiaze.gif.mp4", "rb")
                    )                

            with open(f"./database/{update.effective_chat.id}.json", "w") as file:
                file.write(json.dumps(voti, indent = 4))
                file.close()
            
            counter = 0

        await asyncio.sleep(10)