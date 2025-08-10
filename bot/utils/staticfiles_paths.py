import os

def get_staticfiles_root():
    """Return the absolute path to the StaticFiles directory."""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'StaticFiles'))

def get_static_path(*parts):
    """Return the absolute path to a file or directory in StaticFiles/static."""
    return os.path.join(get_staticfiles_root(), 'static', *parts)

def get_data_path(*parts):
    """Return the absolute path to a file or directory in StaticFiles/data."""
    return os.path.join(get_staticfiles_root(), 'data', *parts)

def get_templates_path(*parts):
    """Return the absolute path to a file or directory in StaticFiles/templates."""
    return os.path.join(get_staticfiles_root(), 'templates', *parts)
