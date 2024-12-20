from bloomerp.utils.router import route
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, StreamingHttpResponse
from bloomerp.utils.llm import BloomerpOpenAI, BloomerpLangChain
from bloomerp.models import ApplicationField, DocumentTemplate
from django.contrib.auth.decorators import login_required
from django.conf import settings
import json
from django.core.cache import cache
from bloomerp.langchain_tools import BLOOMAI_TOOLS

@login_required
@route('llm_executor')
def llm_executor(request:HttpRequest) -> HttpResponse:
    '''
    Component to execute LLM queries.
    '''
    
    LLM_QUERY_TYPES = ['sql', 'document_template', 'tiny_mce_content', 'bloom_ai','code']
    
    try:
        if request.method == 'POST':
            # Get the json data from the request
            json_data = json.loads(request.body)

            query_type = json_data.get('query_type', None)
            query = json_data.get('query', None)
            conversation_history = json_data.get('conversation_history', None)

            # Some preprocessing
            if not query_type:
                return HttpResponse('No llm query type provided')
            
            # Check if the query type is valid
            if query_type not in LLM_QUERY_TYPES:
                return HttpResponse('Invalid llm query type, must be one of: ' + ', '.join(LLM_QUERY_TYPES))
            
            # Check if the query is provided
            openai_key = settings.BLOOMERP_SETTINGS.get('OPENAI_API_KEY', None)
            if not openai_key:
                return HttpResponse('OpenAI key not found in settings')
            
            # Init the OpenAI class
            openai = BloomerpOpenAI(openai_key)

            # Check if the key is valid
            if not openai.is_valid_key():
                return HttpResponse('Invalid OpenAI key')
            
            # ---------------------
            # Query execution
            # ---------------------
            if query_type == 'sql':
                db_tables_and_columns = ApplicationField.get_db_tables_and_columns()
                sql_query = openai.create_sql_query(
                    query,
                    db_tables_and_columns,
                    conversation_history=conversation_history
                    )
                return HttpResponse(sql_query)
            
            elif query_type == 'document_template':
                # Get template id from args
                template_id = json_data['args'].get('template_id', None)

                if not template_id:
                    return HttpResponse('Template id not provided')
                
                # Get the document template
                template = DocumentTemplate.objects.get(pk=template_id)
                variables = template.get_variables()
                return StreamingHttpResponse(
                    openai.create_document_template(
                        query,
                        variables,
                        stream_response=True,
                        conversation_history=conversation_history
                        ),
                    content_type='text/html'
                )
            
            elif query_type == 'tiny_mce_content':
                return StreamingHttpResponse(
                    openai.create_tiny_mce_content(
                        prompt=query, 
                        stream_response=True, 
                        conversation_history=conversation_history
                        ),
                    content_type='text/html'
                    )
            
            elif query_type == 'bloom_ai':
                # Get the conversation id from the args
                conversation_id = json_data['args'].get('conversation_id', None)

                # Try to get the conversation history from the cache
                conversation_history = cache.get(conversation_id, None)

                # Get the to

                executor = BloomerpLangChain(
                    api_key=openai_key, 
                    conversation_history=conversation_history, 
                    conversation_id=conversation_id
                    )
                
                return StreamingHttpResponse(
                    executor.invoke_bloom_ai(query, BLOOMAI_TOOLS, user=request.user),
                    content_type='text/html'
                )

            elif query_type == 'code':
                resp = openai.create_code(
                    query,
                    conversation_history=conversation_history
                    )
                return HttpResponse(resp)
            else:
                return HttpResponse('Action not supported')

        else:
            return HttpRequest('GET request not supported')
    except Exception as e:
        return HttpResponse("Oops! Something went wrong: " + str(e))
    


