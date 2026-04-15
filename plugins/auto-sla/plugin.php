<?php
/**
 * Auto SLA by Type + Severity - osTicket plugin
 *
 * Automatically assigns an SLA Plan to a ticket based on two custom fields:
 * "type" (e.g. Enhancement, Bug, New System) and "severity" (Major, Medium, Minor).
 */
return array(
    'id'            => 'autosla:typeseverity',
    'version'       => '0.1',
    'name'          => 'Auto SLA by Type & Severity',
    'author'        => 'Charles / KRA BI',
    'description'   => 'Auto-populates a ticket\'s SLA Plan from a configurable '
                     . 'matrix of Type x Severity (e.g. "Minor Bug" = 2 weeks, '
                     . '"Major Enhancement" = 6 months).',
    'url'           => 'https://example.local/',
    'plugin'        => 'autosla.php:AutoSlaPlugin',
    'requires'      => array(),
);
