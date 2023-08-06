# HAI-GPT

[![](https://camo.githubusercontent.com/15a53d5ec5d896319068168a27da0203156bbdb9/68747470733a2f2f6a617977636a6c6f76652e6769746875622e696f2f73622f6c616e672f656e676c6973682e737667)](README_en.md)
[![](https://camo.githubusercontent.com/cb8cb80af654f3dae14a4aa62e44bf62f16953d6/68747470733a2f2f6a617977636a6c6f76652e6769746875622e696f2f73622f6c616e672f6368696e6573652e737667)](README.md)  
**This project is to realize its own artificial intelligence assistant on the basis of large models including openai
GPT, especially thanks to the emergence of these large models, which make these functions possible.**

## Project Deployment and Running

### 1. Download the project code

```
git clone https://github.com/hambuger/HAI-GPT.git
```

### 2. Install dependencies

It is recommended to have GPU support with nvcc version 11.7 or 11.8.

```
pip install -r requirements.txt
```

### 3. Install required databases

3.1 Since this project requires storing long-term memories and using advanced features of Elasticsearch for memory
retrieval, you need to install Elasticsearch. Please refer to the documentation to install Elasticsearch on your system.
After installation, create an index named "lang_chat_content" in Elasticsearch using the provided mapping.

```
PUT /lang_chat_content
{
    "mappings": {
        "properties": {
            "content_creation_time": {
                "type": "date"
            },
            "content_creator": {
                "type": "keyword"
            },
            "content_importance": {
                "type": "float"
            },
            "content_last_access_time": {
                "type": "date"
            },
            "content_leaf_depth": {
                "type": "integer"
            },
            "content_node_id": {
                "type": "keyword"
            },
            "content_owner": {
                "type": "keyword"
            },
            "content_type": {
                "type": "keyword"
            },
            "content_vector": {
                "type": "dense_vector",
                "dims": 1536
            },
            "creator_ip": {
                "type": "keyword"
            },
            "depend_node_id": {
                "type": "keyword"
            },
            "generated_content": {
                "type": "text",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                },
                "analyzer": "ik_max_word"
            },
            "parent_id": {
                "type": "keyword"
            }
        }
    }
}
```

3.2 The project also requires Redis to implement some locking mechanisms.   
Additionally, it uses a Redis queue for key rotation due to the limited number of requests for the OpenAI single API
key.  
Install Redis on your system and create a queue named "api_keys" in Redis.

```
lpush api_keys sk-xx1 sk-xx2 sk-xx3
```

### 4. Configure program variables

Create a .env file in the project root directory and set the following environment variables:

```
ES_HOST=             # Elasticsearch address
REDIS_HOST=localhost # Redis address
REDIS_PORT=6379      # Redis port
ENCODING_FOR_MODEL=gpt-3.5-turbo  # Model for calculating OpenAI tokens
MY_NAME=             # User name
USE_IMPORTANT_SCORE=True         # Whether to use chat history importance scoring
GET_INVOKE_METHOD_MODEL=gpt-3.5-turbo-16k  # Model used for invoking steps
GET_METHOD_ARGUMENTS_MODEL=gpt-3.5-turbo-0613  # Model used for getting method arguments
DEFAULT_CHAT_MODEL=gpt-3.5-turbo # Default chat model
ASR_MODEL=           # ASR model, BAIDU or WHISPER
WHISPER_MODEL_KEY=   # API key for using Whisper mode
OS_NAME=windows      # Current system name, windows, linux, macos
PHONE_OS_NAME=android # Phone system name, android, ios
WOLFRAMALPHA_ID=     # WolframAlpha API key
KWS_MODEL_DIR=       # KWS model directory
SERPER_API_KEY=      # Serper API key
OPEN_WEATHER_MAP_KEY= # OpenWeatherMap API key
PICOVOICE_ACCESS_KEY= # Access key required for KWS tool
```

### 5. Run the program

```       
python andrew_chat.py
```

### 6. Experience the features

The program supports multiple interaction modes, such as voice, text, and images. To initiate a voice conversation, use
the wake-up word "Andrew." Once woken up, Andrew will listen to the user's voice until they stop speaking for 30 seconds
or say "goodbye," and then the voice conversation will end until the next wake-up. You can also stop Andrew's current
voice playback by typing "stop" in the command line. The program supports voice-only conversations, voice + command-line
text conversations, and standalone command-line text conversations.

## Project Overview

This project implements the following features:

1. Multiple interaction modes, including voice, text, and image.
2. Support for Windows, Linux, and macOS.
3. Support for KWS voice wake-up, camera object detection, and mobile device control.
4. Long-term memory with memory retrieval during conversations.
5. Multiple information retrieval methods, such as Google, WolframAlpha, Serper, and OpenWeatherMap.
6. Continuous learning capabilities, forming persistent program memory.

### 2023-08-06
The second version of the learning logic provides GPT with some capabilities such as Google, pip install, run python and
save code, allowing it to decide the next call based on the output of the previous step.
And Google yourself to fix the errors encountered in the study, and finally produce callable code.

### 2023-08-01
Learning and forming non-expressive memory, the primary version, has a low success rate, and it cannot effectively solve
the infinite loop problem similar to autoGPT.
But the main idea has been formed, and the follow-up can continue to be optimized.

### 2023-07-28

1. Support windows, linux, macos system operation
2. Increase the use of Microsoft tts speech synthesis
3. Support command line input chat, and voice can input text at the same time
4. Support input stop to stop voice playback

### 2023-07-12

1. Python code execution function
2. Voice kws function and use of Baidu Feijiang ASR
3. Use different tts according to different systems
4. Call the hugging face open source model to realize image recognition and question answering
5. Let gpt decide whether to call the camera to take pictures and identify
6. Use YouTube to play the video requested by the user
7. Call Google to query the information the user needs
8. Check the weather in various places
9. Call the mobile phone to make a call through airtest
10. Depending on the system to decide how to call music playback
11. query using WolframAlpha

### 2023-06-19

1. By passing the user instruction statement and method name to chatgpt, let chagpt judge the order of method calls and
   return json data
2. In theory, a method registration center can be constructed to maintain all the capabilities that chatgpt can call
3. todo: You can use the dynamic execution of the language to implement chatgpt to learn new skills, and persist the
   skills as method codes