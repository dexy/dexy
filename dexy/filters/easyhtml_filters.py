from dexy.dexy_filter import DexyFilter

class EasyHtml(DexyFilter):
    """
    Wraps your text in HTML header/footer which links to hosted Atatonic CSS
    assets. Easy way to add styles (includes Python syntax highlighting).
    """
    ALIASES = ['easyhtml']
    INPUT_EXTENSIONS = ['.html']
    OUTPUT_EXTENSIONS = ['.html']
    HEADER = """
    <html>
        <head>
        <style type="text/css">
html,body,div,span,applet,object,iframe,h1,h2,h3,h4,h5,h6,p,blockquote,pre,a,abbr,acronym,address,big,cite,code,del,dfn,em,font,img,ins,kbd,q,s,samp,small,strike,strong,sub,sup,tt,var,b,u,i,center,dl,dt,dd,ol,ul,li,fieldset,form,label,legend,table,caption,tbody,tfoot,thead,tr,th,td{border:0;outline:0;font-size:100%;vertical-align:baseline;background:transparent;margin:0;padding:0}body{line-height:1;font:12px/18px "Lucida Grande", Arial, sans-serif;color:#111}ol,ul{list-style:none}blockquote,q{quotes:none}blockquote:before,blockquote:after,q:before,q:after{content:none}:focus{outline:0}ins{text-decoration:none}del{text-decoration:line-through}table{border-collapse:collapse;border-spacing:0}hr{height:0;border:0;border-top:1px solid #e0e0e0;width:100%;margin:0 0 17px;padding:0}header,footer,section,aside,nav,article{display:block!important}.zp-wrapper{width:970px;margin:0 auto}.zp-5,.zp-10,.zp-15,.zp-20,.zp-25,.zp-30,.zp-33,.zp-35,.zp-40,.zp-45,.zp-50,.zp-55,.zp-60,.zp-65,.zp-67,.zp-70,.zp-75,.zp-80,.zp-85,.zp-90,.zp-95,.zp-100{float:left;display:inline}.zp-5{width:5%}.zp-10{width:10%}.zp-15{width:15%}.zp-20{width:20%}.zp-25{width:25%}.zp-30{width:30%}.zp-33{width:33.33%}.zp-35{width:35%}.zp-40{width:40%}.zp-45{width:45%}.zp-50{width:50%}.zp-55{width:55%}.zp-60{width:60%}.zp-65{width:65%}.zp-67{width:66.67%}.zp-70{width:70%}.zp-75{width:75%}.zp-80{width:80%}.zp-85{width:85%}.zp-90{width:90%}.zp-95{width:95%}.zp-100{width:100%}.last{padding:0!important}.clear{clear:both}.left{float:left}.right{float:right}.list{list-style:none;margin:0;padding:0}.list li{display:inline;margin:0 6px 0 0}.clearfix:after,.zp-wrapper:after{content:".";display:block;clear:both;visibility:hidden;line-height:0;height:0}.clearfix,.zp-wrapper{display:inline-block}html[xmlns] .clearfix,html[xmlns] .zp-wrapper{display:block}* html .clearfix,* html .zp-wrapper{height:1%}.skip{display:block;left:-9999px;position:absolute;visibility:hidden}h1{font-size:36px;line-height:36px;font-weight:400;font-family:Georgia, "Times new roman", serif}h2{font-family:Georgia, "Times new roman", serif;font-size:18px;line-height:36px;font-style:italic;font-weight:400}h3{font-size:12px;line-height:18px;font-weight:700;color:#000;margin:0}h4{font-size:12px;line-height:18px;font-weight:400;color:#666;margin:0}h5,h6{font-size:12px;line-height:18px;font-weight:400;margin:0}p{margin:0 0 18px}p img,li img{float:left;margin:4px 6px 0 0;padding:0}p img.right,li img.right{float:right;margin:4px 0 6px;padding:0}a,a:focus{color:#009;text-decoration:underline}blockquote{background:#F9F9F9;border-left:6px solid #ccc;color:#333;font-family:Georgia, "Times new roman", serif;font-size:13px;font-style:italic;margin:0 0 18px;padding:9px}p.intro:first-letter,p.important:first-letter{font-size:43px;font-weight:400;line-height:32px;letter-spacing:5px;float:left;width:auto;font-family:Georgia, Times, serif;padding:5px 0 0}p.intro:first-line,p.important:first-line{font-variant:small-caps}pre,code{font-family:monaco, courier, "courier new", monospace;font-size:11px;margin:0 0 2px;padding:2px}a.button,button{display:block;float:left;border:1px solid #ccc;background:#ccc url(../images/button.png) left top repeat-x;font-family:"Lucida Grande", Tahoma, Arial, Verdana, sans-serif;font-size:11px;line-height:16px;text-decoration:none;font-weight:400;color:#333;cursor:pointer;white-space:nowrap;vertical-align:baseline;border-color:#999 #858585 #666;margin:0 3px 15px 0;padding:2px 6px}button{width:auto;overflow:visible;padding:1px 4px}a.button{line-height:14px}button[type]{line-height:16px;padding:1px 4px}a.button:hover,button:hover{background-color:#ccc;border:1px solid #000;color:#000;text-decoration:none}.notification{font-size:11px;line-height:18px;margin:0 0 17px;padding:0 4px}.notice{background:#FFF6BF;color:#514721;border-bottom:1px solid #FFD324}.error{background:#FBE3E4;color:#8a1f11;border-bottom:1px solid #FBC2C4}.success{background:#E6EFC2;color:#264409;border-bottom:1px solid #C6D880}fieldset{border:1px solid #ccc;margin:0 0 18px;padding:9px}legend{color:#333;font-size:18px;line-height:18px;padding:0}label{float:left;width:100px;display:block;text-align:left;cursor:pointer;color:#333;margin:0 12px 0 0}.form-item{margin:0 0 11px}textarea,input{border:solid #ddd;border-width:1px 1px 2px;padding:4px}textarea{font-family:"Lucida Sans",Helvetica,sans-serif;font-size:11px}textarea:focus,input:focus{background:#f9f9f9;border:solid #ddd;border-width:1px 1px 2px}input.form-field-error,textarea.form-field-error{background:#FBE3E4;color:#8A1F11;border-color:#FBC2C4 #FBC2C4 #ee9b9e;border-style:solid;border-width:1px 1px 2px}input.form-field-notice,textarea.form-field-notice{background:#FFF6BF;color:#514721;border-color:#FFD324 #FFD324 #e3bb1b;border-style:solid;border-width:1px 1px 2px}select{border:1px solid #ccc;background:#f9f9f9;color:#333}input[type=checkbox],input[type=radio]{margin:3px 4px 0 0}input[type=radio]{background-color:#fff;color:#000}option{background:#fff;color:#000}optgroup{background:#f2f2f2;color:#111}a:hover,input[type=checkbox]{color:#000}

.hll { background-color: #ffffcc }
.c { color: #888888 } /* Comment */
.err { color: #a61717; background-color: #e3d2d2 } /* Error */
.k { color: #008800; font-weight: bold } /* Keyword */
.cm { color: #888888 } /* Comment.Multiline */
.cp { color: #cc0000; font-weight: bold } /* Comment.Preproc */
.c1 { color: #888888 } /* Comment.Single */
.cs { color: #cc0000; font-weight: bold; background-color: #fff0f0 } /* Comment.Special */
.gd { color: #000000; background-color: #ffdddd } /* Generic.Deleted */
.ge { font-style: italic } /* Generic.Emph */
.gr { color: #aa0000 } /* Generic.Error */
.gh { color: #303030 } /* Generic.Heading */
.gi { color: #000000; background-color: #ddffdd } /* Generic.Inserted */
.go { color: #888888 } /* Generic.Output */
.gp { color: #555555 } /* Generic.Prompt */
.gs { font-weight: bold } /* Generic.Strong */
.gu { color: #606060 } /* Generic.Subheading */
.gt { color: #aa0000 } /* Generic.Traceback */
.kc { color: #008800; font-weight: bold } /* Keyword.Constant */
.kd { color: #008800; font-weight: bold } /* Keyword.Declaration */
.kn { color: #008800; font-weight: bold } /* Keyword.Namespace */
.kp { color: #008800 } /* Keyword.Pseudo */
.kr { color: #008800; font-weight: bold } /* Keyword.Reserved */
.kt { color: #888888; font-weight: bold } /* Keyword.Type */
.m { color: #0000DD; font-weight: bold } /* Literal.Number */
.s { color: #dd2200; background-color: #fff0f0 } /* Literal.String */
.na { color: #336699 } /* Name.Attribute */
.nb { color: #003388 } /* Name.Builtin */
.nc { color: #bb0066; font-weight: bold } /* Name.Class */
.no { color: #003366; font-weight: bold } /* Name.Constant */
.nd { color: #555555 } /* Name.Decorator */
.ne { color: #bb0066; font-weight: bold } /* Name.Exception */
.nf { color: #0066bb; font-weight: bold } /* Name.Function */
.nl { color: #336699; font-style: italic } /* Name.Label */
.nn { color: #bb0066; font-weight: bold } /* Name.Namespace */
.py { color: #336699; font-weight: bold } /* Name.Property */
.nt { color: #bb0066; font-weight: bold } /* Name.Tag */
.nv { color: #336699 } /* Name.Variable */
.ow { color: #008800 } /* Operator.Word */
.w { color: #bbbbbb } /* Text.Whitespace */
.mf { color: #0000DD; font-weight: bold } /* Literal.Number.Float */
.mh { color: #0000DD; font-weight: bold } /* Literal.Number.Hex */
.mi { color: #0000DD; font-weight: bold } /* Literal.Number.Integer */
.mo { color: #0000DD; font-weight: bold } /* Literal.Number.Oct */
.sb { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Backtick */
.sc { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Char */
.sd { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Doc */
.s2 { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Double */
.se { color: #0044dd; background-color: #fff0f0 } /* Literal.String.Escape */
.sh { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Heredoc */
.si { color: #3333bb; background-color: #fff0f0 } /* Literal.String.Interpol */
.sx { color: #22bb22; background-color: #f0fff0 } /* Literal.String.Other */
.sr { color: #008800; background-color: #fff0ff } /* Literal.String.Regex */
.s1 { color: #dd2200; background-color: #fff0f0 } /* Literal.String.Single */
.ss { color: #aa6600; background-color: #fff0f0 } /* Literal.String.Symbol */
.bp { color: #003388 } /* Name.Builtin.Pseudo */
.vc { color: #336699 } /* Name.Variable.Class */
.vg { color: #dd7700 } /* Name.Variable.Global */
.vi { color: #3333bb } /* Name.Variable.Instance */
.il { color: #0000DD; font-weight: bold } /* Literal.Number.Integer.Long */

            .content .padding {
                padding: 30px 36px 30px 30px;
            }
             .item .padding {
                 padding: 0 12px 0 0;
             }
            .list-item h2 {
                margin: 0;
                line-height: 27px;
            }

            td {
                padding: 5px;
            }
    """

    HEADER_CLOSE = """
            </style>
        </head>
        <body>
            <div class="zp-wrapper">
            <div class="zp-70 content">
            <div class="padding">
    """

    FOOTER = """
            </div></div></div>
        </body>
    </html>
    """
    def process_text(self, input_text):
        return "%s%s%s%s%s" % (self.HEADER, self.arg_value("css", ""), self.HEADER_CLOSE, input_text, self.FOOTER)
