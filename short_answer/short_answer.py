"""Short Answer XBlock."""
import datetime
import json
from io import BytesIO

import pytz
import unicodecsv  # pylint: disable=import-error
from django.db.models import Q
from django.contrib.auth.models import User
from django.template import Context, Template
from django.utils.translation import ugettext_lazy as _
from webob.response import Response  # pylint: disable=import-error

from courseware.models import StudentModule  # pylint: disable=import-error
from student.models import CourseEnrollment  # pylint: disable=import-error
from xmodule.util.duedate import get_extended_due_date  # pylint: disable=import-error

import pkg_resources
from xblock.core import XBlock  # pylint: disable=import-error
from xblock.fields import Boolean, DateTime, Float, Integer, Scope, String  # pylint: disable=import-error
from xblock.fragment import Fragment  # pylint: disable=import-error


def create_csv_row(row):
    """
    Convert a list into a CSV row.

    Args:
        row (list) - one CSV line
    Returns:
        A string with comma-separated values from the row list.
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
    instructors can view, grade, add feedback and download a CSV of all submissions.
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
        default=_('Your answer was submitted successfully.'),
        scope=Scope.settings,
        help=_('Message that will be shown to the student once the student submits an answer.')
    )

    weight = Integer(
        display_name="Problem Weight",
        help=("Defines the number of points each problem is worth. "
              "If the value is not set, the problem is worth the sum of the "
              "option point values."),
        values={"min": 0, "step": 1},
        default=100,
        scope=Scope.settings
    )

    score = Integer(
        display_name=_('Student score'),
        default=0,
        scope=Scope.settings,
        help=_('Score given for this assignment.')
    )

    grades_published = Boolean(
        display_name='Display grade to students',
        scope=Scope.user_state_summary,
        default=False,
        help='Indicates if the grades will be displayed to students.'
    )

    @property
    def module(self):
        """
        Retrieve the student module for current user.
        """
        module, _ = StudentModule.objects.get_or_create(
            course_id=self.course_id,
            module_state_key=self.location,
            student=self.user,
        )
        return module

    @property
    def passed_due(self):
        """
        Return true if the due date has passed.
        """
        now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
        due = get_extended_due_date(self)
        if due is not None:
            return now > due
        return False

    @property
    def student_grade(self):
        """
        Retrieve the manually added grade for the current user.
        """
        return self.module.grade

    @property
    def user(self):
        """
        Retrieve the user object from the user_id in xmodule_runtime.
        """
        return User.objects.get(id=self.xmodule_runtime.user_id)

    def max_score(self):
        return self.weight

    def studio_view(self, context=None):
        """
        View for the form when editing this block in Studio.
        """
        cls = type(self)
        context['fields'] = (
            (cls.display_name, getattr(self, 'display_name', ''), 'input', 'text'),
            (cls.description, getattr(self, 'description', ''), 'textarea', 'text'),
            (cls.feedback, getattr(self, 'feedback', ''), 'textarea', 'text'),
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
        js_options = {
            'gradesPublished': self.grades_published,
            'weight': self.weight,
            'passedDue': self.passed_due,
            'score': self.student_grade,
        }
        context.update({
            'answer': self.answer,
            'description': self.description,
            'feedback': self.feedback,
            'grades_published': self.grades_published,
            'is_course_staff': getattr(self.xmodule_runtime, 'user_is_staff', False),
            'weight': self.weight,
            'module_id': self.module.id,  # Use the module id to generate different pop-up modals
            'score': self.student_grade,
        })
        frag = Fragment()
        frag.add_content(render_template('static/html/short_answer.html', context))
        frag.add_css(resource_string('static/css/short_answer.css'))
        frag.add_javascript(resource_string('static/js/src/short_answer.js'))
        frag.initialize_js('ShortAnswerXBlock', js_options)
        return frag

    @XBlock.json_handler
    def student_submission(self, data, _):
        """
        Handle the student's answer submission.
        """
        if self.passed_due:
            return Response(
                status_code=400,
                body=json.dumps({'error': 'Submission due date has passed.'})
            )
        self.answer = data.get('submission')
        self.answered_at = datetime.datetime.now()
        return Response(status_code=201)

    @XBlock.json_handler
    def submit_edit(self, data, _):
        """
        Handle the Studio edit form request.
        """
        for key in data:
            setattr(self, key, data[key])
        return Response(status_code=201)

    @XBlock.json_handler
    def submit_grade(self, data, _):
        """
        Handle the grade submission request.
        """
        score = data.get('score')
        module_id = data.get('module_id')
        if not (score and module_id):
            error_msg_tpl = 'Missing {params} parameter.'
            if not (score or module_id):
                missing_params = 'score and module_id'
            else:
                missing_params = 'score' if not score else 'module_id'
            return Response(
                status_code=400,
                body=json.dumps({'error': error_msg_tpl.format(params=missing_params)})
            )

        if float(score) > self.weight:
            return Response(
                status_code=400,
                body=json.dumps({'error': 'Submitted score larger than the maximum allowed.'})
            )
        module = StudentModule.objects.get(pk=module_id)
        module.grade = float(score)
        module.max_grade = self.weight
        module.save()
        return Response(status_code=200, body=json.dumps({'new_score': module.grade}))

    # pylint: disable=no-self-use
    @XBlock.json_handler
    def remove_grade(self, data, _):
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

    @XBlock.handler
    def update_grades_published(self, request, suffix=''):
        self.grades_published = json.loads(request.params.get('grades_published'))
        return Response(status=200)

    def get_submissions_list(self):
        """
        Return a list of all enrolled students and their answer submission information.
        """
        enrollments = CourseEnrollment.objects.filter(
            course_id=self.course_id,
            is_active=True
        ).exclude(Q(user__is_staff=True) | Q(user__is_superuser=True))
        submissions_list = []

        for enrollment in enrollments:
            student = enrollment.user
            module, _ = StudentModule.objects.get_or_create(
                course_id=self.course_id,
                module_state_key=self.location,
                student=student,
                defaults={
                    'max_grade': self.weight,
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
                'maximum_score': self.weight,
                'module_id': module.id,
                'score': module.grade,
            })
        return submissions_list

    @XBlock.handler
    def answer_submissions(self, *args, **kwargs):  # pylint: disable=unused-argument
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
    def csv_download(self, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Handles the CSV download request.
        """
        response = Response(content_type='text/csv')
        response.content_disposition = 'attachment; filename="short_answer_submissions.csv"'
        response.app_iter = self.create_csv()

        return response
