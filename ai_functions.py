import uuid
import datetime
import os
import ollama
import json
from pathlib import Path
import numpy as np
from pypdf import PdfReader
from langdetect import detect as ld

if not os.path.isdir("chats/"):
    os.mkdir("chats/")

def _atomic_write_json(path, data):
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    os.replace(tmp_path, path)

chat_file = Path("chats/chats.json")
if not chat_file.exists() or chat_file.stat().st_size == 0:
    _atomic_write_json("chats/chats.json", [])

def _strip_for_model(msgs):
    stripped = []
    for m in msgs:
        stripped.append({
            "role": m.get("role", ""),
            "content": m.get("content", ""),
        })
    return stripped


def ai(chatid, message, files=None, display_content=None, is_new_chat=False):

    if chatid == None:
        chatid = newchat(display_content or message)
    elif not is_new_chat:
        updateDate(chatid)

    msgs = jsonAppend(chatid, 'user', display_content or message, files=files)

    stream = ollama.chat(
        model='mistral',
        messages=_strip_for_model(msgs),
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

    jsonAppend(chatid, 'assistant', answer)

def newchat(msg, return_name=False):
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
    
    chat_name = noLogAi(getNamePrompt).replace('"', '').strip()
    newchat_dict = {
        "uuid": str(uuid.uuid4()),
        "lastEdited": datetime.datetime.now().isoformat(),
        "chatName": chat_name,
        "pinned": False,
    }

    try:
        with open("chats/chats.json", "r", encoding="utf-8") as file:
            chatsjson = json.load(file)
        if not isinstance(chatsjson, list):
            chatsjson = []
    except Exception:
        chatsjson = []

    chatsjson.insert(0, newchat_dict)
    _atomic_write_json("chats/chats.json", chatsjson)

    if return_name:
        return newchat_dict["uuid"], chat_name
    return newchat_dict["uuid"]

def updateDate(uuid):
    try:
        with open("chats/chats.json", "r", encoding="utf-8") as file:
            chats = json.load(file)
        if not isinstance(chats, list):
            return False
    except Exception:
        return False

    for index, chat in enumerate(chats):
        if chat["uuid"] == uuid:
            chat["lastEdited"] = datetime.datetime.now().isoformat()
            chats.pop(index)
            chats.insert(0, chat)
            break
    else:
        return False

    _atomic_write_json("chats/chats.json", chats)
    return True

def jsonAppend(id, usr, msg, files=None):
    if usr not in ("user", "assistant"):
        print("!!! The user must be either 'user' or 'assistant'")
        return 

    newmsg = {'role': usr, 'content': msg}
    if usr == "user" and files:
        newmsg["files"] = files
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
    try:
        os.remove(f"./chats/{chatid}.json")
    except Exception:
        pass

    try:
        with open("chats/chats.json", "r", encoding="utf-8") as file:
            chatsjson = json.load(file)
        if not isinstance(chatsjson, list):
            chatsjson = []
    except Exception:
        chatsjson = []

    chatsjson = [
        chat for chat in chatsjson
        if chat["uuid"] != str(chatid)
    ]

    _atomic_write_json("chats/chats.json", chatsjson)


def noLogAi(message):
    response: ollama.ChatResponse = ollama.chat(model='mistral', messages=[
        {
            'role': 'user',
            'content': message,
        }
    ])
    return(response.message.content) 

def nomic_embed_text(
    file_paths: [str],
    question: str,
    top_k: int = 4,
    words_per_chunk: int = 250,
    overlap: int = 40,
):
    try:
        with open("supported_file_types.json", "r", encoding="utf-8") as file:
            supported_doc_types = json.load(file)
    except Exception:
        supported_doc_types = [".txt", ".py", ".md", ".pdf"]

    all_passages = []
    passages_text = ""

    for file_path in file_paths:
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix == ".pdf":
            reader = PdfReader(path)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        elif suffix in supported_doc_types:
            text = path.read_text(encoding="utf-8", errors="replace")
        else:
            raise ValueError(f"Not supported filetype: {path.suffix}")

        if not text.strip():
            raise ValueError("No text could be extracted from the file.")

        words = text.split()
        step = words_per_chunk - overlap
        if step <= 0:
            raise ValueError("overlap has to be smaller than words_per_chunk.")

        chunks = [
            " ".join(words[start:start + words_per_chunk])
            for start in range(0, len(words), step)
        ]
        chunks = [c for c in chunks if c.strip()]
        if not chunks:
            raise ValueError("No text could be extracted from the file.")

        chunk_embeddings = ollama.embed(
            model="nomic-embed-text",
            input=chunks,
        ).embeddings

        question_embedding = ollama.embed(
            model="nomic-embed-text",
            input=question,
        ).embeddings[0]

        q = np.array(question_embedding)
        scores = []

        for chunk, embedding in zip(chunks, chunk_embeddings):
            vector = np.array(embedding)
            denominator = np.linalg.norm(q) * np.linalg.norm(vector)
            score = float(np.dot(q, vector) / denominator) if denominator else 0.0
            scores.append((score, chunk))

        scores.sort(key=lambda item: item[0], reverse=True)

        passages = [chunk for _, chunk in scores[:top_k]]
        all_passages.append({"path": str(file_path), "passages": passages})

        passages_text += f"{file_path}:\n"
        for passage in passages:
            passages_text += passage + "\n"
        passages_text += "\n"

    try:
        language = ld(question)
    except Exception:
        language = "en"

    sys_prompt = "Answer the question based on the provided document context. If the answer isn't stated there, say so clearly."
    try:
        with open("./lang_based_sys_prompts.json", "r", encoding="utf-8") as file:
            content = json.load(file)
        for i in content:
            if i.get("lang") == language:
                sys_prompt = i.get("nomic-embed-text", sys_prompt)
                break
    except Exception:
        pass

    final_prompt = sys_prompt + "\n\n" + passages_text + "\nQuestion:\n" + question
    return all_passages, final_prompt

#test:
#for text in ai("64c06330-b00d-4ccc-958f-0f1148648048", """i have a bunch of dates like this: 2026-09-19T11:49:25.382158 in a list of chats: [{"uuid": "02b9a957-8c70-45fe-94e2-672060cf0204","lastEdited": "2026-09-19T10:09:52.192774","chatName": "Request for Recommended Books on Machine Learning"},{"uuid": "64c06330-b00d-4ccc-958f-0f1148648048","lastEdited": "2026-09-19T11:47:55.356992","chatName": "Decoding Unreadable Text"},{"uuid": "46e365b6-2daf-468d-b5f4-215a812117a7","lastEdited": "2026-09-19T11:49:25.382158","chatName": "Hello Greeting"},{"uuid": "2247847e-1cb9-4a63-9ee8-741916b7f281","lastEdited": "2026-09-19T11:52:02.140271","chatName": "Create Kindle for Mother"}] so, how do i order them after the date and give an array of the chatNames based on the date. (recently edited chats come first and older chats come next in order) i am working with python"""):
#    print(text, end="", flush=True)
#delChat("bc987e0b-256c-47e0-b7d0-48cade727e7b")
#print(getchatlist())3