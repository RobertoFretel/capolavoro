import requests, re

def provaLogin(email: str, password: str):
    url = "https://web.spaggiari.eu/rest/v1/auth/login"
    payload = {
        "ident": "",
        "uid": email,
        "pass": password
    }

    response = requests.post(url, json = payload, headers = {
        "User-Agent": "CVVS/std/4.1.7 Android/10",
        "Z-Dev-Apikey": "Tg1NWEwNGIgIC0K",
        "ContentsDiary-Type": "application/json",
        "Content-Type": "application/json"
    })

    try:
        user_response = response.json()
        ident: str = user_response["ident"]
        return {
            "success": True,
            "token": user_response["token"],
            "studentID": re.sub(r"\D", "", ident)
        }
    except:
        user_response = response.json()
        return {
            "success": False,
            "message": user_response["info"]
        }

provaLogin("robertofretel20@gmail.com", "ROWSAfretel20!")