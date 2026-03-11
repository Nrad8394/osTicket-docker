<?php
/**
 * Patch for osTicket v1.18.3 - Fix function redeclaration in class.i18n.php
 * 
 * Issue: Internationalization::bootstrap() can be called multiple times,
 * causing functions _N(), _S(), _NS(), etc. to be redeclared.
 * 
 * Solution: Wrap function declarations in if (!function_exists(...)) guards
 */

$file = '/var/www/html/include/class.i18n.php';
$content = file_get_contents($file);

// Define replacements - wrap each function in if (!function_exists(...)) guard
$replacements = [
    // _N function
    [
        'from' => '        // User-specific translations
        function _N($msgid, $plural, $n) {',
        'to' => '        // User-specific translations
        if (!function_exists(\'_N\')) {
        function _N($msgid, $plural, $n) {'
    ],
    // _S function
    [
        'from' => '        // System-specific translations
        function _S($msgid) {',
        'to' => '        } // if (!function_exists(\'_N\'))
        // System-specific translations
        if (!function_exists(\'_S\')) {
        function _S($msgid) {'
    ],
    // _NS function
    [
        'from' => '        }
        function _NS($msgid, $plural, $count) {',
        'to' => '        }
        } // if (!function_exists(\'_S\'))
        if (!function_exists(\'_NS\')) {
        function _NS($msgid, $plural, $count) {'
    ],
    // _P function
    [
        'from' => '        }

        // Phrases with separate contexts
        function _P($context, $msgid) {',
        'to' => '        }
        } // if (!function_exists(\'_NS\'))
        // Phrases with separate contexts
        if (!function_exists(\'_P\')) {
        function _P($context, $msgid) {'
    ],
    // _NP function
    [
        'from' => '        }
        function _NP($context, $singular, $plural, $n) {',
        'to' => '        }
        } // if (!function_exists(\'_P\'))
        if (!function_exists(\'_NP\')) {
        function _NP($context, $singular, $plural, $n) {'
    ],
    // _L function
    [
        'from' => '        }

        // Language-specific translations
        function _L($msgid, $locale) {',
        'to' => '        }
        } // if (!function_exists(\'_NP\'))
        // Language-specific translations
        if (!function_exists(\'_L\')) {
        function _L($msgid, $locale) {'
    ],
    // _NL function and closing guard
    [
        'from' => '        }
        function _NL($msgid, $plural, $n, $locale) {
            return TextDomain::lookup()->getTranslation($locale)
                ->ngettext($msgid, $plural, is_numeric($n) ? $n : 1);
        }',
        'to' => '        }
        } // if (!function_exists(\'_L\'))
        if (!function_exists(\'_NL\')) {
        function _NL($msgid, $plural, $n, $locale) {
            return TextDomain::lookup()->getTranslation($locale)
                ->ngettext($msgid, $plural, is_numeric($n) ? $n : 1);
        }
        } // if (!function_exists(\'_NL\'))'
    ]
];

foreach ($replacements as $repl) {
    if (strpos($content, $repl['from']) === false) {
        echo "WARNING: Could not find expected text in $file. Patch may have already been applied.\n";
        echo "Looking for: " . substr($repl['from'], 0, 50) . "...\n";
    } else {
        $content = str_replace($repl['from'], $repl['to'], $content);
    }
}

// Write patched content back
if (file_put_contents($file, $content)) {
    echo "Successfully patched $file\n";
} else {
    echo "ERROR: Failed to write patched file $file\n";
    exit(1);
}
?>
