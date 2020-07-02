RENDER_ENGINE_DEBUG = False


def render_debug(message: str):
    global RENDER_ENGINE_DEBUG

    if RENDER_ENGINE_DEBUG:
        print('Debug:', message)
