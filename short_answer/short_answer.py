"""Short Answer XBlock."""
import datetime
from io import BytesIO
import json

import pytz
import unicodecsv
from django.contrib.auth.models import User
from django.template import Context, Template
from django.utils.translation import ugettext_lazy as _
from webob.response import Response

from courseware.models import StudentModule
from student.models import CourseEnrollment
from xmodule.util.duedate import get_extended_due_date

import pkg_resources
from xblock.core import XBlock
from xblock.fields import DateTime, Float, Integer, Scope, String
from xblock.fragment import Fragment


def create_csv_row(row):
    """
    Covert a list into a CSV row.
    """
    stream = BytesIO()
    writer = unicodecsv.writer(stream, encoding='utf-8')
    writer.writerow(row)
    stream.seek(0)
    return stream.read()


def load_resource(resource_path):
    """
    Gets the content of a resource.
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
    """
    Handy helper for getting resources from our kit.
    """
    data = pkg_resources.resource_string(__name__, path)
    return data.decode("utf8")


class ShortAnswerXBlock(XBlock):
    """
    This block defines a Short Answer. Students can submit a short answer and
    instructors can view, grade and add feedback to it.
    """
    has_score = True
    icons_class = 'problem'

    answer = String(
        display_name=_('Student\'s answer'),
        default='',
        scope=Scope.user_state,
        help=_('Text the student entered as answer.')
    )

    answered_at = DateTime(
        display_name=_('Answer submission time.'),
        default=None,
        scope=Scope.user_state,
        help=_('Time and date when the answer has been submitted.')
    )

    description = String(
        display_name=_('Description'),
        default=_('Submit your questions and observations in 1-2 short paragraphs below.'),
        scope=Scope.settings,
        help=_('Description that appears above the text input area.')
    )

    display_name = String(
        display_name=_('Display name'),
        default=_('Short Answer'),
        scope=Scope.settings,
        help=_('This name appears in the horizontal navigation at the top of the page.')
    )

    feedback = String(
        display_name=_('Instructor feedback'),
        default='',
        scope=Scope.settings,
        help=_('Message that will be shown to the student once the student submits an answer.')
    )

    maximum_score = Integer(
        display_name=_('Maximum score'),
        default=100,
        scope=Scope.settings,
        help=_('Maximum score given for this assignment.')
    )

    score = Integer(
        display_name=_('Student score'),
        default=0,
        scope=Scope.settings,
        help=_('Score given for this assignment.')
    )

    weight = Float(
        display_name=_('Problem Weight'),
        default=1.0,
        values={'min': 0},
        scope=Scope.settings,
        help=_('Defines the number of points the problem is worth.'),
    )

    @property
    def user(self):
        """
        Retrieve the user object from the user_id in xmodule_runtime.
        """
        return User.objects.get(id=self.xmodule_runtime.user_id)

    def passed_due(self):
        """
        Return true if the due date has passed.
        """
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        due = get_extended_due_date(self)
        if due is not None:
            return now > due
        return False

    def studio_view(self, context=None):
        """
        View for the form when editing this block in Studio.
        """
        cls = type(self)
        context['fields'] = (
            (cls.display_name, getattr(self, 'display_name', ''), 'input', 'text'),
            (cls.description, getattr(self, 'description', ''), 'textarea', 'text'),
            (cls.feedback, getattr(self, 'feedback', ''), 'textarea', 'text'),
            (cls.maximum_score, getattr(self, 'maximum_score', ''), 'input', 'number'),
            (cls.weight, getattr(self, 'weight', ''), 'input', 'number'),
        )

        frag = Fragment()
        frag.add_content(render_template('static/html/short_answer_edit.html', context))
        frag.add_css(resource_string('static/css/short_answer_edit.css'))
        frag.add_javascript(resource_string('static/js/src/short_answer_edit.js'))
        frag.initialize_js('ShortAnswerStudioXBlock')
        return frag

    def student_view(self, context=None):
        """
        The primary view of the ShortAnswerXBlock, shown to students
        when viewing courses.
        """
        context.update({
            'answer': self.answer,
            'description': self.description,
            'feedback': self.feedback,
            'is_course_staff': getattr(self.xmodule_runtime, 'user_is_staff', False),
            'passed_due': self.passed_due(),
        })
        frag = Fragment()
        frag.add_content(render_template('static/html/short_answer.html', context))
        frag.add_css(resource_string('static/css/short_answer.css'))
        frag.add_javascript(resource_string('static/js/src/short_answer.js'))
        frag.initialize_js('ShortAnswerXBlock')
        return frag

    @XBlock.json_handler
    def student_submission(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Handle the student's answer submission.
        """
        if self.passed_due():
            return Response(
                status_code=400,
                body=json.dumps({'error': 'Submission due date has passed.'})
            )
        self.answer = data.get('submission')
        self.answered_at = datetime.datetime.now()
        return Response(status_code=201)

    @XBlock.json_handler
    def studio_submit(self, data, suffix=''):  # pylint: disable=unused-argument
        """
        Handle the Studio edit form request.
        """
        for key in data:
            setattr(self, key, data[key])
        return Response(status_code=201)

    @XBlock.json_handler
    def submit_grade(self, data, suffix=''):
        """
        Handle the grade submission request.
        """
        score = data.get('score')
        module_id = data.get('module_id')
        if not (score and module_id):
            return Response(
                status_code=400,
                body=json.dumps({'error': 'Missing score and/or module_id parameters.'})
            )

        if int(score) > self.maximum_score:
            return Response(
                status_code=400,
                body=json.dumps({'error': 'Submitted score larger than the maximum allowed.'})
            )

        module = StudentModule.objects.get(pk=module_id)
        module.grade = float(score)
        module.max_grade = self.maximum_score
        module.save()
        return Response(status_code=200, body=json.dumps({'new_score': module.grade}))

    @XBlock.json_handler
    def remove_grade(self, data, suffix=''):
        """
        Handle the grade removal request.
        """
        module_id = data.get('module_id')
        if not module_id:
            return Response(
                status_code=400,
                body=json.dumps({'error': 'Missing module_id parameters.'})
            )

        module = StudentModule.objects.get(pk=module_id)
        module.grade = None
        module.save()
        return Response(status_code=200)

    def get_submissions_list(self):
        """
        Return a list of all enrolled students and their answer submission information.
        """
        enrollments = CourseEnrollment.objects.filter(
            course_id=self.course_id,
            is_active=True
        )
        submissions_list = []

        for enrollment in enrollments:
            student = enrollment.user
            module, _ = StudentModule.objects.get_or_create(
                course_id=self.course_id,
                module_state_key=self.location,
                student=student,
                defaults={
                    'max_grade': self.maximum_score,
                    'module_type': self.category,
                    'state': '{}',
                }
            )
            state = json.loads(module.state)
            submissions_list.append({
                'answer': state.get('answer'),
                'answered_at': str(state.get('answered_at')),
                'email': student.email,
                'fullname': student.profile.name,
                'maximum_score': self.maximum_score,
                'module_id': module.id,
                'score': module.grade,
            })
        return submissions_list

    @XBlock.handler
    def answer_submissions(self, *args, **kwargs):
        """
        Return the submission information of the enrolled students.
        """
        submissions_list = self.get_submissions_list()
        return Response(status_code=200, body=json.dumps(submissions_list))

    def create_csv(self):
        """
        CSV file generator. Yields a CSV line in each iteration.
        """
        submission_list = self.get_submissions_list()
        yield create_csv_row(['Name', 'Email', 'Answer', 'Answered at', 'Score'])

        for entry in submission_list:
            yield create_csv_row([
                entry.get('fullname'),
                entry.get('email'),
                entry.get('answer', ''),
                entry.get('answered_at', ''),
                entry.get('score')
            ])

    @XBlock.handler
    def csv_download(self, *args, **kwargs):
        """
        Handles the CSV download request.
        """
        response = Response(content_type='text/csv')
        response.content_disposition = 'attachment; filename="short_answer_submissions.csv"'
        response.app_iter = self.create_csv()

        return response
