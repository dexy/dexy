# Plugin Guide

## Filters

### Filter Concepts

#### Data Types

Filters take input and emit output. This input may have a number of different shapes.

+ Generic Data

Basically data with no particular 'shape'. This may be text or binary data in a single lump.

+ Sectioned Data

This is textual data which is organized into named sections.

+ Key-Value Data

This is data in key-value format.

+ Columnar Data

This is data in columnar, tabular or CSV-style format.

By exposing different shapes, we can add convenience functions that are appropriate to the shape, such as querying columnar data.


