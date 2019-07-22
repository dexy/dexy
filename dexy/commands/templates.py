from dexy.commands.utils import init_wrapper
from dexy.commands.utils import template_text
from dexy.utils import getdoc
import dexy.templates
import os
import sys
from dexy.utils import file_exists

DEFAULT_TEMPLATE = 'dexy:default'
def gen_command(
        plugins='', # extra python packages to load so plugins will register with dexy
        d=None,  # The directory to place generated files in, must not exist.
        t=False, # Shorter alternative to --template.
        template=DEFAULT_TEMPLATE, # The alias of the template to use.
        **kwargs # Additional kwargs passed to template's run() method.
        ):
    """
    Generate a new dexy project in the specified directory, using the template.
    """
    wrapper = init_wrapper(locals())

    if t and (template == DEFAULT_TEMPLATE):
        template = t
    elif t and template != DEFAULT_TEMPLATE:
        raise dexy.exceptions.UserFeedback("Only specify one of --t or --template, not both.")

    if not template in dexy.template.Template.plugins:
        print("Can't find a template named '%s'. Run 'dexy templates' for a list of templates." % template)
        sys.exit(1)

    template_instance = dexy.template.Template.create_instance(template)
    template_instance.generate(d, **kwargs)

    # We run dexy setup. This will respect any dexy.conf file in the template
    # but passing command line options for 'setup' to 'gen' currently not supported.
    os.chdir(d)
    wrapper.create_dexy_dirs()
    print("Success! Your new dexy project has been created in directory '%s'" % d)
    if file_exists("README"):
        print("\n--------------------------------------------------")
        with open("README", "r") as f:
            print(f.read())
        print("\n--------------------------------------------------")
        print("\nThis information is in the 'README' file for future reference.")

def template_command(
        alias=None
        ):
    print(template_text(alias))

def templates_command(
        plugins='', # extra python packages to load so plugins will register with dexy
        simple=False, # Only print template names, without docstring or headers.
        validate=False, # Intended for developer use only, validate templates (runs and checks each template).
        key=False # Only print information which matches this search key.
        ):
    """
    List templates that can be used to generate new projects.
    """
    init_wrapper(locals())

    if not simple:
        FMT = "%-40s %s"
        print(FMT % ("Alias", "Info"))

    for i, template in enumerate(dexy.template.Template):
        if key:
            if not key in template.alias:
                continue

        if template.setting('nodoc'):
            continue

        if simple:
            print(template.alias)
        else:
            first_line_help = template.setting('help').splitlines()[0].strip()
            print(FMT % (template.alias, first_line_help), end=' ')
            if validate:
                print(" validating...", end=' ')
                print(template.validate() and "OK" or "ERROR")
            else:
                print('')
    
    if i < 5:
        print("Run '[sudo] pip install dexy-templates' to install some more templates.")

    if not simple:
        print("Run 'dexy help -on gen' for help on generating projects from templates.")
