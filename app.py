from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

#======python的函數庫==========
import tempfile, os
import datetime
from openai import OpenAI
import time
import traceback
#======python的函數庫==========

app = Flask(__name__)
static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# OPENAI API Key初始化設定
# openai.api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    # This is the default and can be omitted
    api_key= os.getenv('OPENAI_API_KEY')
)

SUPPORTED_LANGUAGE_MAP = {
    "th": "泰文",
    "vn": "越南文",
    "tw": "繁體中文",
    "en": "英文",
    "id": "印尼文",
}

def GPT_response(source_language, target_language, text, name):
    format_text = f"幫我把以下文字從{source_language}翻譯成{target_language}:\n{text}"
    # response = openai.Completion.create(
    #     model="gpt-3.5-turbo-instruct",
    #     prompt=format_text,
    #     temperature=0.5,
    #     max_tokens=500
    # )
    response = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": format_text,
                }
            ],
            model="gpt-3.5-turbo",
        )
    print(response)
    # 重組回應
    # format_answer = response["choices"][0]["text"].replace("。", "")
    answer = response.choices[0].message.content.replace("。", "")
    if(name != ''):
        return f"{name}:\n{answer}"
    return answer
    



# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    try:
        country = msg[:5]
        country_list = country.split("-")
        if (
            len(country_list) == 2
            and (source_language := SUPPORTED_LANGUAGE_MAP.get(country_list[0]))
            and (target_language := SUPPORTED_LANGUAGE_MAP.get(country_list[1]))
        ):
            name = ''
            if (hasattr(event.source, "group_id") and getattr(event.source, "group_id")):
                profile = line_bot_api.get_group_member_profile(event.source.group_id, event.source.user_id)
                name = profile.display_name
            GPT_answer = GPT_response(source_language, target_language, msg[6:], name)
            print(GPT_answer)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(GPT_answer))
        else: 
            print('不需要翻譯')
    except:
        print(traceback.format_exc())
        line_bot_api.reply_message(event.reply_token, TextSendMessage('你所使用的OPENAI API key額度可能已經超過，請於後台Log內確認錯誤訊息'))
        

@handler.add(PostbackEvent)
def handle_message(event):
    print(event)

        
import os
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
