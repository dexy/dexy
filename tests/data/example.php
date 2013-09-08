<html>
<!-- @section "head" -->
<head>
<title>PHP Example</title>
</head>
<!-- @end -->
<?php

// examples taken from http://www.php.net/manual/en and modified

/// "assign-variables"
$b = $a = 5;
$a++;

/// "compare"
if ($a > $b) {
  echo "<p>a ($a) is bigger than b ($b)</p>";
  $b = $a;
}
/// @end
?>
<!-- @section "display-variables" -->
<?php
    echo "The value of a is $a."
?>
<!-- @end -->
</html>
