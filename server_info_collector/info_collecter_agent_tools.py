info_collector_agent_tools = [{
        "type": "function",
        "name": "read_memory",
        "description": """Call this tool if you need past conversation history to answer the user.
        Use it when:
        - user says 'remember', 'earlier', 'before', 'last time', 'we discussed'
        - the current message references something you have no context for
        - you feel like you're missing background to give a good answer
        Do NOT call it if the current conversation already has enough context.
        
        When you call this, the full conversation history will be injected and 
        your request will be automatically resent with that context. 
        You do not need to ask the user for anything — just call this tool and wait.
        Only inlcude tool outputs if you need any tool output read_memory tool output history will not be given
        """,
        "parameters": {
            "type": "object",
            "properties": {
                 "include_tool_outputs":{
                      "type":"boolean",
                      "description":"If true, the tool will include the outputs of any tools that were called in use it only if needed to answer the user, otherwise set it to false THIS DOES NOT RETURN READ_MEMORY TOOL OUTPUTS, it only returns the tool outputs of other tools that were called in the conversation history"
                 }
            }   # no params needed, just a trigger
        }
    },{
        "type": "function",
        "name": "search_web",
        "description": """Call this tool if you need to search for information from the web.
        Use it when:
        - user asks about current events, news, or general knowledge or something that is not common knowledge
        - if the answer requires specific information that is not common knowledge or may have changed since your training data
        - if your answer depends on the date and time and the current information can change with date and time
        When the answer depends on current or external information, use this tool.
        If uncertain whether your internal knowledge is sufficient, prefer using this tool.
        re-call the tool if you feel u need to search more or if you want to call a different query do that as well

        The tool returns summaries and positions for matching results.
        If additional detail is needed, call `crawl_result` with the relevant result position.
        You may call `crawl_result` for multiple results if necessary.
        Please note that crawl_result is not there so just inform the user what all website links you want to search on
        """,
        "parameters": {
            "type": "object",
            "properties": {
                 "queries":{
                      "type":"array",
                      "items":{
                          "type":"string"
                      },
                      "description":"One or more search queries to execute.Provide multiple queries when broadening the search or investigating different aspects of a topic. If multiple independent searches would improve the answer, include them all in a single call instead of making separate calls."
                 }
            }   # no params needed, just a trigger
        }
    },
    {
        "type": "function",
        "name": "read_website",
        "description": """Call this tool if you need to crawl or read or get the information from the a website you have a link for.
        Use it when:
        - you got a set of results from the search_web tool and you need to get the information from the website link to answer the user
        - you have a link to a website which you need to crawl to get the relevnat answer
        - if the answer from website requires specific information that is not common knowledge or may have changed since your training data
        - if your answer depends on the date and time and the current information can change with date and time
       
        The tool returns the website content for the link
        You may call this for multiple results if necessary.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                 "websites":{
                      "type":"array",
                      "items":{
                          "type":"string"
                      },
                      "description":"One or more website links to crawl for content. Provide multiple links when you need information from different websites. If multiple independent crawls would improve the answer, include them all in a single call instead of making separate calls."
                 }
            }   # no params needed, just a trigger
        }
    },
    {
        "type": "function",
        "name": "write_to_file",
        "description": """Write content to a file on the user's machine.
        Use it only when the user explicitly asks you to create or update a local file.
        The application will ask the user for permission before writing.
        Use this tool also when its part of a broder task to achieve a goal and the user has given permission to write files for that task.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                 "filePath":{
                      "type":"string",
                      "description":"Directory path where the file should be written."
                 },
                 "filename":{
                      "type":"string",
                      "description":"Name of the file to create or overwrite."
                 },
                 "content":{
                      "type":"string",
                      "description":"Exact content to write to the file."
                 }
            },
            "required": ["filePath", "filename", "content"]
        }
    },
    {
        "type": "function",
        "name": "run_command",
        "description": """Run a shell command on the user's machine.
        Use it only when the user explicitly asks you to run a command or when its part of a broader task to achieve a goal and the user has given permission to run commands for that task.
        If the command might affect the whole system, ask the user for explicit permission in plain text before calling this tool. Begin the warning exactly with [[running this code might break system]] and wait for the user to confirm before calling this tool.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                 "command":{
                      "type":"string",
                      "description":"The shell command to run."
                 }
            },
            "required": ["command"]
        }
    },
                
    {
        "type": "function",
        "name": "read_file",
        "description": """Read a local file from the user's machine.
        Use it when the user asks you to inspect, summarize, explain, or use content from a specific local file.
        This tool does not ask for write permission because it only reads.""",
        "parameters": {
            "type": "object",
            "properties": {
                 "filePath":{
                      "type":"string",
                      "description":"Full path of the file to read."
                 }
            },
            "required": ["filePath"]
        }
    },
    {
        "type": "function",
        "name": "ask_question",
        "description": """This tool is used to ask the user a question and get their response. use it when you need to ask the user a question to get information that you cannot gather automatically or infer from the system.
        Use it when you cant get the info from the system to show options or you are curious about something and you want to ask the user a question to get their input. This tool is used to ask the user a question and get their response. The user will be prompted with the question and they can provide their answer. Use this tool when you need to ask the user a question to get information that you cannot gather automatically or infer from the system.""",
        "parameters": {
            "type": "object",
            "properties": {
                 "question":{
                      "type":"string",
                      "description":"The question to ask the user."
                 }
            },
            "required": ["question"]
        }
    },
    {
        "type": "function",
        "name": "ask_question_with_options",
        "description": """This tool is used to ask the user a question with multiple options and get their response. Use it when you need to ask the user a question and provide them with a set of predefined options to choose from. The user will be prompted with the question and the available options, and they can select one of the options as their answer. Use this tool when you need to ask the user a question and provide them with a set of predefined options to choose from. you can use this to ask yes or no questions also""",
        "parameters": {
            "type": "object",
            "properties": {
                 "question":{
                      "type":"string",
                      "description":"The question to ask the user."
                 },
                 "options":{
                      "type":"array",
                      "items":{"type":"string"},
                        "description":"The list of options to present to the user."
                 }
            },
            "required": ["question","options"]
        }
    },
    {
        "type": "function",
        "name": "save_device_details",
        "description": """Save the collected server/device details after all required data points have been collected. The data must be valid JSON. This tool writes the data to the correctly spelled manifest.json file in the project root.""",
        "parameters": {
            "type": "object",
            "properties": {
                 "data":{
                      "type":["object", "array", "string"],
                      "description":"The complete collected device details as valid JSON."
                 }
            },
            "required": ["data"]
        }
    },{
        "type": "function",
        "name": "edit_manifest_code",
        "description": """Replace setup_flow/generate_manifest.py with complete, verified Python source code.
        Use only after inspecting the current generator and gathering evidence with read-only commands.
        The application will ask the user for permission before writing the file.
        After a successful write, run the generator and validate manifest.json before reporting success.
        """,
        "parameters": {
            "type": "object",
            "properties": {
                 "content":{
                      "type":"string",
                      "description":"The complete latest working Python source code for setup_flow/generate_manifest.py. Do not send a patch or snippet."
                 }
            },
            "required": ["content"]
        }
    }

    
    ]
