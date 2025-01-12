from django.conf import settings
import openai
from colorama import Fore, Style

class BloomerpConfigChecker:
    '''Class that checks whether the configuration for bloomerp is correct'''
    settings : dict = settings

    OKAY = 0 # Okay status
    WARNING = 1 # Warning status
    ERROR = 2 # Error status

    def _check_open_ai_key(self) -> tuple[int, str]:
        '''Check if the open ai key is set'''
        openai_key = self.settings.BLOOMERP_SETTINGS.get('OPENAI_API_KEY', None)

        appended_message = 'Without a valid key, the LLM features will not work.'

        if not openai_key:
            return self.WARNING, 'OpenAI key not found in settings' + appended_message
        else:
            # Check if the key is valid
            client = openai.OpenAI(api_key=openai_key)
            try:
                client.models.list()
            except openai.AuthenticationError:
                return self.WARNING, 'Invalid OpenAI key' + appended_message
            else:
                return self.OKAY, 'OpenAI key is valid'

    def _check_login_url(self) -> tuple[int, str]:
        '''Check if the login url is set'''
        login_url = self.settings.LOGIN_URL
        
        if not login_url:
            return self.ERROR, 'Login URL not found in settings'
        
        if login_url != 'login':
            return self.WARNING, 'It is recommended to set the login URL to "login"'
        
        return self.OKAY, 'Login URL is set correctly'

    def check(self) -> bool:
        '''Check the configuration'''
        print(f'{Fore.BLUE}Checking Bloomerp configuration{Style.RESET_ALL}')

        checks = [
            self._check_open_ai_key,
            self._check_login_url
        ]

        for check in checks:
            status, message = check()
            if status == self.OKAY:
                print(f'{Fore.GREEN}OK: {message}{Style.RESET_ALL}')
            elif status == self.WARNING:
                print(f'{Fore.YELLOW}WARNING: {message}{Style.RESET_ALL}')
            else:
                print(f'{Fore.LIGHTRED_EX}ERROR: {message}{Style.RESET_ALL}')