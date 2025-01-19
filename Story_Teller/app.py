import sys
import configparser

# Azure Speech
import azure.cognitiveservices.speech as speechsdk
import librosa

# Azure OpenAI
import os
from openai import AzureOpenAI

from flask import Flask, request, abort
from linebot.v3 import (
    WebhookHandler
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    AudioMessage,
)

#Config Parser
config = configparser.ConfigParser()
config.read('config.ini')

# Azure OpenAI Key
client = AzureOpenAI(
    api_key=config["AzureOpenAI"]["KEY"],
    api_version=config["AzureOpenAI"]["VERSION"],
    azure_endpoint=config["AzureOpenAI"]["BASE"],
)

# Azure Speech Settings
speech_config = speechsdk.SpeechConfig(
    subscription=config["AzureSpeech"]["SPEECH_KEY"],
    region=config["AzureSpeech"]["SPEECH_REGION"],
)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
UPLOAD_FOLDER = "static"

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

channel_access_token = config['Line']['CHANNEL_ACCESS_TOKEN']
channel_secret = config['Line']['CHANNEL_SECRET']
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(
    access_token=channel_access_token
)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    azure_openai_result = azure_openai(event.message.text)
    audio_duration = azure_speech(azure_openai_result)
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    TextMessage(text=azure_openai_result),
                    AudioMessage(
                        originalContentUrl=f"{config['Deploy']['CURRENT_WEBSITE']}/static/outputaudio.wav",
                        duration=audio_duration,
                    )
                ],
            )
        )

def azure_openai(user_input):

    role_description = "你是一個說故事大師，你說的故事非常有畫面感。"
    custom_user_input = f"請用這個關鍵字:{user_input}，以繁體中文撰寫一個低於300字的故事。"

    message_text = [
        {
            "role": "system",
            "content": role_description,
        },
        {"role": "user", "content": custom_user_input},
    ]

    # message_text[0]["content"] += "你是一個人工智慧助理, "
    # message_text[0]["content"] += "請一律用繁體中文回答。"

    completion = client.chat.completions.create(
        model=config["AzureOpenAI"]["DEPLOYMENT_NAME"],
        messages=message_text,
        max_tokens=800,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None,
    )
    print(completion)
    return completion.choices[0].message.content


def azure_speech(openai_output):
    # The language of the voice that speaks.
    speech_config.speech_synthesis_voice_name = "zh-TW-YunJheNeural"
    file_name = "outputaudio.wav"
    file_config = speechsdk.audio.AudioOutputConfig(filename="static/" + file_name)
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=file_config
    )

    # Receives a text from console input and synthesizes it to wave file.
    result = speech_synthesizer.speak_text_async(openai_output).get()
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(
            "Speech synthesized for text [{}], and the audio was saved to [{}]".format(
                openai_output, file_name
            )
        )
        audio_duration = round(
            librosa.get_duration(path="static/outputaudio.wav") * 1000
        )
        print(audio_duration)
        return audio_duration

    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))

if __name__ == "__main__":
    app.run()