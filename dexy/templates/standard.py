import dexy.template

class DefaultTemplate(dexy.template.Template):
    """
    A very boring default template that ships with dexy.
    """
    aliases = ['default']
    filters_used = ['jinja']
