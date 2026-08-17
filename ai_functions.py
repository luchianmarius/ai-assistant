import uuid4 from uuid
import datetime

if not os.path.isdir("chats/"):
    os.mkdir("chats/")

if not os.path.isfile("chats/chats.json"):
    with open("chats/chats.json", "x") as file:
        json.dump([], file, indent=4)

def ollama(chatid, message):
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

    self.jsonAppend(chatid, 'assistant', answer)

def jsonAppend(id, usr, msg):
    if usr not in ("user", "assistant"):
        print("!!! The user must be either 'user' or 'assistant'")
        return 

    if id == None:
        id = uuid4()
        with open("chats/chats.json", "w") as file:
            chats = json.load(file)
            newchat = {
                uuid = id,
                last edited = datetime.datetime.now(),
                chat name
            }

    path = f"./chats/{id}.json"
    newmsg = {'role': usr, 'content': msg}
    content = []

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
