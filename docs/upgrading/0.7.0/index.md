## Upgrading to Dexy 0.7.0

Dexy 0.7.0 is a major rewrite and, while it should not be onerous to upgrade, you will have to make some changes in your project. Hopefully these changes are of a simplifying nature and won't be too onerous.

### .dexy file

In 0.7.0, you have more options in how you tell dexy which files you want it to run. Behind the scenes, there is now a Parser class which can be subclassed to make it easy to define new file formats, and you can also write a Python script to configure dexy by creating dexy Doc objects directly.

The upshot is, there is now a super-simple text file based format.

<pre>
{{ d['ex1/dexy.txt'] }}
</pre>

