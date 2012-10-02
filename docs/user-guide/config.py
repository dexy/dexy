from dexy import conf
from dexy.doc import Doc

doc = Doc("modules.txt|pydoc", contents="dexy")
conf("*.py", doc, "*.py|pyg", "*/*.py|py", "*.md|jinja|markdown")
