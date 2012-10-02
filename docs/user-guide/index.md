## Hello, World

Let's start with a simple example that will help you create a dexy project in just a few minutes.

### Run a Simple Script

Let's start by creating a simple python script that we want Dexy to run for us:

{{ d['hello-world/script.py|pyg'] }}

We need to tell Dexy what we want it to do with this script, so we need to write another file named `config.py` with instructions for Dexy.

{{ d['hello-world/config.py|pyg'] }}

This config tells Dexy that we want to take the file named "config.py" and run it through a filter identified as "py".

The generated files look liks this:

{% for k in d['hello-world/config.py-py.txt-files'].keys() -%}
`{{ k }}`
{% endfor -%}


<pre>
{{ d['hello-world/script.py|py'] }}
</pre>


<pre>
{{ sorted(d['modules.txt|pydoc'].keys()) }}
</pre>
