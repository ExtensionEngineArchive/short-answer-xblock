/* Javascript for ShortAnswerXBlock. */
function ShortAnswerXBlock(runtime, element) {

    function onError(error) {
        $('p.error', element).text('An error occured.');
        console.error('Error: ', error);
    }

    $('button[type=submit]', element).click(function(event) {
        const $block = $(event.targetElement);
        const content = $('textarea', element).val();
        const handlerUrl = runtime.handlerUrl(element, 'student_submission');

        $.ajax({
            url: handlerUrl,
            method: 'POST',
            data: JSON.stringify({'content': content}),
            success: function(data) {
                const response = JSON.parse(data);
                console.log('SUCCESS: ', data);
                if (response.feedback) {
                    $('.feedback p', element).text(response.feedback);
                }
            },
            error: onError
        });
    });

    $(function ($) {
        // On document load operations.
    });
}
