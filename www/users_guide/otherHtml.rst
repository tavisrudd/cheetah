non-Webware HTML output
=======================

(otherHTML)

Cheetah can be used with all types of HTML output, not just with
Webware.

Static HTML Pages
-----------------

(otherHTML.static)

Some sites like Linux Gazette (http://www.linuxgazette.com/)
require completely static pages because they are mirrored on
servers running completely different software from the main site.
Even dynamic sites may have one or two pages that are static for
whatever reason, and the site administrator may wish to generate
those pages from Cheetah templates.

There's nothing special here. Just create your templates as usual.
Then compile and fill them whenever the template definition
changes, and fill them again whenever the placeholder values
change. You may need an extra step to copy the .html files to their
final location. A Makefile (chapter tips.Makefile) can help
encapsulate these steps.

CGI scripts
-----------

(otherHTML)

Unlike Webware servlets, which don't have to worry about the HTTP
headers, CGI scripts must emit their own headers. To make a
template CGI aware, add this at the top:

::

    #extends Cheetah.Tools.CGITemplate
    #implements respond
    $cgiHeaders#slurp

Or if your template is inheriting from a Python class:

::

    #extends MyPythonClass
    #implements respond
    $cgiHeaders#slurp

A sample Python class:

::

    from Cheetah.Tools import CGITemplate
    class MyPythonClass(CGITemplate):
        def cgiHeadersHook(self):
            return "Content-Type: text/html; charset=koi8-r\n\n"

Compile the template as usual, put the .py template module in your
cgi-bin directory and give it execute permission. {.cgiHeaders()}
is a "smart" method that outputs the headers if the module is
called as a CGI script, or outputs nothing if not. Being
"called as a CGI script" means the environmental variable
{REQUEST\_METHOD} exists and {self.isControlledByWebKit} is false.
If you don't agree with that definition, override {.isCgi()} and
provide your own.

The default header is a simple ``Content-type: text/html\n\n``,
which works with all CGI scripts. If you want to customize the
headers (e.g., to specify the character set), override
{.cgiHeadersHook()} and return a string containing all the headers.
Don't forget to include the extra newline at the end of the string:
the HTTP protocol requires this empty line to mark the end of the
headers.

To read GET/POST variables from form input, use the {.webInput()}
method (section webware.webInput), or extract them yourself using
Python's {cgi} module or your own function. Although {.webInput()}
was originally written for Webware servlets, it now handles CGI
scripts too. There are a couple behavioral differences between CGI
scripts and Webware servlets regarding input variables:


#. CGI scripts, using Python's {cgi} module, believe
   {REQUEST\_METHOD} and recognize { either} GET variables { or} POST
   variables, not both. Webware servlets, doing additional processing,
   ignore {REQUEST\_METHOD} and recognize both, like PHP does.

#. Webware servlets can ask for cookies or session variables
   instead of GET/POST variables, by passing the argument {src='c'} or
   {src='s'}. CGI scripts get a {RuntimeError} if they try to do
   this.


If you keep your .tmpl files in the same directory as your CGI
scripts, make sure they don't have execute permission. Apache at
least refuses to serve files in a {ScriptAlias} directory that
don't have execute permission.


