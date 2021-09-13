# Protopy

A library and CLI for rendering directory trees.

It is composed of two projects:

- A command-line utility that creates scaffolding for files and projects from templates.
- A library that allows for embedding into other applications with minimal dependencies

## How does it work

A protopy template is a directory which contains at least a `proto.py` file. Inside this directory, we create the
directory tree to be copied into the generated path. Protopy uses [jinja](https://jinja.palletsprojects.com/en/3.0.x/)
to render its templates, the rendering happens both on the file/dir names and inside any file that ends with `.tmpl`.

## Example

The following is the directory structure of a template we will use as our example.

```
our-template/
├── {{project_name}}
│   ├── {{readme_file_name}}
│   ├── src
│   │   └── main.py
│   └── {{tests_dir}}
└── proto.py
```

Note that we have a directory named `{{project_name}}` and a file named `{{readme_file_name}}` (yes, the file and
directory names include the double-curly-braces, just as you see them here), This means that this template
expects `proto.py` to define at least those variables.

Here is an example content for `proto.py`:

```python
# this is the main template logic.
# after the execution of this file, the module variables will be visible to the renderer of the directory tree to be copied into the generated path. 

# you can ask the user for input like the following, which results in the prompt:  "> Project Name:"
# the 'project_name' also represents the name of a commandline variable, we will see more about it down this example 
project_name = ask('project_name')

# you can also set default and explicit prompt
author = ask('author', prompt='Who are you?', default="no one")

# you can restrict input to a set of choices
readme_type = ask('readme_type', prompt='What Type of README file would you like?', default=0,
                  choices=["Markdown", "reStructuredText"])

# you can create module variables like any python module - you don't have to ask for them.. 
if readme_type == "Markdown":
    readme_file_name = "README.md.tmpl"
else:
    readme_file_name = "README.rst.tmpl"

# you can ask for yes/no confirmation like this:
tests_dir = ""
if confirm("use_tests", prompt="Would you like a tests directory?"):
    tests_dir = "tests"

# when calling from the commandline the user can supply named args and positional args,
# in the example below, if the user executed protopy with either the commands:
# > protopy <your template name> "My Protopy-Generated Project"
# > protopy <your template name> description="My Protopy-Generated Project"
# then the user will not get any prompt and the value "My Protopy-Generated Project" will be returned 
description = ask('description', positional_arg=0)

# you can print additional information to the user using the say command, it supports terminal formatting (read the doc for more info): 
say("<info>Done configuring and start generating!</info>")


# finally you can optionally define a post generation hook
def post_generation():
    say("<info>Done generating!</info>")

# Check out the docs for more information..
```

Notice the file named `readme_file_name` in the directory structure, this file gets its value inside `proto.py`. It has
2 possible values `README.md.tmpl` and `README.rst.tmpl`, since the file extension is `tmpl` its content will be
rendered using `jinja`.

Here is an example content of the `{{readme_file_name}}` file:

```markdown
# {{project_name}}

> Created By {{author}}

{{description}}
```

Next, we can see that there is a directory named `{{tests_dir}}` in our template, by examining the `proto.py` file we
can see that the `tests_dir` variable can be empty, this will result in a file/directory without a name in the rendering
phase which will cause the file/dir to not be rendered (in other words the `{{tests_dir}}` directory may not exist).

Finally we can generate a project based on this template via:

```console
> protopy generate our-template output-dir project_name="example"
Who are you? [no one] > John            
What Type of README file would you like? [Markdown]:
 [0] Markdown
 [1] reStructuredText
 > 
Would you like a tests directory? (yes/no) [yes] no
Description > our example description
Done configuring and start generating! 
Done generating! 
```

Notice that the user was not asked about the Project name as we supplied it in the commandline. The resulted content
of `output-dir` is:

```
.
└── example
    ├── README.md
    └── src
        └── main.py
```

and the content of README.md is:

```markdown
# example

> Created By John

our example description
```

## CLI Commands

Protopy supports the following commands:

### New

```
Description:
  create a new template (and populate it with some example content)

Usage:
  protopy new [<out_dir>]

Arguments:
  out_dir   directory to create the template in, defaults to the current directory

```

### Generate

```
Description:
  generate directory tree based on a given template

Usage:
  protopy generate <template> <output_path> [<template_args>...]

Arguments:
  template         the template to use (supports path, git, zip, url to zip, global template ref (with #))
  output_path      where to put the generated content
  template_args    template arguments, can be positional and key=value

```

The `generate` command support generating templates from different sources:

- Local directory: `protopy generate /path/to/dir ...`
- Local zip file: `protopy generate /path/to/zip/file.zip ...`
- Remote zip file: `protopy generate https://url-to-zip-file.zip ...`
- Git repository: `protopy generate git+https://github.com/...`

## The `proto.py` file

The `proto.py` file executes before the directory tree generation starts. Any (module level) variable that is defined
in `proto.py` will then be available to the `jinja` templates in the generation process. After the generation completes,
if `proto.py` defined a module level `post_generation` function it will be called.

During its execution, `proto.py` has several special methods that are supplied to it by protopy:

```python

def ask(named_arg: str, *, prompt: str = None, default: Any = "", choices: Optional[List[str]] = None,
        autocomplete: Optional[List[str]] = None, secret: bool = False, positional_arg: int = -1):
    """
    ask the user for information (either retrieving it from the command line or from the user supplied arguments)
    :param named_arg: the name of the argument that may contain the value for this function to return
    :param prompt: (optional - defaults to a string generated from named_arg) the prompt to show to the user
    :param default: (optional - defaults to None) the default value to suggest the user
    :param choices: (optional - defaults to None) list of choices to restrict the user input to
    :param autocomplete: (optional - defaults to None) list of autocomplete suggestions to help the user with
    :param secret: (optional - defaults to False) set to True to hide the user input
    :param positional_arg:  (optional - defaults to -1) the number of the positional argument that may contain the
                            value for this function to return
    :return: the requested user input
    """


def confirm(named_arg: str, *, prompt: str, default: bool = True, positional_arg: int = -1) -> bool:
    """
    ask the user for yes/no confirmation (either retrieving it from the command line or from the user supplied arguments)
    :param named_arg: the name of the argument that may contain the value for this function to return (supports the values y,yes,n,no)
    :param prompt: (optional - defaults to a string generated from named_arg) the prompt to show to the user
    :param default: (optional - defaults to True = 'yes') the default value to suggest the user
    :param positional_arg: (optional - defaults to -1) the index of the positional argument that may contain the
                            value for this function to return
    :return: True if the user confirmed or False otherwise
    """


def say(msg: str):
    """
    display a message to the user
    :param msg: the message to display 
    """

```

Internally, Protopy uses [cleo](https://github.com/sdispater/cleo) for terminal IO, therefore all prompts support output
coloring. You can read about it [here](https://cleo.readthedocs.io/en/latest/introduction.html#coloring-the-output), but
here is the gist of it:

```python
# Use predefined colors.
say('<info>hi there</info>')
say('<comment>hi there</comment>')
say('<question>hi there</question>')
say('<error>hi there</error>')

# Define your own colors.
# Available foreground and background colors are: black, red, green, yellow, blue, magenta, cyan and white.
# And available options are: bold, underscore, blink, reverse and conceal.
say('<fg=green>hi there</>')
say('<fg=black;bg=cyan>hi there</>')
say('<bg=yellow;options=bold>hi there</>')
```

## Advanced Templating

### Excluding files

Sometimes, your template may contain files that you want to exclude from the rendering process. You can use
a `.protopyignore` file for that (just add glob patterns to it similar to `.gitignore` file)

### Dynamic file positioning

When generating file/dir names, you can give the file a name that includes a relative path and the file will be
relocated into this path during the generation process.

For example, For a template structure:

```
dynamic-template/
├── {{dynamically_positioned_file}}
└── proto.py
```

And a proto.py file:

```python
# proto.py
dynamically_positioned_file = "some/nested/directory/file.txt"
```

running the command

```console
> protopy generate dynamic-template out-dir
```

will result with the directory structure:

```
out-dir/
└── some
    └── nested
        └── directory
            └── file.txt
```

## The Protopy library (`protopy_lib`)

The Protopy library (protopy_lib) includes the Protopy engine itself without the commandline and support for multiple
template sources. It has minimal set of dependencies and is intended for embedding inside other applications.

it exposes the following class:

```python

class ProtopyEngine:

    def render(self, template_dir: Union[Path, str], target_dir: Union[Path, str],
               args: List[str], kwargs: Dict[str, str], excluded_files: Optional[List[Path]] = None):
        """
        renders the given template into the target directory
        
        :param template_dir: the directory holding the template 
        :param target_dir: the directory to output the generated content into
        :param args: positional arguments for the template
        :param kwargs: named arguments for the template
        :param excluded_files:  list of path objects that represents files in the template directory that should be 
                                excluded from the generation process
        """

```

## Comparison to other tools

Protopy is very similar in concept to [cookiecutter](https://github.com/cookiecutter/cookiecutter)
and [copier](https://github.com/copier-org/copier/) but has the following differences:

- No configuration, instead a regular python code is being used.
- Composed of two parts - library and cli to support embedding without unneeded dependencies
- Does not directly support template updates 
- Allows for dynamic file positioning, as it intended to be used both for generating projects and also scaffolding
  software components

## How to build this project
This project is built using [relaxed-poetry](https://github.com/bennylut/relaxed-poetry)