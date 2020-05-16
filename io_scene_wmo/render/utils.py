RENDER_ENGINE_DEBUG = True


def render_debug(message: str):
    global RENDER_ENGINE_DEBUG

    if RENDER_ENGINE_DEBUG:
        print('Debug:', message)
