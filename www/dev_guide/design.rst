Design Decisions and Tradeoffs
==============================

(design)

Delimiters
----------

(design.Delimiters)

One of the first decisions we encountered was which delimiter
syntax to use. We decided to follow Velocity's {$placeholder} and
{#directive} syntax because the former is widely used in other
languages for the same purpose, and the latter stands out in an
HTML or text document. We also implemented the
``${longPlaceholder}`` syntax like the shells for cases where
Cheetah or you might be confused where a placeholder ends. Tavis
went ahead and made ``${longPlaceholder}`` and
``$[longPlaceholder]`` interchangeable with it since it was trivial
to implement. Finally, the {#compiler} directive allows you to
change the delimiters if you don't like them or if they conflict
with the text in your document. (Obviously, if your document
contains a Perl program listing, you don't necessarily want to
backslash each and every {$} and {#}, do you?)

The choice of comment delimiters was more arbitrary. {##} and {#\*
... \*#} doesn't match any language, but it's reminiscent of Python
and C while also being consistent with our "{#} is for directives"
convention.

We specifically chose { not} to use pseudo HTML tags for
placeholders and directives, as described more thoroughly in the
Cheetah Users' Guide introduction. Pseudo HTML tags may be easier
to see in a visual editor (supposedly), but in text editors they're
hard to distinguish from "real" HTML tags unless you look closely,
and they're many more keystrokes to type. Also, if you make a
mistake, the tag will show up as literal text in the rendered HTML
page where it will be easy to notice and eradicate, rather than
disappearing as bogus HTML tags do in browsers.

Late binding
------------

(design.lateBinding)

One of Cheetah's unique features is the name mapper, which lets you
write {$a.b} without worrying much about the type of {a} or {b}.
Prior to version 0.9.7, Cheetah did the entire NameMapper lookup at
runtime. This provided maximum flexibility at the expense of speed.
Doing a NameMapper lookup is intrinsically more expensive than an
ordinary Python expression because Cheetah has to decide what type
of container {a} is, whether the the value is a function (autocall
it), issue the appropriate Python incantation to look up {b} in it,
autocall again if necessary, and then convert the result to a
string.

To maximize run-time (filling-time) performance, Cheetah 0.9.7
pushed much of this work back into the compiler. The compiler
looked up {a} in the searchList at compile time, noted its type,
and generated an eval'able Python expression based on that.

This approach had two significant drawbacks. What if {a} later
changes type before a template filling? Answer: unpredictable
exceptions occur. What if {a} does not exist in the searchList at
compile time? Answer: the template can't compile.

To prevent these catastrophes, users were required to prepopulate
the searchList before instantiating the template instance, and then
not to change {a}'s type. Static typing is repugnant in a dynamic
language like Python, and having to prepopulate the searchList made
certain usages impossible. For example, you couldn't instantiate
the template object without a searchList and then set {self}
attributes to specify the values.

After significant user complaints about the fragility of this
system, Tavis rewrote placeholder handling, and in version 0.9.8a3
(August 2001), Tavis moved the name mapper lookup back into
runtime. Performance wasn't crippled because he discovered that
writing a C version of the name mapper was easier than anticipated,
and the C version completed the lookup quickly. Now Cheetah had
"late binding", meaning the compiler does not look up {a} or care
whether it exists. This allows users to create {a} or change its
type anytime before a template filling.

The lesson we learned is that it's better to decide what you want
and then figure out how to do it, rather than assuming that certain
goals are unattainable due to performance considerations.

Caching framework
-----------------

(design.cache)

Webware compatibility and the transaction framework
---------------------------------------------------

(design.webware)

Single inheritance
------------------

(design.singleInheritance)


