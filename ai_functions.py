import uuid
import datetime
import os
import ollama
import json
from pathlib import Path

if not os.path.isdir("chats/"):
    os.mkdir("chats/")

chat_file = Path("chats/chats.json")
if not chat_file.exists() or chat_file.stat().st_size == 0:
    with open("chats/chats.json", "x", encoding="utf-8") as file:
        json.dump([], file, indent=4)

def ai(chatid, message):

    if chatid == None:
        chatid = newchat(message)
    else:
        updateDate(chatid)

    msgs = jsonAppend(chatid, 'user', message)

    stream = ollama.chat(
        model='mistral',
        messages=msgs,
        stream=True,
    )
    
    answer = ""

    for chunk in stream:
        if isinstance(chunk, dict):
            text = chunk["message"]["content"]
        else:
            text = chunk.message.content

        answer += text
        yield text
        """
            #in the other file, you can do this:
            import main_functions as mf
            for text in mf.ai().ollama(mf.newId(), "why is the sky blue?"):
                print(text, end='', flush=True)
            #this will take the stream and print it (but you should use text to speech)
        """

    jsonAppend(chatid, 'assistant', answer)

def newchat(msg):
    getNamePrompt = f"""
        Create a short, clear title for the users message.

        Rules:
        Reply with only the title.
        Use 2 to 5 words.
        Summarize the main topic or intent.
        Keep important keywords.
        Use title case.
        No quotes, punctuation, explanations, or extra text.

        User message:
        {msg}
    """
    
    newchat = {
        "uuid": str(uuid.uuid4()),
        "lastEdited": datetime.datetime.now().isoformat(),
        "chatName": noLogAi(getNamePrompt).replace('"', '').strip()
    }

    with open("chats/chats.json", "r", encoding="utf-8") as file:
        chatsjson = json.load(file)

    chatsjson.insert(0, newchat)

    with open("chats/chats.json", "w", encoding="utf-8") as file:
        json.dump(chatsjson, file, indent=4)

    return newchat["uuid"]

def updateDate(uuid):
    with open("chats/chats.json", "r", encoding="utf-8") as file:
        chats = json.load(file)

    for index, chat in enumerate(chats):
        if chat["uuid"] == uuid:
            chat["lastEdited"] = datetime.datetime.now().isoformat()
            chats.pop(index)
            chats.insert(0, chat)
            break
    else:
        return False

    with open("chats/chats.json", "w", encoding="utf-8") as file:
        json.dump(chats, file, indent=4)
    return True

def jsonAppend(id, usr, msg):
    if usr not in ("user", "assistant"):
        print("!!! The user must be either 'user' or 'assistant'")
        return 

    
    newmsg = {'role': usr, 'content': msg}
    content = []

    path = f"./chats/{id}.json"
    
    if not os.path.isfile(path):    
        with open(path, "x", encoding="utf-8") as file:
            content = [newmsg]
            json.dump(content, file, indent=4)
    else:
        with open(path, "r", encoding="utf-8") as file:
            content = json.load(file)
        content.append(newmsg)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(content, file, indent=4)
    
    return content

def getchatlist():
    with open("chats/chats.json", "r", encoding="utf-8") as file:
        content = json.load(file)

        chats = []
        for chat in content:
            chats.append(chat["chatName"])
        return chats

def delChat(chatid):
    os.remove(f"./chats/{chatid}.json")

    with open("chats/chats.json", "r", encoding="utf-8") as file:
        chatsjson = json.load(file)

    chatsjson = [
        chat for chat in chatsjson
        if chat["uuid"] != str(chatid)
    ]

    with open("chats/chats.json", "w", encoding="utf-8") as file:
        json.dump(chatsjson, file, indent=4)


def noLogAi(message):
    response: ollama.ChatResponse = ollama.chat(model='mistral', messages=[
        {
            'role': 'user',
            'content': message,
        }
    ])
    return(response.message.content)    

#test:
#for text in ai("64c06330-b00d-4ccc-958f-0f1148648048", """i have a bunch of dates like this: 2026-09-19T11:49:25.382158 in a list of chats: [{"uuid": "02b9a957-8c70-45fe-94e2-672060cf0204","lastEdited": "2026-09-19T10:09:52.192774","chatName": "Request for Recommended Books on Machine Learning"},{"uuid": "64c06330-b00d-4ccc-958f-0f1148648048","lastEdited": "2026-09-19T11:47:55.356992","chatName": "Decoding Unreadable Text"},{"uuid": "46e365b6-2daf-468d-b5f4-215a812117a7","lastEdited": "2026-09-19T11:49:25.382158","chatName": "Hello Greeting"},{"uuid": "2247847e-1cb9-4a63-9ee8-741916b7f281","lastEdited": "2026-09-19T11:52:02.140271","chatName": "Create Kindle for Mother"}] so, how do i order them after the date and give an array of the chatNames based on the date. (recently edited chats come first and older chats come next in order) i am working with python"""):
#    print(text, end="", flush=True)
#delChat("bc987e0b-256c-47e0-b7d0-48cade727e7b")
#print(getchatlist())3