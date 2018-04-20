/* Javascript for ShortAnswerXBlock. */
function ShortAnswerXBlock(runtime, element, options) {
  const $answerSubmitButton = $('.answer-submission-button', element);
  const $shortAnswer = $('.short-answer', element);
  const gradesPublished = options.gradesPublished;
  const maxScore = options.weight;
  const passedDue = options.passedDue;
  const score = options.score;
  // Variables that depend on other variables.
  const shouldDisableAnswerTextArea = gradesPublished || passedDue;

  /**
   * Display errors from the server or a default error message if no error
   * message was received from the server.
   */
  function displayError(cls, err) {
    const msg = (err.responseJSON) ? err.responseJSON.error || err.statusText : 'An error occured.';
    console.error(err);
    $(cls).text('Error: ' + msg);
  }

  function clearErrors() {
    $('.error, .modal-error').text('');
  }

  /**
   * Close the score editing fields in the modal window.
   */
  function closeEditing() {
    $('span.score', element).removeClass('hidden');
    $('input[name=score-input]', element).addClass('hidden');
    $('.submit-grade-form', element).addClass('hidden');
    $('.action-buttons', element).removeClass('hidden')
  }

  /**
   * Check condition to verify that submiting is allowed.
   */
  function isSubmitDisallowed() {
    return gradesPublished || passedDue || isAnswerTextAreaEmpty();
  }

  /**
   * Check if the answer text area is empty.
   */
  function isAnswerTextAreaEmpty() {
    return !$shortAnswer.val();
  }

  /**
   * Check if the value sent is a number between 0 and 100.
   */
  function is_score_valid(score) {
    return score !== '' && !isNaN(score) && 0 <= score && score <= maxScore;
  }

  /**
   * Populate the submissions table in the modal window and
   * bind all the buttons for each row.
   */
  function populateSubmissions(submissions) {
    const $tableBody = $('.submissions-list tbody', element);
    const template = _.template($('.answer-table-row-tpl', element).text());

    $tableBody.empty();
    clearErrors();

    submissions.forEach(function(submission) {
      submission.answer = submission.answer || '';
      if (submission.answered_at !== 'None') {
        submission.answered_at = moment(submission.answered_at).format('MMM Do YYYY, HH:mm');
      } else {
        submission.answered_at = ''
      }
      submission.score = submission.score || '';

      $(template(submission)).appendTo($tableBody);
    });

    // Save grades published value when checkbox clicked
    $('input[name=grades-published]', element).change(function() {
      var updateGradesPublishedUrl = runtime.handlerUrl(element, 'update_grades_published')
      var url = updateGradesPublishedUrl + '?grades_published=' + this.checked;

      $.get(url, function() {
          console.log('Student grade visibility updated.');
      }).fail(function() {
          alert('Something went wrong. Please contact the support team.');
      })
    });

    $('button[name=toggle-answer]', element).click(function() {
      const $answer = $(this).siblings('.answer');
      const btnText = ($answer.hasClass('hidden')) ? 'Hide answer' : 'Show answer';

      $(this).text(btnText);
      $answer.toggleClass('hidden');
    });

    $('button[name=change-grade]', element).click(function() {
        const $row = $(this).parents('tr');

        closeEditing();
        $('.score', $row).addClass('hidden');
        $('input[name=score-input]', $row).removeClass('hidden');
        $('.submit-grade-form', $row).removeClass('hidden');
        $('.action-buttons', $row).addClass('hidden');
      });

    $('button[name=remove-grade]', element).click(function() {
      const $scoreCell = $(this).parents('tr').find('.score');
      const moduleId = $(this).data('module-id');
      const removeGradeHandlerUrl = runtime.handlerUrl(element, 'remove_grade');

      clearErrors();
      $.ajax({
        url: removeGradeHandlerUrl,
        method: 'POST',
        data: JSON.stringify({
          module_id: moduleId
        }),
        success: function() {
          $scoreCell.text('');
        },
        error: function(err) {
          displayError('.modal-error', err);
        }
      });
    });

    $('button[name=submit-grade]', element).click(function() {
        const $row = $(this).parents('tr');
        const moduleId = $(this).data('module-id');
        const gradingHandlerUrl = runtime.handlerUrl(element, 'submit_grade');
        const score = $('input[name=score-input]', $row).val();

        if (!is_score_valid(score)) {
          $('.modal-error', element).text('The grade should be a positive number between 0-' + maxScore);
          return;
        }

        closeEditing();
        clearErrors();
        $.ajax({
          url: gradingHandlerUrl,
          method: 'POST',
          data: JSON.stringify({
            module_id: moduleId,
            score: score
          }),
          success: function(data) {
            $('.score', $row).text(data.new_score)
          },
          error: function(err) {
            displayError('.modal-error', err);
          }
        });
      });

    $('button[name=cancel]', element).click(closeEditing);
  }

  /**
   * Handler for the 'Submit' answer click. Posts the score to the server's
   * submission endpoint and displays feedback and error if any occur.
   */
  $('.answer-submission-button', element).click(function() {
    const $button = $(this);
    const $feedback = $('.feedback', element);
    const handlerUrl = runtime.handlerUrl(element, 'student_submission');
    const submission = $('textarea', element).val();

    $button.attr('disabled', 'disabled');
    clearErrors();

    $.ajax({
      url: handlerUrl,
      method: 'POST',
      data: JSON.stringify({'submission': submission}),
      success: function(data) {
        $feedback.removeClass('hidden');
        $button.removeAttr('disabled');
      },
      error: function(err) {
        displayError('.error', err);
      }
    });
  });

  /**
   * Display the modal window.
   */
  $('.submissions-button', element)
    .leanModal({position: 'relative', top: 50})
    .click(function(event) {
      const handlerUrl = runtime.handlerUrl(element, 'answer_submissions');

      clearErrors();
      $.ajax({
        url: handlerUrl,
        method: 'GET',
        success: populateSubmissions,
        error: function(err) {
          displayError('.modal-error', err);
        }
    });
  });

  /**
   * Enable/Disable the submit button.
   */
  $shortAnswer.keyup(function() {
    $answerSubmitButton.attr('disabled', isSubmitDisallowed());
  });

  $(function($) {
    const csvDownloadUrl = runtime.handlerUrl(element, 'csv_download');
    $('form[name=csv-download]', element).attr('action', csvDownloadUrl);

    $answerSubmitButton.attr('disabled', isSubmitDisallowed());
    $shortAnswer.attr('disabled', shouldDisableAnswerTextArea);
  });
}
