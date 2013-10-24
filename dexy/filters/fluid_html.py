from dexy.filter import DexyFilter

class FluidHtml(DexyFilter):
    """
    Wraps your text in HTML header/footer which includes Baseline CSS resets.
    Easy way to add styles (includes Pygments syntax highlighting).
    """
    aliases = ['easyhtml']
    _settings = {
            'input-extensions' : ['.html'],
            'output-extensions' : ['.html'],
            "css" : ("Custom CSS to include in header.", ""),
            "js" : ("Custom JS to include (please wrap in script tags).", ""),
            }

    def process_text(self, input_text):
        css = self.setting('css')
        if css:
            self.log_debug("custom css is %s" % css)

        js = self.setting('js')
        if js:
            self.log_debug("custom js is %s" % js)

        args = {
                'pygments_css' : PYGMENTS_CSS,
                'css_framework' : CSS_FRAMEWORK,
                'buttons' : CSS_BUTTONS,
                'custom_css' : css,
                'custom_js' : js,
                'content' : input_text
                }
        return """
<html>
    <head>
        <meta http-equiv="Content-type" content="text/html;charset=UTF-8" />
        <style type="text/css">
            %(css_framework)s
            %(buttons)s
            %(pygments_css)s

            /* custom css */
            %(custom_css)s
        </style>
        <!-- custom js -->
        %(custom_js)s
    </head>
    <body>
    <div id="content">
        <div class="g3">
%(content)s
        </div>
    </div>
    </body>
</html>
""" % args




PYGMENTS_CSS = """
.highlight .hll { background-color: #ffffcc }
.highlight .c { color: #888888 } /* Comment */
.highlight .err { color: #a61717; background-color: #e3d2d2 } /* Error */
.highlight .k { color: #008800; font-weight: bold } /* Keyword */
.highlight .cm { color: #888888 } /* Comment.Multiline */
.highlight .cp { color: #cc0000; font-weight: bold } /* Comment.Preproc */
.highlight .c1 { color: #888888 } /* Comment.Single */
.highlight .cs { color: #cc0000; font-weight: bold; background-color: #fff0f0 } /* Comment.Special */
.highlight .gd { color: #000000; background-color: #ffdddd } /* Generic.Deleted */
.highlight .ge { font-style: italic } /* Generic.Emph */
.highlight .gr { color: #aa0000 } /* Generic.Error */
.highlight .gh { color: #303030 } /* Generic.Heading */
.highlight .gi { color: #000000; background-color: #ddffdd } /* Generic.Inserted */
.highlight .go { color: #888888 } /* Generic.Output */
.highlight .gp { color: #555555 } /* Generic.Prompt */
.highlight .gs { font-weight: bold } /* Generic.Strong */
.highlight .gu { color: #606060 } /* Generic.Subheading */
.highlight .gt { color: #aa0000 } /* Generic.Traceback */
.highlight .kc { color: #008800; font-weight: bold } /* Keyword.Constant */
.highlight .kd { color: #008800; font-weight: bold } /* Keyword.Declaration */
.highlight .kn { color: #008800; font-weight: bold } /* Keyword.Namespace */
.highlight .kp { color: #008800 } /* Keyword.Pseudo */
.highlight .kr { color: #008800; font-weight: bold } /* Keyword.Reserved */
.highlight .kt { color: #888888; font-weight: bold } /* Keyword.Type */
.highlight .m { color: #0000DD; font-weight: bold } /* Literal.Number */
.highlight .s { color: #dd2200; background-color: #fff0f0 } /* Literal.String */
.highlight .na { color: #336699 } /* Name.Attribute */
.highlight .nb { color: #003388 } /* Name.Builtin */
.highlight .nc { color: #bb0066; font-weight: bold } /* Name.Class */
.highlight .no { color: #003366; font-weight: bold } /* Name.Constant */
.highlight .nd { color: #555555 } /* Name.Decorator */
.highlight .ne { color: #bb0066; font-weight: bold } /* Name.Exception */
.highlight .nf { color: #0066bb; font-weight: bold } /* Name.Function */
.highlight .nl { color: #336699; font-style: italic } /* Name.Label */
.highlight .nn { color: #bb0066; font-weight: bold } /* Name.Namespace */
.highlight .py { color: #336699; font-weight: bold } /* Name.Property */
.highlight .nt { color: #bb0066; font-weight: bold } /* Name.Tag */
.highlight .nv { color: #336699 } /* Name.Variable */
.highlight .ow { color: #008800 } /* Operator.Word */
.highlight .w { color: #bbbbbb } /* Text.Whitespace */
.highlight .mf { color: #0000DD; font-weight: bold } /* Literal.Number.Float */
.highlight .mh { color: #0000DD; font-weight: bold } /* Literal.Number.Hex */
.highlight .mi { color: #0000DD; font-weight: bold } /* Literal.Number.Integer */
.highlight .mo { color: #0000DD; font-weight: bold } /* Literal.Number.Oct */
.highlight .sb { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Backtick */
.highlight .sc { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Char */
.highlight .sd { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Doc */
.highlight .s2 { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Double */
.highlight .se { color: #0044dd; background-color: #fff0f0 } /* Literal.String.Escape */
.highlight .sh { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Heredoc */
.highlight .si { color: #3333bb; background-color: #fff0f0 } /* Literal.String.Interpol */
.highlight .sx { color: #22bb22; background-color: #f0fff0 } /* Literal.String.Other */
.highlight .sr { color: #008800; background-color: #fff0ff } /* Literal.String.Regex */
.highlight .s1 { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Single */
.highlight .ss { color: #aa6600; background-color: #fff0f0 } /* Literal.String.Symbol */
.highlight .bp { color: #003388 } /* Name.Builtin.Pseudo */
.highlight .vc { color: #336699 } /* Name.Variable.Class */
.highlight .vg { color: #dd7700 } /* Name.Variable.Global */
.highlight .vi { color: #3333bb } /* Name.Variable.Instance */
.highlight .il { color: #0000DD; font-weight: bold } /* Literal.Number.Integer.Long */
"""

CSS_FRAMEWORK = """
/*
    Fluid Baseline Grid v1.0.0
    Designed & Built by Josh Hopkins and 40 Horse, http://40horse.com
    Licensed under Unlicense, http://unlicense.org/

    Base stylesheet with CSS normalization, typographic baseline grid and progressive responsiveness
*/

/* HTML5 DECLARATIONS */
article, aside, details, figcaption, figure, footer, header, hgroup, menu, nav, section, dialog {display: block}
audio[controls],canvas,video {display: inline-block; *display: inline; zoom: 1}

/* BASE */
html {height: 100%; font-size: 100%; overflow-y: scroll; -webkit-text-size-adjust: 100%} /* Force scrollbar in non-IE and Remove iOS text size adjust without disabling user zoom */
body {margin: 0; min-height: 100%; -webkit-font-smoothing:antialiased; font-smoothing:antialiased; text-rendering:optimizeLegibility; background:url('../images/24px_grid_bg.gif') 0 1.1875em} /* Improve default text rendering, handling of kerning pairs and ligatures */

/* DEFAULT FONT SETTINGS */
/* 16px base font size with 150% (24px) friendly, unitless line height and margin for vertical rhythm */
/* Font-size percentage is based on 16px browser default size */
body, button, input, select, textarea {font: 100%/1.5 Georgia,Palatino,"Palatino Linotype",Times,"Times New Roman",serif; *font-size: 1em; color: #333} /* IE7 and older can't resize px based text */
p, blockquote, q, pre, address, hr, code, samp, dl, ol, ul, form, table, fieldset, menu, img {margin: 0 0 1.5em; padding: 0}

/* TYPOGRAPHY */
/* Composed to a scale of 12px, 14px, 16px, 18px, 21px, 24px, 36px, 48px, 60px and 72px */
h1, h2, h3, h4, h5, h6 {font-family:Futura, "Century Gothic", AppleGothic, sans-serif;color:#222;text-shadow:1px 1px 1px rgba(0,0,0,.10)}
h1 {margin: 0; font-size: 3.75em; line-height: 1.2em; margin-bottom: 0.4em} /* 60px / 72px */
h2 {margin: 0; font-size: 3em; line-height: 1em; margin-bottom: 0.5em} /* 48px / 48px */
h3 {margin: 0; font-size: 2.25em; line-height: 1.3333333333333333333333333333333em; margin-bottom: 0.6667em} /* 36px / 48px */ 
h4 {margin: 0; font-size: 1.5em; line-height: 1em; margin-bottom: 1em} /* 24px / 24px */
h5 {margin: 0; font-size: 1.3125em; line-height: 1.1428571428571428571428571428571em; margin-bottom: 1.1428571428571428571428571428571em} /* 21px / 24px */
h6 {margin: 0; font-size: 1.125em; line-height: 1.3333333333333333333333333333333em; margin-bottom: 1.3333333333333333333333333333333em} /* 18px / 24px */
p, ul, blockquote, pre, td, th, label {margin: 0; font-size: 1em; line-height: 1.5em; margin-bottom: 1.5em} /* 16px / 24px */
small, p.small {margin: 0; font-size: 0.875em; line-height: 1.7142857142857142857142857142857em; margin-bottom: 1.7142857142857142857142857142857em} /* 14px / 24px */

/* CODE */
pre {white-space: pre; white-space: pre-wrap; word-wrap: break-word} /* Allow line wrapping of 'pre' */
pre, code, kbd, samp {font-size: 1em; line-height: 1.5em; margin-bottom: 1.5em; font-family: Menlo, Consolas, 'DejaVu Sans Mono', Monaco, monospace}

/* TABLES */
table {border-collapse: collapse; border-spacing: 0; margin-bottom: 1.5em}
th {text-align: left}
tr, th, td {padding-right: 1.5em; border-bottom: 0 solid #333}

/* FORMS */
form {margin: 0}
fieldset {border: 0;padding: 0}
textarea {overflow: auto; vertical-align: top}
legend {*margin-left: -.75em}
button, input, select, textarea {vertical-align: baseline; *vertical-align: middle} /* IE7 and older */
button, input {line-height: normal; *overflow: visible}
button, input[type="button"], input[type="reset"], input[type="submit"] {cursor: pointer;-webkit-appearance: button}
input[type="checkbox"], input[type="radio"] {box-sizing: border-box}
input[type="search"] {-webkit-appearance: textfield; -moz-box-sizing: content-box; -webkit-box-sizing: content-box; box-sizing: content-box}
input[type="search"]::-webkit-search-decoration {-webkit-appearance: none}
button::-moz-focus-inner, input::-moz-focus-inner {border: 0; padding: 0}

/* QUOTES */
blockquote, q {quotes: none}
blockquote:before, blockquote:after, q:before, q:after {content: ''; content: none}
blockquote, q, cite {font-style: italic}
blockquote {padding-left: 1.5em; border-left: 3px solid #ccc}
blockquote > p {padding: 0}

/* LISTS */
ul, ol {list-style-position: inside; padding: 0}
li ul, li ol {margin: 0 1.5em}
dl dd {margin-left: 1.5em}
dt {font-family:Futura, "Century Gothic", AppleGothic, sans-serif}

/* HYPERLINKS */
a {text-decoration: none; color:#c47529}
a:hover {text-decoration: underline}
a:focus {outline: thin dotted}
a:hover, a:active {outline: none} /* Better CSS Outline Suppression */

/* MEDIA */
figure {margin: 0}
img, object, embed, video {max-width: 100%; _width: 100%} /* Fluid images */
img {border: 0; -ms-interpolation-mode: bicubic} /* Improve IE's resizing of images */
svg:not(:root) {overflow: hidden} /* Correct IE9 overflow */

/* ABBREVIATION */
abbr[title], dfn[title] {border-bottom: 1px dotted #333; cursor: help}

/* MARKED/INSERTED/DELETED AND SELECTED TEXT */
ins, mark {text-decoration: none}
mark {background: #c47529}
ins {background: #d49855}
del {text-decoration: line-through}
::-moz-selection {background: #c47529; color: #fff; text-shadow: none} /* selected text */
::selection {background: #c47529; color: #fff; text-shadow: none} /* selected text */

/* OTHERS */
strong, b, dt { font-weight: bold}
dfn {font-style: italic}
var, address {font-style: normal}
sub, sup {font-size: 75%; line-height: 0; position: relative; vertical-align: baseline} /* Position 'sub' and 'sup' without affecting line-height */
sup {top: -0.5em} /* Move superscripted text up */
sub {bottom: -0.25em} /* Move subscripted text down */
span.amp{font-family:Adobe Caslon Pro,Baskerville,"Goudy Old Style","Palatino","Palatino Linotype","Book Antiqua",Georgia,"Times New Roman",Times,serif;font-style:italic;font-size:110%;line-height:0;position:relative;vertical-align:baseline} /* Best available ampersand */

/* MICRO CLEARFIX HACK */
.cf:before, .cf:after {content:"";display:table} /* For modern browsers */
.cf:after {clear:both}
.cf {zoom:1} /* For IE 6/7 (trigger hasLayout) */

/* DEFAULT MOBILE STYLE */
body {width: 92%; margin: 0 auto} /* Center page without wrapper */
/* column grid */
.g1,.g2,.g3{display:block; position: relative; margin-left: 1%; margin-right: 1%}
/* 1 column grid */
.g1,.g2,.g3{width:98.0%}


/* media Queries

FOLDING FLUID GRID
< 767px         - 1-Column Fluid Grid
768px - 1023px  - 2-Column Fluid Grid
> 1024px            - 3-Column Fluid Grid
Change widths as necessary
------------------------------------------- */

/* MOBILE PORTRAIT */
@media only screen and (min-width: 320px) {
    body {
        
    }
}

/* MOBILE LANDSCAPE */
@media only screen and (min-width: 480px) {
    body {
        
    }
}

/* SMALL TABLET */
@media only screen and (min-width: 600px) {
    body {
        
    }
}

/* TABLET/NETBOOK */
@media only screen and (min-width: 768px) { 
    body {
        
    }
    
    /* COLUMN GRID */
    .g1,.g2,.g3 {display:inline; float: left}
    
    /* 2 COLUMN GRID */
    .g1 {width:48.0%}
    .g2 {width:48.0%}
    .g3 {width:98.0%}
}

/* LANDSCAPE TABLET/NETBOOK/LAPTOP */
@media only screen and (min-width: 1024px) { 
    body {

    }
    
    /* 3 COLUMN GRID */
    .g1 {width:31.333%}
    .g2 {width:64.667%;}
    .g3 {width:98.0%}
}

@media only screen and (min-width: 1280px) { 
/* DESKTOP */
        body {

    }
}

/* WIDESCREEN */
/* Increased body size for legibility */
@media only screen and (min-width: 1400px) { 
    body {font-size:116.75%; background:url('../images/28px_grid_bg.gif') 0 1.25em; max-width:1440px} /* 18.5px / 28px */
}


/* PRINT */
@media print {
  * {background: transparent !important; color: black !important; text-shadow: none !important; filter:none !important; -ms-filter: none !important} /* Black prints faster */
  a, a:visited {color: #444 !important; text-decoration: underline}
  a[href]:after {content: " (" attr(href) ")"}
  abbr[title]:after {content: " (" attr(title) ")"}
  .ir a:after, a[href^="javascript:"]:after, a[href^="#"]:after {content: ""}  /* Don't print links for images, javascript or internal links */
  pre, blockquote {border: 1px solid #999; page-break-inside: avoid; }
  thead {display: table-header-group; } /* Repeat header row at top of each printed page */
  tr, img {page-break-inside: avoid; }
  img {max-width: 100% !important; }
  @page {margin: 0.5cm}
  p, h2, h3 {orphans: 3; widows: 3}
  h2, h3{page-break-after: avoid}
}
"""

CSS_BUTTONS = """
/*
 * Copyright (c) 2013 Thibaut Courouble
 * http://www.cssflow.com
 *
 * Licensed under the MIT License:
 * http://www.opensource.org/licenses/mit-license.php
 */

.button {
  font: 10px/18px 'Lucida Grande', Arial, sans-serif;
  display: inline-block;
  vertical-align: top;
  position: relative;
  overflow: hidden;
  min-width: 96px;
  line-height: 30px;
  padding: 0 24px;
  font-size: 14px;
  color: white;
  text-align: center;
  text-decoration: none;
  text-shadow: 0 1px #154c86;
  background-color: #247edd;
  background-clip: padding-box;
  border: 1px solid;
  border-color: #1c65b2 #18589c #18589c;
  border-radius: 4px;
  -webkit-box-shadow: inset 0 1px rgba(255, 255, 255, 0.4), 0 1px 2px rgba(0, 0, 0, 0.2);
  box-shadow: inset 0 1px rgba(255, 255, 255, 0.4), 0 1px 2px rgba(0, 0, 0, 0.2);
  background-image: -webkit-linear-gradient(top, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0) 50%, rgba(0, 0, 0, 0.12) 51%, rgba(0, 0, 0, 0.04));
  background-image: -moz-linear-gradient(top, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0) 50%, rgba(0, 0, 0, 0.12) 51%, rgba(0, 0, 0, 0.04));
  background-image: -o-linear-gradient(top, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0) 50%, rgba(0, 0, 0, 0.12) 51%, rgba(0, 0, 0, 0.04));
  background-image: linear-gradient(to bottom, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0) 50%, rgba(0, 0, 0, 0.12) 51%, rgba(0, 0, 0, 0.04));
}
.button:before {
  content: '';
  position: absolute;
  top: -25%;
  bottom: -25%;
  left: -20%;
  right: -20%;
  border-radius: 50%;
  background: transparent;
  -webkit-box-shadow: inset 0 0 38px rgba(255, 255, 255, 0.5);
  box-shadow: inset 0 0 38px rgba(255, 255, 255, 0.5);
}
.button:hover {
  background-color: #1a74d3;
  text-decoration: none;
}
.button:active {
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 -1px #154c86;
  background: #1f71c8;
  border-color: #113f70 #154c86 #1c65b2;
  -webkit-box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2), 0 1px rgba(255, 255, 255, 0.4);
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2), 0 1px rgba(255, 255, 255, 0.4);
  background-image: -webkit-linear-gradient(top, #1a5da5, #3a8be0);
  background-image: -moz-linear-gradient(top, #1a5da5, #3a8be0);
  background-image: -o-linear-gradient(top, #1a5da5, #3a8be0);
  background-image: linear-gradient(to bottom, #1a5da5, #3a8be0);
}
.button:active:before {
  top: -50%;
  bottom: -125%;
  left: -15%;
  right: -15%;
  -webkit-box-shadow: inset 0 0 96px rgba(0, 0, 0, 0.2);
  box-shadow: inset 0 0 96px rgba(0, 0, 0, 0.2);
}

.button-green {
  text-shadow: 0 1px #0d4d09;
  background-color: #1ca913;
  border-color: #147b0e #11640b #11640b;
}
.button-green:hover {
  background-color: #159b0d;
}
.button-green:active {
  text-shadow: 0 -1px #0d4d09;
  background: #189210;
  border-color: #093606 #0d4d09 #147b0e;
  background-image: -webkit-linear-gradient(top, #126d0c, #20c016);
  background-image: -moz-linear-gradient(top, #126d0c, #20c016);
  background-image: -o-linear-gradient(top, #126d0c, #20c016);
  background-image: linear-gradient(to bottom, #126d0c, #20c016);
}

.button-red {
  text-shadow: 0 1px #72100d;
  background-color: #cd1d18;
  border-color: #9f1713 #891310 #891310;
}
.button-red:hover {
  background-color: #c01511;
}
.button-red:active {
  text-shadow: 0 -1px #72100d;
  background: #b61a15;
  border-color: #5b0d0b #72100d #9f1713;
  background-image: -webkit-linear-gradient(top, #921511, #e4201b);
  background-image: -moz-linear-gradient(top, #921511, #e4201b);
  background-image: -o-linear-gradient(top, #921511, #e4201b);
  background-image: linear-gradient(to bottom, #921511, #e4201b);
}
"""
