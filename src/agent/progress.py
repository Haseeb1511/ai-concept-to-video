import datetime

def get_military_log(category: str, message: str) -> str:
    """
    Format a message in a tactical military style:
    [HH:MM:SS] >> STATUS: COMPILING MANIM ASSETS...
    """
    now = datetime.datetime.now().strftime("%H:%M:%S")
    return f"[{now}] >> {category.upper()}: {message.upper()}"
