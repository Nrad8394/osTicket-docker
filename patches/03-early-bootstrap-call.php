<?php
/**
 * Patch for osTicket v1.18.3 - Call Internationalization::bootstrap() early
 * 
 * Issue: When Bootstrap::connect() fails, it tries to send error emails which use _S()
 * But _S() is not defined until Internationalization::bootstrap() is called, which
 * happens in osTicket::start() - AFTER Bootstrap::connect().
 * 
 * Solution: Call Internationalization::bootstrap() before Bootstrap::connect()
 */

$file = '/var/www/html/main.inc.php';
$content = file_get_contents($file);

// Check if already patched
if (strpos($content, 'Internationalization::bootstrap()') !== false) {
    echo "SKIP: main.inc.php already patched\n";
    exit;
}

// Find the line "Bootstrap::connect();" and add a call to Internationalization::bootstrap() before it
$pattern = '/^(Bootstrap::connect\(\);)/m';

if (preg_match($pattern, $content)) {
    $replacement = 'Internationalization::bootstrap();' . "\n" . '$1';
    $content = preg_replace($pattern, $replacement, $content, 1, $count);
    
    if ($count === 1 && file_put_contents($file, $content)) {
        echo "PATCHED: Added early Internationalization::bootstrap() call\n";
    } else {
        echo "ERROR: Could not patch main.inc.php\n";
        exit(1);
    }
} else {
    echo "ERROR: Could not find Bootstrap::connect() in main.inc.php\n";
    exit(1);
}

?>
