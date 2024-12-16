
def parse_bool_parameter(value, default_value=False) -> bool:
    '''
    Function that will parse a string to a boolean value.
    '''
    try:
        if type(value) == bool:
            return value
        
        if value.lower() in ['true', '1']:
            return True
        elif value.lower() in ['false', '0']:
            return False
        else:
            return default_value
    except:
        return default_value    
    