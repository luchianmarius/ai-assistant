import uuid 
import datetime
import os 
import ollama
import json

if not os.path.isdir("chats/"):
    os.mkdir("chats/")

chatsnewlist = []
if not os.path.isfile("chats/chats.json"):
    with open("chats/chats.json", "x") as file:
        json.dump([], file, indent=4)

def ai(chatid, message):
    msgs = jsonAppend(chatid, 'user', message)

    stream = ollama.chat(
        model='mistral',
        messages=msgs,
        stream=True,
    )
    
    answer = ""

    for chunk in stream:
        text = chunk['message']['content']
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
    return

def jsonAppend(id, usr, msg):
    if usr not in ("user", "assistant"):
        print("!!! The user must be either 'user' or 'assistant'")
        return 

    
    newmsg = {'role': usr, 'content': msg}
    content = []

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

    if id == None:
        id = uuid.uuid4()
        name = noLogAi(getNamePrompt)

        newchat = {
            "uuid": str(id),
            "lastEdited": datetime.datetime.now().isoformat(),
            "chatName": name
        }

        with open("chats/chats.json", "r") as file:
            chatsjson = json.load(file)

        chatsjson.append(newchat)

        with open("chats/chats.json", "w") as file:
            json.dump(chatsjson, file, indent=4)

    path = f"./chats/{id}.json"
    
    if not os.path.isfile(path):    
        with open(path, "x") as file:
            content = [newmsg]
            json.dump(content, file, indent=4)
    else:
        with open(path, "r") as file:
            content = json.load(file)
        content.append(newmsg)

        with open(path, "w") as file:
            json.dump(content, file, indent=4)
    return content

def delChat(chatid):
    os.remove(f"./chats/{chatid}.json")

    with open("chats/chats.json", "r") as file:
        chatsjson = json.load(file)

    chatsjson = [
        chat for chat in chatsjson
        if chat["uuid"] != str(chatid)
    ]

    with open("chats/chats.json", "w") as file:
        json.dump(chatsjson, file, indent=4)


def noLogAi(message):
    response: ollama.ChatResponse = ollama.chat(model='mistral', messages=[
        {
            'role': 'user',
            'content': message,
        },
    ])
    return(response.message.content)

#test:
#for text in ai(None, "explain to me the culture, food and everything else about moldova"):
#    print(text, end="", flush=True)
#delChat("bc987e0b-256c-47e0-b7d0-48cade727e7b")