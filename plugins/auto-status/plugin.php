<?php
/**
 * Auto Status on Allocation - osTicket plugin
 *
 * Updates ticket status automatically when a ticket is assigned or reassigned
 * to an agent or team.
 */
return array(
    'id'            => 'autostatus:allocation',
    'version'       => '0.1',
    'name'          => 'Auto Status on Allocation',
    'author'        => 'Charles / KRA BI',
    'description'   => 'Automatically updates a ticket status when it is allocated (assigned) or reassigned.',
    'url'           => 'https://example.local/',
    'plugin'        => 'autostatus.php:AutoStatusPlugin',
    'requires'      => array(),
);
