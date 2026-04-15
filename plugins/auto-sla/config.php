<?php
require_once INCLUDE_DIR . 'class.plugin.php';
require_once INCLUDE_DIR . 'class.forms.php';
require_once INCLUDE_DIR . 'class.sla.php';

class AutoSlaConfig extends PluginConfig {

    /**
     * Build a choice list of active SLA Plans using the ORM helper.
     * SLA::getSLAs() checks the flags bitmask (FLAG_ACTIVE = 0x0001)
     * correctly — unlike a raw "WHERE isactive=1" query which would fail
     * because the column does not exist in osTicket 1.16+.
     */
    private function slaChoices() {
        $choices = array('' => '— No SLA —');
        foreach (SLA::getSLAs() as $id => $label) {
            $choices[$id] = $label;
        }
        return $choices;
    }

    /**
     * Parse a comma-separated string into a trimmed, non-empty array.
     * Used to turn the admin-configured type/severity lists into arrays.
     */
    static function parseList($raw, $defaults = array()) {
        $items = array();
        foreach (explode(',', (string) $raw) as $item) {
            $item = trim($item);
            if ($item !== '')
                $items[] = $item;
        }
        return $items ?: $defaults;
    }

    /**
     * Convert a human label to a config-key-safe slug.
     * e.g. "New System" → "new_system", "Bug" → "bug"
     */
    static function slug($label) {
        return preg_replace('/[^a-z0-9]+/', '_',
            strtolower(trim($label)));
    }

    function getOptions() {
        $slaChoices = $this->slaChoices();

        $rawTypes = $this->get('type_values') ?: 'Enhancement,Bug,New System';
        $rawSevs  = $this->get('severity_values') ?: 'Major,Medium,Minor';

        $types      = self::parseList($rawTypes,  array('Enhancement', 'Bug', 'New System'));
        $severities = self::parseList($rawSevs,   array('Major', 'Medium', 'Minor'));

        $opts = array(
            'intro' => new SectionBreakField(array(
                'label' => 'Auto SLA by Type & Severity',
                'hint'  => 'Automatically assigns an SLA Plan based on two custom '
                         . 'fields (Type and Severity). Configure the field variable '
                         . 'names below, then define the values from your custom lists '
                         . 'and map each combination to an SLA Plan.',
            )),

            'field_name_type' => new TextboxField(array(
                'label'         => 'Custom field variable: Type',
                'default'       => 'type',
                'hint'          => 'The Variable name of the custom list/choice field '
                                 . 'on the ticket form that stores the ticket type. '
                                 . 'Must match exactly (case-insensitive) what is set '
                                 . 'under Admin → Manage → Forms. Common examples: '
                                 . '`type` or `issue_type`.',
                'configuration' => array('size' => 30, 'length' => 64),
            )),
            'field_name_severity' => new TextboxField(array(
                'label'         => 'Custom field variable: Severity',
                'default'       => 'severity',
                'hint'          => 'The Variable name of the custom field that stores '
                                 . 'severity. Common examples: `severity` or '
                                 . '`issue_severity`.',
                'configuration' => array('size' => 30, 'length' => 64),
            )),

            'values_break' => new SectionBreakField(array(
                'label' => 'Configured Values',
                'hint'  => 'Enter the exact choice labels from your custom lists, '
                         . 'separated by commas. The matrix below rebuilds when you '
                         . 'save. Changing these values will orphan old mappings — '
                         . 'you will need to re-map any renamed entries.',
            )),
            'type_values' => new TextboxField(array(
                'label'         => 'Type values (comma-separated)',
                'default'       => 'Enhancement,Bug,New System',
                'hint'          => 'Must match the labels in your Type custom list.',
                'configuration' => array('size' => 60, 'length' => 512),
            )),
            'severity_values' => new TextboxField(array(
                'label'         => 'Severity values (comma-separated)',
                'default'       => 'Major,Medium,Minor',
                'hint'          => 'Must match the labels in your Severity custom list.',
                'configuration' => array('size' => 60, 'length' => 512),
            )),

            'matrix_break' => new SectionBreakField(array(
                'label' => 'SLA Matrix',
                'hint'  => 'Select the SLA Plan for each Type + Severity combination. '
                         . 'Leave blank to skip auto-assignment for that case. '
                         . 'Create SLA Plans first under Admin → Manage → SLA Plans.',
            )),
        );

        // Build the matrix grouped by type, one section per type
        foreach ($types as $tLabel) {
            $tKey = self::slug($tLabel);

            $opts["type_section_{$tKey}"] = new SectionBreakField(array(
                'label' => $tLabel,
            ));

            foreach ($severities as $sLabel) {
                $sKey = self::slug($sLabel);
                $opts["map_{$tKey}_{$sKey}"] = new ChoiceField(array(
                    'label'   => $sLabel . ' ' . $tLabel,
                    'choices' => $slaChoices,
                    'default' => '',
                ));
            }
        }

        $opts['behaviour_break'] = new SectionBreakField(array(
            'label' => 'Behaviour',
        ));
        $opts['overwrite_existing'] = new BooleanField(array(
            'label'   => 'Overwrite an SLA that was already set',
            'default' => false,
            'hint'    => 'When off, manual or unrelated SLA selections are preserved. '
                       . 'SLA values already managed by this matrix can still remap '
                       . 'when Type/Severity changes.',
        ));
        $opts['log_note'] = new BooleanField(array(
            'label'   => 'Post internal note when SLA is set',
            'default' => true,
            'hint'    => 'Recommended — creates an audit trail showing which rule '
                       . 'triggered the SLA change.',
        ));
        $opts['log_debug'] = new BooleanField(array(
            'label'   => 'Write debug log to /tmp/autosla-debug.log',
            'default' => false,
            'hint'    => 'Enable only when diagnosing issues. Log may contain '
                       . 'ticket data — disable in production.',
        ));

        return $opts;
    }
}
