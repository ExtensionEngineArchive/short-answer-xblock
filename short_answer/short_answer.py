"""Short Answer XBlock."""
import json

from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _  # pylint: disable=import-error
from webob.response import Response

import pkg_resources
from xblock.core import XBlock
from xblock.fields import Float, Integer, Scope, String
from xblock.fragment import Fragment


class ShortAnswerXBlock(XBlock):
    """
    This block defines a Short Answer. Students can submit a short answer and
    instructors can view, grade and add feedback to it.
    """
    has_score = True
    icons_class = 'problem'

    display_name = String(
        default=_('Short Answer'),
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
        scope=Scope.user_state,
        help=_('Feedback of the instructor.')
    )

    score = Integer(
        display_name=_('Student score'),
        default=None,
        scope=Scope.settings,
        help=_('Score given by instructor.')
    )

    max_score = Integer(
        display_name=_('Maximum score'),
        default=100,
        scope=Scope.settings,
        help=_('Maximum grade score given to assignment by staff.')
    )

    weight = Float(
        display_name=_('Problem Weight'),
        values={'min': 0, 'step': .1},
        scope=Scope.settings,
        help=_('Defines the number of points each problem is worth. '
               'If the value is not set, the problem is worth the sum of the '
               'option point values.'),
    )

    @property
    def user(self):
        return User.objects.get(id=self.xmodule_runtime.user_id)

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        """
        The primary view of the ShortAnswerXBlock, shown to students
        when viewing courses.
        """
        html = self.resource_string("static/html/short_answer.html")
        frag = Fragment(html.format(self=self))
        frag.add_css(self.resource_string("static/css/short_answer.css"))
        frag.add_javascript(self.resource_string("static/js/src/short_answer.js"))
        frag.initialize_js('ShortAnswerXBlock')
        return frag

    @XBlock.json_handler
    def student_submission(self, data, suffix=''):
        return Response(json_body=json.dumps({
            'feedback': 'Here is some feedback.'
        }))
