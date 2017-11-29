# Short Answer XBlock

This XBlock provides a way for students to submit short essayic texts.

## Installation

Source into the virtual environment of your `edx-platform` application and from
this application's root directory run:

```bash
$ pip install -r requirements.txt
```

## Enabling in Studio

In Studio go to the course where you want to use this block and open `Advanced
Settings` that are under the `Settings` top dropdown. The first option should be
`Advanced Module List` where you will append `"short_answer"` to enable this
XBlock for that course.
Once you have done that you should see the `Short Answer` option within the
`Advanced` section when adding new content to your units.
