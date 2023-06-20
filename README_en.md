# HAI-GPT
[中文版本](README.md)
## How to Use This Project
On a CentOS environment, run the project by executing the following command:

```bash
./run_flask.sh
````

Project Objective
This project aims to create an artificial intelligence with human-level memory capabilities. The goal is to improve the performance of artificial intelligence based on this memory.

Implemented Features
This project has implemented the following features:

Continuous dialogue: Implemented continuous dialogue interaction with users.  
Importance scoring: Evaluate and score the importance of users' dialogue content.  
Relevance search: Conduct vector relevance search on users' dialogue content.  
Dialogue content summarization and refinement: Periodically summarize and refine the dialogue content between the user and the AI.  
Memory retrieval: Retrieve memories based on importance, recency, and relevance for future dialogues.  

Additions on 2023-06-19:

By passing user command sentences and method names to chatgpt, chatgpt can determine the method call order and return JSON data.  
In theory, a method registration center can be constructed to maintain all capabilities that chatgpt can call.  
TODO: Use dynamic language execution to enable chatgpt to learn new skills and persist these skills as method codes. (Optimize the above MD file to support both Chinese and English and translate it into an English version.)
