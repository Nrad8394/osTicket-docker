<?php
/**
 * Patch for osTicket v1.18.3 - Fix namespace issues with global functions
 */

$files_to_patch = [
    '/var/www/html/include/class.mailer.php' => 'semicolon',
    '/var/www/html/include/class.session.php' => 'braced',
    '/var/www/html/include/class.mailfetch.php' => 'semicolon',
    '/var/www/html/include/class.mime.php' => 'semicolon',
    '/var/www/html/include/class.oauth2.php' => 'semicolon',
    '/var/www/html/include/class.mail.php' => 'semicolon',
];

$use_statements = "use function _S;\nuse function _N;\nuse function _NS;\nuse function _P;\nuse function _NP;\nuse function _L;\nuse function _NL;\nuse function __;";

foreach ($files_to_patch as $file => $style) {
    if (!file_exists($file)) {
        echo "SKIP: $file (not found)\n";
        continue;
    }
    
    $content = file_get_contents($file);
    
    if (strpos($content, 'use function') !== false) {
        echo "SKIP: $file (already patched)\n";
        continue;
    }
    
    if ($style === 'semicolon') {
        // Find "namespace osTicket\...;" and add use statements after it
        if (preg_match('/^(namespace osTicket[^;]+;)(\s*)/m', $content, $matches, PREG_OFFSET_CAPTURE)) {
            $pos = $matches[0][1] + strlen($matches[0][0]);
            $newline_pos = strpos($content, "\n", $matches[0][1]);
            if ($newline_pos !== false) {
                $insert_pos = $newline_pos + 1;
                $content = substr_replace($content, "\n" . $use_statements . "\n\n", $insert_pos, 0);
                file_put_contents($file, $content);
                echo "PATCHED (semicolon): $file\n";
                continue;
            }
        }
    } else if ($style === 'braced') {
        // Find "namespace osTicket\...{" and add use statements inside the block
        if (preg_match('/^(namespace osTicket[^{]+\{)\s*$/m', $content, $matches, PREG_OFFSET_CAPTURE)) {
            $end_of_namespace = $matches[0][1] + strlen($matches[0][0]);
            $next_line_start = strpos($content, "\n", $end_of_namespace - 1) + 1;
            $content = substr_replace($content, "    " . str_replace("\n", "\n    ", $use_statements) . "\n\n", $next_line_start, 0);
            file_put_contents($file, $content);
            echo "PATCHED (braced): $file\n";
            continue;
        }
    }
    
    echo "ERROR: Could not patch $file (style: $style)\n";
}

echo "Done.\n";
?>
