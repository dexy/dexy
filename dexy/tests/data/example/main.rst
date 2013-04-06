Multiplication
==============

{% from 'dexy.jinja' import code, codes with context -%}

First we assign variables:

{{ codes('multiply.py|idio', 'assign-variables') }}

Then we multiply:

{{ codes('multiply.py|idio', 'multiply') }}
