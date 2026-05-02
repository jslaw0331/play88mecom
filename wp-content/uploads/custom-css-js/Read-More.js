<!-- start Simple Custom CSS and JS -->
<script type="text/javascript">
jQuery(document).ready(function($) {
  $("#content").each(function() {
    const $this = $(this);
    const $text = $this.find(".text");
    const $button = $this.find(".read-more");

    // Check if content exceeds 5 lines
    const originalHeight = $text[0].scrollHeight;
    const lineHeight = parseFloat($text.css("line-height"));
    const maxLinesHeight = lineHeight * 5;

    if (originalHeight > maxLinesHeight) {
      $button.show(); // Show the button if text exceeds 5 lines
    }

    // Toggle Read More/Read Less
    $button.on("click", function() {
      $text.toggleClass("expanded");
      $button.text($text.hasClass("expanded") ? "Read Less" : "Read More");
    });
  });
});</script>
<!-- end Simple Custom CSS and JS -->
