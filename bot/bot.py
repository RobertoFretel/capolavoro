from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CallbackQueryHandler, CommandHandler, MessageHandler, filters
import re, requests, asyncio, os, aiohttp, json
from comandi.login import provaLogin
from comandi.notificatore import cercaAggiornamenti

TOKEN = "7047670907:AAEeAhxNg4PPg_BRkxeVwsifhGkfyHQBEEM"
regex = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Za-z]{2,})+"
NOTIFICHE = 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if not os.path.exists(f"./database/{chat.id}.json"):
        with open(f"./database/{chat.id}.json", "w") as file:
            file.write("")
            file.close()

    await context.bot.send_message(
        chat_id = chat.id,
        text = "Ciaooo 👋, sono il tuo bot per la scuola! \n Fa /login per sbloccare tutte le funzionalità"
    )

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global loginHandler

    if "token" not in context.user_data:
        await update.message.reply_text(
            text = "✉️ Inserisci l'email:"
        )

        loginHandler = MessageHandler(filters.TEXT & ~filters.COMMAND, promptForLogin)
        bot.add_handler(loginHandler)
    else:
        await update.message.reply_text(
            text = "Hai già effettuato il login con successo!"
        )

async def promptForLogin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    messaggio = update.message.text

    # chiedi la password e passali su un array credenziali

    if "email" not in context.user_data:
        if bool(re.fullmatch(regex, messaggio)):
            context.user_data["email"] = messaggio
            await update.message.reply_text(
                text = "🔑 Inserisci la password:"
            )

        else:
            await context.bot.send_message(
                chat_id = chat.id,
                text = "❌ Email non valida, riprova:"
            )
    elif "password" not in context.user_data: 
        context.user_data["password"] = messaggio
        await update.message.reply_text(
            text = "Credenziali salvate con successo!"
        )

        risposta = provaLogin(context.user_data["email"], context.user_data["password"])
        if risposta["success"]:
            await update.message.reply_text(
                text = "☑️ Login avvenuto con successo!"
            )

            context.user_data["token"] = risposta["token"]
            context.user_data["stID"] = risposta["studentID"]
            
            studentId, token = context.user_data["stID"], context.user_data["token"] 

            # carico tutti i voti adesso, perche poi è la fine
            url = f"https://web.spaggiari.eu/rest/v1/students/{studentId}/grades"
            headers = {
                "User-Agent": "CVVS/std/4.1.7 Android/10",
                "Z-Dev-Apikey": "Tg1NWEwNGIgIC0K",
                "ContentsDiary-Type": "application/json",
                "Z-Auth-Token": token
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers = headers) as risposta:
                    voti = await risposta.json()
                    voti = sorted(voti["grades"], key = lambda x: x["evtDate"])
                    voti = [num for num in reversed(voti)]

                    with open(f"./database/{update.effective_chat.id}.json", "w") as file:
                        file.write(json.dumps(voti, indent = 4))
                        file.close()

                await session.close()

            await mostraInfo(update, context)
            asyncio.create_task(cercaAggiornamenti(update, context))

        else:
            await update.message.reply_text(
                text = "❌ riprova il login, " + risposta["message"]
            )

            context.user_data.clear()

        bot.remove_handler(loginHandler)
        
async def mostraInfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    studentId = context.user_data["stID"]
    url = f"https://web.spaggiari.eu/rest/v1/students/{studentId}/card"

    infoRisposta = requests.get(url, headers = {
        "User-Agent": "CVVS/std/4.1.7 Android/10",
        "Z-Dev-Apikey": "Tg1NWEwNGIgIC0K",
        "ContentsDiary-Type": "application/json",
        "Z-Auth-Token": context.user_data["token"]
    })

    info = infoRisposta.json()["card"]

    await update.message.reply_text(
        text = 
f"""
<b>Nome</b>: <code>{info["firstName"].title()} {info["lastName"].title()}</code>
<b>CF</b>: <code>{info["fiscalCode"]}</code>
<b>Luogo</b>: <em>{info["schCity"].title()} ({info["schProv"]})</em>
""",
    parse_mode = "HTML"
    )

async def callbackBottoni(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Arrivato il tocco")
    query = update.callback_query
    voti_materia = []

    async with open(f"./database/{update.effective_chat.id}.json", "r") as file:
        database: list = json.loads(file.read())
        voti_materia = [voto for voto in database if voto.get("subjectDesc") == query.data]

        # mo che chai i voti di quella materia fa un po tu
        
        await context.bot.send_message(
            chat_id = update.effective_chat.id,
            text = str(len(voti_materia))
        )

        file.close()

    await query.answer(
        text=f"Tocca vede la media di {query.data}"
    )

if __name__ == '__main__':

    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler('start', start))
    bot.add_handler(CommandHandler('login', login))
    bot.add_handler(CallbackQueryHandler(callbackBottoni))

    bot.run_polling()
    