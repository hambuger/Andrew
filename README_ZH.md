# Andrew
[![](https://camo.githubusercontent.com/15a53d5ec5d896319068168a27da0203156bbdb9/68747470733a2f2f6a617977636a6c6f76652e6769746875622e696f2f73622f6c616e672f656e676c6973682e737667)](README.md)  
**本项目是在包含openai gpt等大模型的基础上实现自己的人工智能助手，特别感谢这些大模型，使这些功能得以可能出现。**
## 项目部署运行
### 1.下载项目代码
```
git clone https://github.com/hambuger/Andrew.git  
```
### 2.安装依赖项  
其中最好支持GPU，nvcc版本11.7或者11.8最好  
```
pip install -r requirements.txt  
```

### 3.安装需要的数据库  
#### 3.1 安装es数据库 
由于本项目需要存储长期记忆，并且需要使用一些es的高级功能来做记忆检索，所以需要安装es数据库。
具体安装es自行Google，安装完成后，需要在es中创建一个名为lang_chat_content的索引，具体方法如下：
```
PUT /lang_chat_content

{
    "mappings":{
        "properties":{
            "content_creation_time":{
                "type":"date"
            },
            "content_creator":{
                "type":"keyword"
            },
            "content_importance":{
                "type":"float"
            },
            "content_last_access_time":{
                "type":"date"
            },
            "content_leaf_depth":{
                "type":"integer"
            },
            "content_node_id":{
                "type":"keyword"
            },
            "content_owner":{
                "type":"keyword"
            },
            "content_type":{
                "type":"keyword"
            },
            "content_vector":{
                "type":"dense_vector",
                "dims":1536
            },
            "creator_ip":{
                "type":"keyword"
            },
            "depend_node_id":{
                "type":"keyword"
            },
            "generated_content":{
                "type":"text",
                "fields":{
                    "keyword":{
                        "type":"keyword",
                        "ignore_above":256
                    }
                },
                "analyzer":"ik_max_word"
            },
            "parent_id":{
                "type":"keyword"
            }
        }
    }
}
```

#### 3.2 安装Redis数据库 
项目中需要使用Redis来做一些锁。  
还有我使用的openai的单个api_key是有3 times/minute的限制的，所以需要使用Redis队列来做一个轮询key机制。
具体安装Redis自行Google，安装完成后，需要在Redis中创建一个名为api_keys的队列，具体方法如下：
```
lpush api_keys sk-xx1 sk-xx2 sk-xx3
```


### 4.配置程序变量  
在项目根目录下创建.env文件，内容如下：
```
ES_HOST=   # es的地址  
REDIS_HOST=localhost  # redis的地址   
REDIS_PORT=6379 # redis的端口  
ENCODING_FOR_MODEL=gpt-3.5-turbo # 计算openai token使用的模型  
MY_NAME= #用户名  
USE_IMPORTANT_SCORE=True #是否使用对话记录重要性打分  
GET_INVOKE_METHOD_MODEL=gpt-3.5-turbo-16k  # 决定调用步骤时使用的模型  
GET_METHOD_ARGUMENTS_MODEL=gpt-3.5-turbo-0613  # 获取调用方法的参数时使用的模型  
DEFAULT_CHAT_MODEL=gpt-3.5-turbo # 默认的聊天模型  
ASR_MODEL= # asr模型  BAIDU 或者 WHISPER  
WHISPER_MODEL_KEY= # 当使用whisper模式时，使用的api key  
OS_NAME=windows # 当前系统名称，windows,linux,macos  
PHONE_OS_NAME=android # 手机系统名称，android,ios  
WOLFRAMALPHA_ID= # wolframalpha api key  
KWS_MODEL_DIR=  # kws模型目录  
SERPER_API_KEY= # serper api key  
OPEN_WEATHER_MAP_KEY= # open weather map api key  
PICOVOICE_ACCESS_KEY= # kws工具使用需要的access key
```

### 5.运行程序
```
python andrew_chat.py
```

### 6.体验功能  
语音交流，唤醒词为“安德鲁”，“安德鲁”不必是一句话的开头，只要包含“安德鲁”就可以。  
唤醒后，会自动听取用户语音，直到用户停止说话30s,或者用户说“再见”，安德鲁会结束语音对话，直到下一次唤醒。    
命令行输入stop,可终止安德鲁的当前语音播放。    
支持语音对话，语音+命令行文本对话， 单独命令行文本对话。

## 项目介绍
本项目实现了以下功能：

1. 具有多种交互方式，如语音，文本，图像
2. 支持Windows，Linux，MacOS
3. 支持kws语音唤醒，摄像头物体检测，手机端设备控制
4. 具有长期记忆，并在对话中检索历史记忆
5. 支持多种信息获取方式，如Google，WolframAlpha，Serper，OpenWeatherMap
6. 具有持续学习能力，并形成持久程序记忆

## 版本历史

### 2023-08-06

- 新增功能：...
- 修复问题：...
- 改进：第二版的学习逻辑，提供给GPT一些能力如Google，pip install, run python和save
  code,让它自己根据上一步的输出来具体决定下一步的调用，  
  并且自己Google来修复学习中遇到的错误，最终产出可调用的代码。
- todo：...

### 2023-08-01

- 新增功能：学习并形成非表述记忆，初级版本，成功率较低，而且还不能有效解决类似autoGPT的死循环问题。
  但是主要思路已经形成，后续可以继续优化。
- 修复问题：...
- 改进：...
- todo：...

### 2023-07-28

- 新增功能：  
  1.支持windows,linux,macos系统运行  
  2.增加使用微软tts语音合成  
  3.支持命令行输入聊天，并且可以语音同时输入文本  
  4.支持输入stop停止语音播放
- 修复问题：...
- 改进：...
- todo：...

### 2023-07-12

- 新增功能：  
  1.python代码执行功能  
  2.语音kws功能以及使用百度飞浆ASR  
  3.根据系统不同使用不同的tts  
  4.调用hugging face开源模型实现图片识别并问答  
  5.让gpt决定是否调用摄像头来拍照识别  
  6.使用YouTube播放用户要求的视频  
  7.调用Google查询用户需要信息  
  8.查询各地天气  
  9.通过airtest实现调用手机拨打电话  
  10.根据系统不同来决定调用音乐播放方式  
  11.使用WolframAlpha查询
- 修复问题：...
- 改进：...
- todo：...

### 2023-06-19

- 新增功能：  
  1.通过将用户指令语句和方法名传递给chatgpt，让chagpt判断方法调用顺序并返回json数据
- 修复问题：...
- 改进：...
- todo：  
  1.理论上可以构造一个方法注册中心，维护所有chatgpt可以调用的能力   
  2.可以使用语言的动态执行实现chatgpt学习新技能，并将技能持久化为方法代码