from colors import color


def get_rd(text: str):
    return color(text, 'red')


def get_gr(text: str):
    return color(text, 'green')


def get_yl(text: str):
    return color(text, 'yellow')


def get_bl(text: str):
    return color(text, 'blue')


def get_ok(text: str, ok: bool):
    return get_gr(text) if ok else get_rd(text)

