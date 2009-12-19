Introduction
============

Who should read this Guide?
---------------------------

The Cheetah Developers' Guide is for those who want to learn how
Cheetah works internally, or wish to modify or extend Cheetah. It
is assumed that you've read the Cheetah Users' Guide and have an
intermediate knowledge of Python.

Contents
--------

This Guide takes a behaviorist approach. First we'll look at what
the Cheetah compiler generates when it compiles a template
definition, and how it compiles the various $placeholder features
and #directives. Then we'll stroll through the files in the Cheetah
source distribution and show how each file contributes to the
compilation and/or filling of templates. Then we'll list every
method/attribute inherited by a template object. Finally, we'll
describe how to submit bugfixes/enhancements to Cheetah, and how to
add to the documentation.

Appendix A will contain a BNF syntax of the Cheetah template
language.


