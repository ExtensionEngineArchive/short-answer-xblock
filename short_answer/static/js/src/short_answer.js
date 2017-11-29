/* Javascript for ShortAnswerXBlock. */
function ShortAnswerXBlock(runtime, element) {

  $('button[type=submit]', element).click(function(event) {
    const $button = $(event.targetElement);
    const $error = $('p.error', element);
    const $feedback = $('.feedback', element);
    const submission = $('textarea', element).val();
    const handlerUrl = runtime.handlerUrl(element, 'student_submission');

    $button.attr('disabled', 'disabled');
    $error.text('');

    $.ajax({
      url: handlerUrl,
      method: 'POST',
      data: JSON.stringify({'submission': submission}),
      success: function(data) {
        $feedback.removeClass('hidden');
        $button.removeAttr('disabled');
      },
      error: function(err) {
        $error.text('An error occured.');
        console.error('Error: ', err);
      }
    });
  });

  $(function ($) {
    // On document load operations.
  });
}
