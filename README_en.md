# HAI-GPT
[中文版本](README.md)

Complete ai assistant function experience entrance:
> python andrew_chat.py

How to experience the web version:
> flask run

This project aims to achieve artificial intelligence with human memory level. On the basis of this memory, the performance of artificial intelligence is further improved. The goals are as follows:
1. The artificial intelligence can pass the Turing test, and it is in various forms of information exchange, including text, voice, video, pictures, etc.
2. The artificial intelligence can control various devices, including but not limited to mobile phones, computers, smart homes, smart vehicles, etc.
3. The artificial intelligence can obtain information through various means, including but not limited to networks, sensors, cameras, microphones, GPS, etc.
4. The artificial intelligence can port the code to any platform and device, including but not limited to mobile phones, computers, smart homes, smart vehicles, etc.
5. The artificial intelligence can continuously improve its abilities through learning and memory, including but not limited to language ability, control ability, information acquisition ability, etc.

This project implements the following functions:

1. Continuous dialogue: Realize continuous dialogue interaction with users.
2. Importance scoring: evaluate and score the importance of the user's dialogue content.
3. Correlation search: Carry out a vector correlation search on the user's dialogue content.
4. Summarize and refine the dialogue content: Summarize and refine the dialogue content between the user and AI in stages.
5. Memory Retrieval: Retrieve memories based on importance, recency and relevance for the next conversation.

2023-06-19 Added:
1. By passing the user instruction statement and method name to chatgpt, let chagpt judge the order of method calls and return json data
2. In theory, a method registration center can be constructed to maintain all the capabilities that chatgpt can call  
3. todo: You can use the dynamic execution of the language to implement chatgpt to learn new skills, and persist the skills as method codes

2023-07-12 Added:
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

2023-07-28 :
1. Support windows, linux, macos system operation
2. Increase the use of Microsoft tts speech synthesis
3. Support command line input chat, and voice can input text at the same time
4. Support input stop to stop voice playback

2023-08-01 :  
Learning and forming non-expressive memory, the primary version, has a low success rate, and it cannot effectively solve the infinite loop problem similar to autoGPT.
But the main idea has been formed, and the follow-up can continue to be optimized.