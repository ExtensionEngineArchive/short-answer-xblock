# Short Answer XBlock

This XBlock provides a way for students to submit short essayic texts.

An example student view:

![Student view](https://lh3.googleusercontent.com/U9mrh6sqvO2qIkTUXQKdB5ceG1jK1aXFXYCKh6Mu6lIdqwnlSv222lXTFkotRQQC4_AsORq-8JJP-BmJPDnm=w1920-h1014)

The submissions are manually graded in the block's modal window in LMS:

![Grading modal](https://lh3.googleusercontent.com/lvsbo-UlMuIwL1NdJ82XdCzNoTPE8aJ9YJAf3yA1i6sZlEZIY1f5_kAdOCO4A8ajwdtGQo-u076oTpDHpLTk=w1920-h1014-rw)

## Installation

Source into the virtual environment of your `edx-platform` application and from
this application's root directory run:

```bash
$ pip install -r requirements.txt
```

### JS Dependencies

Globally accessable:
* jQuery
* underscore.js
* moment.js

If you are using this block in the `eucalyptus.1` release or newer these
dependencies are already available.

## Enabling in Studio

In Studio go to the course where you want to use this block and open `Advanced
Settings` that are under the `Settings` top dropdown. The first option should be
`Advanced Module List` where you will append `"short_answer"` to enable this
XBlock for that course.
Once you have done that you should see the `Short Answer` option within the
`Advanced` section when adding new content to your units.
