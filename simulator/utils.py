from typing import Any, Dict, List, Callable, Optional
from simulator import exceptions

def action(func):
    def wrapper(*args, **kwargs):
        if args[0].available_actions == 0:
            raise exceptions.NoAvailableActionsLeft()
        
        result = func(*args, **kwargs)
        args[0].spent_actions += 1
        return result
    return wrapper


def check_action_availability(func):
    def wrapper(self):
        try:
            result = func(self)
        except exceptions.NoAvailableActionsLeft:
            print("Пора идти спать. Сегодня уже ничего не сделать.")
            return None
        return result
    return wrapper


class Option:
    key: str
    text: str
    handler: Callable
    handler_args: List[Any]
    handler_kwargs: Dict

    def __init__(self, key: str, text: str, handler: Optional[Callable] = None, handler_args: Optional[List[Any]] = None, handler_kwargs: Optional[Dict] = None):
        self.key = key
        self.text = text
        self.handler = handler
        self.handler_args = handler_args
        self.handler_kwargs = handler_kwargs
    
    def __str__(self):
        return f"{self.key} - {self.text}"