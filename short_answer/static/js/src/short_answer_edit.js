/* Javascript for Studio part of ShortAnswerXBlock. */
function ShortAnswerStudioXBlock(runtime, element) {

  /**
   * Send a POST request to save the form data.
   */
  $('.save-button', element).click(function(event) {
    event.preventDefault();

    const $btn = $(event.targetElement);
    const handlerUrl = runtime.handlerUrl(element, 'submit_edit');
    const data = {
      'display_name': $('#display_name-input', element).val(),
      'description': $('#description-input', element).val(),
      'weight': $('#weight-input', element).val(),
      'width': $('#width-input', element).val(),
      'feedback': $('#feedback-input', element).val()
    };
    const dataValid = true;

    /* Data validation */
    if (data.weight <= 0) {
      $('#error-weight', element).html('Weight must be a positive number');
      dataValid = false;
    }

    if (dataValid)
      $.ajax({
        url: handlerUrl,
        method: 'POST',
        data: JSON.stringify(data),
        success: function(data) {
          window.location.reload(false);
        },
        error: function(err) {
          console.error('Error: ', err);
        }
      });
  });

  /**
   * Close modal on Cancel button click event.
   */
  $('.cancel-button', element).click(function(event) {
    runtime.notify('cancel', {});
  });
}
