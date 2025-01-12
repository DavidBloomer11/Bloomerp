from openai import OpenAI, Stream
from django.conf import settings
from langchain_core.messages import (
    HumanMessage, 
    SystemMessage, 
    ToolMessage, 
    BaseMessage,
    AIMessage,
    messages_from_dict,
    messages_to_dict
    )
from langchain_core.chat_history import InMemoryChatMessageHistory
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.graph.graph import CompiledGraph
from django.core.cache import cache
from langchain_core.tools import StructuredTool
from bloomerp.langchain_tools import BaseBloomerpTool
from pydantic import BaseModel, Field


class BloomerpOpenAI:
    def __init__(self, api_key: str = None):
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o-mini"
    
    def _prepare_messages(
            self,
            query: str,
            system_content: str,
            conversation_history: list[dict[str, str]] = None
            ) -> list[dict[str, str]]:
        '''Prepare messages for the OpenAI API.'''
        messages = [
            {'role': 'system', 'content': system_content}
        ]

        if conversation_history:
            messages += conversation_history

        messages.append({'role': 'user', 'content': query})

        return messages

    def is_valid_key(self):
        '''Checks if the OpenAI API key is valid.'''
        try:
            self.client.models.list()
            return True
        except Exception:
            return False

    def create_tiny_mce_content(
            self, 
            prompt:str, 
            stream_response:bool=False,
            conversation_history: list[dict[str, str]] = None
            ) -> str:
        '''Function to create the content for TinyMCE editor.'''

        SYSTEM_CONTENT = '''
        You are a helpful assistant that helps me to create content for TinyMCE editor based on the prompt it gives.
        The output should be the content that can be used in TinyMCE editor, meaning it should be formatted as HTML.
        '''

        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(prompt, SYSTEM_CONTENT, conversation_history)
        
        if stream_response:
            response : Stream = self.client.chat.completions.create(
                model = self.model,
                stream=True,
                messages = messages
            )

            for content in response:
                chunk = content.choices[0].delta.content

                # Filter out the ```html ... ``` from the output
                if chunk:
                    yield chunk
                else:
                    print('Streaming done')
                
        else:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages
            )

            content = response.choices[0].message.content
            return content

    def create_sql_query(self,
                        query: str,
                        db_tables_and_columns: list[tuple[str, list[str]]],
                        conversation_history: list[dict[str, str]] = None
                        ) -> str:
        '''
        This function creates a SQL query from a natural language query.
        '''

        SYSTEM_CONTENT = '''
        You are a helpful assistant that helps me to create SQL queries from natural language.
        The output should be a SQL query using sqlite3 syntax, without any explanation. Dont include in the output ```sql ... ```, just the raw SQL query.
        Here are the database tables, columns and datatypes for each column in the database:
        '''

        for table in db_tables_and_columns:
            SYSTEM_CONTENT += f'\n{table[0]}: '

            for column in table[1]:
                SYSTEM_CONTENT += f'{column[0]} ({column[1]}), '
        
        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(query, SYSTEM_CONTENT, conversation_history)

        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages
        )

        sql_query = response.choices[0].message.content

        # Remove ```sql ... ``` from the output
        sql_query = sql_query.replace('```sql\n', '').replace('```', '')

        return sql_query

    def create_document_template(
            self, 
            query: str,
            variables: list[(str, str, str)], 
            conversation_history: list[dict[str, str]] = None,
            stream_response:bool=False
            ) -> str:
        '''
        This function creates a document template from a natural language query.
        '''
        SYSTEM_CONTENT = '''
        You are a helpful assistant that helps me to create document templates from natural language.
        The output should be the document (in html) using jinja2 (Django template) syntax, without any explanation. Dont include in the output ```html ... ```, just the raw HTML.
        For object variables, use the following syntax: {{ object.variable_name }}
        For free variables, use the following syntax: {{ free_variable_name }}

        Here are the available variables that you can use in the document template:
        '''
        for variable in variables:
            SYSTEM_CONTENT += f'\n{variable[0]} ({variable[1]}) - {variable[2]}'


        messages = self._prepare_messages(query, SYSTEM_CONTENT, conversation_history)

        if stream_response:
            response : Stream = self.client.chat.completions.create(
                model = self.model,
                stream=True,
                messages = messages
            )

            for content in response:
                chunk = content.choices[0].delta.content

                # Filter out the ```html ... ``` from the output
                if chunk:
                    yield chunk
        else:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages
            )

            content = response.choices[0].message.content
            return content
    
    def create_bloom_ai(self, query: str, conversation_history: list[dict[str, str]] = None) -> str:
        '''
        This function creates a document template from a natural language query.
        '''
        raise NotImplementedError('Bloom AI is not implemented yet')
    
    def create_code(self, query: str, conversation_history: list[dict[str, str]] = None) -> str:
        '''
        This function creates a document template from a natural language query.
        '''

        # Create system content
        SYSTEM_CONTENT = '''
        You are a helpful assistant that helps me to create code from natural language.
        Only return the actual code snippet without giving any explanation.
        Don't include any markdown code blocks in the output.
        '''

        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(query, SYSTEM_CONTENT, conversation_history)

        response = self.client.chat.completions.create(
            model = self.model,
            messages = messages
        )

        code = response.choices[0].message.content

        return code
    


class BloomerpLangChain:
    '''Class to invoke the Bloom AI agent.''' 
    conversation_history : list
    invoked: bool = False

    def __init__(self, 
                 api_key:str=None, 
                 conversation_history:list = None, 
                 ):
        '''
        Args:
            api_key: The OpenAI API key.
            conversation_history: The conversation history.
        '''

        self.api_key = api_key
        self.conversation_history = conversation_history
        self.model = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)

    def invoke_tiny_mce_content(self, query:str):
        '''Invoke the TinyMCE content agent.'''

        SYSTEM_CONTENT = '''You are a helpful assistant that helps me to create content for TinyMCE editor based on the prompt it gives.
        The output should be the content that can be used in TinyMCE editor, meaning it should be formatted as HTML.
        '''

        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(query, SYSTEM_CONTENT)

        # Create the agent
        memory = MemorySaver()
        agent = create_react_agent(self.model, tools=[], checkpointer=memory)

        # Invoke the model
        for chunk in self._invoke_model(messages, agent):
            yield chunk
    
    def invoke_sql_query(self, query:str, db_tables_and_columns:list[tuple[str, list[str]]]):
        '''Invoke the SQL query agent.'''

        # Prepare system content
        SYSTEM_CONTENT = '''You are a helpful assistant that helps me to create SQL queries from natural language.
        The output should be a SQL query using sqlite3 syntax, without any explanation. Dont include in the output ```sql ... ```, just the raw SQL query.
        Here are the database tables, columns and datatypes for each column in the database:
        '''

        for table in db_tables_and_columns:
            SYSTEM_CONTENT += f'\n{table[0]}: '

            for column in table[1]:
                SYSTEM_CONTENT += f'{column[0]} ({column[1]}), '

        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(query, SYSTEM_CONTENT)

        # Create the agent
        memory = MemorySaver()
        agent = create_react_agent(self.model, tools=[], checkpointer=memory)

        # Invoke the model
        for chunk in self._invoke_model(messages, agent):
            yield chunk
        
    def invoke_bloom_ai(self, query:str, tools:list[StructuredTool], user=None):
        '''Invoke the Bloom AI agent.'''

        if user:
            name = user.get_full_name()

        SYSTEM_CONTENT = f'''You are an AI agent for a ERP system called Bloomerp. You are currently serving a user named {name}.
        Your job is to help users with their day-to-day job, which can include answering to queries. 
        You can use the tools provided to you to get information from the database and provide it to the user.
        If you need to get information from the database, you can use the tool get_database_tables to get the tables and their columns in the database, but please only call this once per conversation.
        '''

        # Prepare messages for the OpenAI API
        # Used to save the state of the conversation
        memory = MemorySaver()

        initialized_tools = []
        for tool in tools:
            # Check if the tool has attribute requires_user
            if issubclass(tool, BaseBloomerpTool):
                initialized_tools.append(tool(user=user))
            else:
                initialized_tools.append(tool())


        # Create the agent
        agent = create_react_agent(self.model, tools=initialized_tools, checkpointer=memory)

        # Get messages from the conversation history
        messages = self._parse_conversation_history()

        if not messages.messages:
            messages.add_message(SystemMessage(SYSTEM_CONTENT))
        
        messages.add_message(HumanMessage(query))

        # Get the configuration
        config = {"configurable": {"thread_id": "abc123"}}

        # Execute the agent
        for chunk in agent.stream(
            input=messages, config=config, stream_mode='messages'
        ):  
            if type(chunk[0]) == ToolMessage:
                tool_name : str = chunk[0].name
                tool_name = tool_name.replace('_', ' ').capitalize()
                yield f" *Calling '{tool_name}' tool.* "
            else:
                result = chunk[0].content
                yield result
        
        # Set invoked to True
        self.invoked = True

        # Save the conversation history
        messages : list[BaseMessage] = memory.get(config)['channel_values']['messages']

        # Set the conversation history
        self.conversation_history = messages

    def invoke_code(self, query:str):
        '''Invoke the code agent.'''

        SYSTEM_CONTENT = '''You are a helpful assistant that helps me to create code from natural language.
        Only return the actual code snippet without giving any explanation.
        Don't include any markdown code blocks in the output.
        '''

        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(query, SYSTEM_CONTENT)

        # Create the agent
        memory = MemorySaver()
        agent = create_react_agent(self.model, tools=[], checkpointer=memory)

        # Invoke the model
        for chunk in self._invoke_model(messages, agent):
            yield chunk

    def invoke_document_template(self, query:str, variables:list[(str, str, str)]):
        '''Invoke the document template agent.'''

        SYSTEM_CONTENT = '''
        You are a helpful assistant that helps me to create document templates from natural language.
        The output should be the document (in html) using jinja2 (Django template) syntax, without any explanation. Dont include in the output ```html ... ```, just the raw HTML.
        For object variables, use the following syntax: {{ object.variable_name }}
        For free variables, use the following syntax: {{ free_variable_name }}

        Here are the available variables that you can use in the document template:
        '''
        for variable in variables:
            SYSTEM_CONTENT += f'\n{variable[0]} ({variable[1]}) - {variable[2]}'

        # Prepare messages for the OpenAI API
        messages = self._prepare_messages(query, SYSTEM_CONTENT)

        # Create the agent
        memory = MemorySaver()
        agent = create_react_agent(self.model, tools=[], checkpointer=memory)

        # Invoke the model
        for chunk in self._invoke_model(messages, agent):
            yield chunk

    def serialize_conversation_history(self) -> list[dict]:
        '''Make the conversation history JSON serializable.'''
        if self.conversation_history:
            return messages_to_dict(self.conversation_history)
        else:
            return []

    def _parse_conversation_history(self) -> InMemoryChatMessageHistory:
        '''Parse the conversation history into InMemoryChatMessageHistory.'''
        try:
            if self.conversation_history:
                return InMemoryChatMessageHistory(messages=messages_from_dict(self.conversation_history))    
            else:
                return InMemoryChatMessageHistory()
        except Exception as e:
            return InMemoryChatMessageHistory()

    def _invoke_model(self, messages:InMemoryChatMessageHistory, agent:CompiledGraph):
        '''Invoke the model.'''
        
        # This should be investigated in the future
        config = {"configurable": {"thread_id": "abc123"}}

        # Execute the agent
        for chunk in agent.stream(
            input=messages, config=config, stream_mode='messages'
        ):  
            if type(chunk[0]) == ToolMessage:
                tool_name : str = chunk[0].name
                tool_name = tool_name.replace('_', ' ').capitalize()
                yield f" *Calling '{tool_name}' tool.* "
            else:
                result = chunk[0].content
                yield result

        # Set invoked to True
        self.invoked = True

        # Save the conversation history
        messages : list[BaseMessage] = agent.checkpointer.get(config)['channel_values']['messages']

        # Set the conversation history
        self.conversation_history = messages

    def _prepare_messages(self, query:str, system_content:str) -> InMemoryChatMessageHistory:
        '''Prepares messages using the conversation history.
        
        Args:
            query: The user query.
            system_content: The system content.

        Returns:
            InMemoryChatMessageHistory: The conversation history.
        '''
        messages = self._parse_conversation_history()

        if not messages.messages:
            messages.add_message(SystemMessage(system_content))
        
        messages.add_message(HumanMessage(query))

        return messages
    
    def auto_name(self):
        '''Automatically provides a title for a conversation history.'''
        
        class ConversationName(BaseModel):
            title : str = Field(max_length=80)

        SYSTEM_CONTENT = '''Your goal is give a title to a conversation history based on the conversation that happened.
        the title should be max 80 characters long and should be a summary of the conversation that happened.
        '''
        # Prepare messages
        messages = self._parse_conversation_history()

        messages.add_message(SystemMessage(SYSTEM_CONTENT))

        structured_llm = self.model.with_structured_output(ConversationName)

        # Execute
        return structured_llm.invoke(messages.messages).dict()['title']

        
