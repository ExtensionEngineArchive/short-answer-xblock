/* Javascript for Studio part of ShortAnswerXBlock. */
function ShortAnswerStudioXBlock(runtime, element) {

  // Send a POST request to save the form data.
  $('.save-button', element).click(function(event) {
    event.preventDefault();

    const $btn = $(event.targetElement);
    const handlerUrl = runtime.handlerUrl(element, 'studio_submit');
    const data = {
      'display_name': $('#display_name-input', element).val(),
      'max_score': $('#max_score-input', element).val(),
      'weight': $('#weight-input', element).val(),
      'feedback': $('#feedback-input', element).val()
    };

    $.ajax({
      url: handlerUrl,
      method: 'POST',
      data: JSON.stringify(data),
      success: function(data) {
        window.location.reload(false);
      },
      error: function(err) {
        console.log('Error: ', err);
      }
    });
  });

  // Close modal on Cancel.
  $('.cancel-button', element).click(function(event) {
    runtime.notify('cancel', {});
  });

  $(function ($) {
    // On document load operations.
  });
}
