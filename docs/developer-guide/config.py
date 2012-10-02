from dexy import run

run(
        ["modules.txt|pydoc", { "contents" : "dexy", "version" : "14" } ],
        "*.py",
        "*.py|idio",
        "*/*.py|py",
        ["*.md|jinja|markdown|dexcellent", { "depends" : True }]
        )

