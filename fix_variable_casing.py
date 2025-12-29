
import os
import re

def process_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Fix Attribute Access
    # callback_query.Message -> callback_query.message
    content = content.replace("callback_query.Message", "callback_query.message")
    
    # 2. Fix Function Signatures (simple regex)
    # async def name(Client, Message): -> (client, message):
    # This is rough but effective for this codebase's style
    content = content.replace("(Client, Message):", "(client, message):")
    content = content.replace("(Client, callback_query):", "(client, callback_query):")
    content = content.replace("(Client, m):", "(client, m):")
    
    # 3. Fix Variable Usage 
    # await Client. -> await client.
    content = content.replace("await Client.", "await client.")
    # Client.get_chat -> client.get_chat
    # But ONLY if it's the instance. How to tell?
    # Usually Class method usage is rare except for decorators.
    # Decorator: @Client.on_message -> Keep Title.
    
    # Let's simple check widely used instance methods
    instance_methods = ["get_chat", "send_message", "send_photo", "send_document", "ask", "download_media"]
    for m in instance_methods:
        content = content.replace(f"Client.{m}", f"client.{m}")

    # Message.reply -> message.reply
    # Message.edit -> message.edit
    # Message.command -> message.command
    # Message.from_user -> message.from_user
    # Message.text -> message.text
    # Message.chat -> message.chat
    msg_attrs = ["reply", "edit", "command", "from_user", "text", "chat", "document", "photo", "sticker", "video", "caption", "id"]
    for m in msg_attrs:
        content = content.replace(f"Message.{m}", f"message.{m}")
    
    # Message.reply_text -> message.reply_text 
    content = content.replace("Message.reply_text", "message.reply_text")

    # Fix argument usage in body
    # "if Client:" -> "if client:"
    # hard to regex safely.
    # But usually "client" is passed as 1st arg. 
    
    
    if content: # Always write for now to be safe, or compare with read
         with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
         print(f"Fixed Variables: {filepath}")

def main():
    root_dir = r"c:\Users\abhin\Downloads\MANGA-BOT--main\MANGA-BOT--main"
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if ".antigravity" in dirpath: continue
        for filename in filenames:
            if filename.endswith(".py"):
                 if filename == "repair_font.py" or filename == "fix_variable_casing.py": continue
                 process_file(os.path.join(dirpath, filename))

if __name__ == "__main__":
    main()
