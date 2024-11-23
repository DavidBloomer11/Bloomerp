from openai import OpenAI
from django.conf import settings


class BloomerpOpenAI:
    def __init__(self):
        API_KEY = settings.BLOOMERP_SETTINGS.get('BLOOMERP_OPENAI_API_KEY', None)

        self.client = OpenAI(api_key=API_KEY)
        self.model = "gpt-4o"
    
    def is_valid_key(self):
        '''Checks if the OpenAI API key is valid.'''
        try:
            self.client.models.list()
            return True
        except Exception:
            return False


    def create_sql_query(self,
                        query: str,
                        db_tables_and_columns: list[tuple[str, list[str]]]
                        ) -> str:
        '''
        This function creates a SQL query from a natural language query.
        '''
        system_content = '''
        You are a helpful assistant that helps me to create SQL queries from natural language.
        The output should be a SQL query using sqlite3 syntax, without any explanation. Dont include in the output ```sql ... ```, just the raw SQL query.
        Here are the database tables, columns and datatypes for each column in the database:
        '''

        for table in db_tables_and_columns:
            system_content += f'\n{table[0]}: '

            for column in table[1]:
                system_content += f'{column[0]} ({column[1]}), '
        

        response = self.client.chat.completions.create(
            model = self.model,
            messages = [
                {'role': 'system', 'content': system_content},
                {'role': 'user', 'content': query},
            ]
        )


        sql_query = response.choices[0].message.content

        # Remove ```sql ... ``` from the output
        sql_query = sql_query.replace('```sql\n', '').replace('```', '')

        return sql_query
