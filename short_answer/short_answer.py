"""Short Answer XBlock."""
from django.contrib.auth.models import User
from django.template import Context, Template
from django.utils.translation import ugettext_lazy as _  # pylint: disable=import-error
from webob.response import Response  # pylint: disable=import-error

import pkg_resources
from xblock.core import XBlock
from xblock.fields import Float, Integer, Scope, String
from xblock.fragment import Fragment


def load_resource(resource_path):
    """
    Gets the content of a resource
    """
    resource_content = pkg_resources.resource_string(__name__, resource_path)
    return unicode(resource_content)


def render_template(template_path, context=None):
    """
    Evaluate a template by resource path, applying the provided context.
    """
    if context is None:
        context = {}

    template_str = load_resource(template_path)
    template = Template(template_str)
    return template.render(Context(context))


def resource_string(path):
    """Handy helper for getting resources from our kit."""
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")


class ShortAnswerXBlock(XBlock):
    """
    This block defines a Short Answer. Students can submit a short answer and
    instructors can view, grade and add feedback to it.
    """
    has_score = True
    icons_class = 'problem'

    display_name = String(
        display_name=_('Display name'),
        default=_('Short Answer'),
        scope=Scope.settings,
        help=_('This name appears in the horizontal navigation at the top of '
               'the page.')
    )

    description = String(
        display_name=_('Description'),
        default=_('Submit your questions and observations in 1-2 short '
                  'paragraphs below.'),
        scope=Scope.settings,
        help=_('This name appears in the horizontal navigation at the top of '
               'the page.')
    )

    submission = String(
        display_name=_('Student answer submission'),
        default='',
        scope=Scope.user_state,
        help=_('Student submission.')
    )

    feedback = String(
        display_name=_('Instructor feedback'),
        default='',
        scope=Scope.settings,
        help=_('Message that will be shown to the student once the student '
               ' submits an answer.')
    )

    score = Integer(
        display_name=_('Student score'),
        default=0,
        scope=Scope.settings,
        help=_('Score given for this assignment.')
    )

    max_score = Integer(
        display_name=_('Maximum score'),
        default=100,
        scope=Scope.settings,
        help=_('Maximum grade score given to this assignment.')
    )

    weight = Float(
        display_name=_('Problem Weight'),
        default=0.0,
        values={'min': 0, 'step': .1},
        scope=Scope.settings,
        help=_('Defines the number of points the problem is worth.'),
    )

    @property
    def user(self):
        """Retrieve the user object from the user_id in xmodule_runtime."""
        return User.objects.get(id=self.xmodule_runtime.user_id)

    def studio_view(self, context=None):
        """View for the form when editing this block in Studio."""
        cls = type(self)
        context['fields'] = (
            (cls.display_name, getattr(self, 'display_name', ''), 'input', 'text'),
            (cls.max_score, getattr(self, 'max_score', ''), 'input', 'number'),
            (cls.weight, getattr(self, 'weight', ''), 'input', 'number'),
            (cls.feedback, getattr(self, 'feedback', ''), 'textarea', 'text'),
        )

        frag = Fragment()
        frag.add_content(
            render_template('static/html/short_answer_edit.html', context)
        )
        frag.add_css(resource_string('static/css/short_answer_edit.css'))
        frag.add_javascript(
            resource_string('static/js/src/short_answer_edit.js')
        )
        frag.initialize_js('ShortAnswerStudioXBlock')
        return frag

    def student_view(self, context=None):
        """
        The primary view of the ShortAnswerXBlock, shown to students
        when viewing courses.
        """
        context['feedback'] = self.feedback
        context['submission'] = self.submission
        frag = Fragment()
        frag.add_content(
            render_template('static/html/short_answer.html', context)
        )
        frag.add_css(resource_string('static/css/short_answer.css'))
        frag.add_javascript(resource_string('static/js/src/short_answer.js'))
        frag.initialize_js('ShortAnswerXBlock')
        return frag

    @XBlock.json_handler
    def student_submission(self, data, suffix=''):  # pylint: disable=unused-argument
        """Handle the student's answer submission."""
        self.submission = data.get('submission')
        return Response(status_code=201)

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):  # pylint: disable=unused-argument
        """Handle the Studio edit form request."""
        for key in data:
            setattr(self, key, data[key])
        return Response(status_code=201)
