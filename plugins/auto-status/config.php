<?php
require_once INCLUDE_DIR . 'class.plugin.php';
require_once INCLUDE_DIR . 'class.forms.php';
require_once INCLUDE_DIR . 'class.ticket.php';

class AutoStatusConfig extends PluginConfig {

    /**
     * Scan saved config to find the highest-numbered rule that has any
     * meaningful data in it. Returns 0 if no rules are configured yet.
     */
    private function getLastFilledRule() {
        for ($i = 50; $i >= 1; $i--) {
            if ($this->get('rule_'.$i.'_enabled')
                    || $this->get('rule_'.$i.'_target_status')
                    || $this->get('rule_'.$i.'_name'))
                return $i;
        }
        return 0;
    }

    function getOptions() {
        // Build dropdown lists from live system data
        $targetChoices = array('' => '— Do not change —');
        $fromChoices   = array('' => 'Any current status');
        $staffChoices  = array();
        $teamChoices   = array();
        $roleChoices   = array();

        $sql = 'SELECT id, name FROM ' . TICKET_STATUS_TABLE . ' ORDER BY name';
        if (($res = db_query($sql))) {
            while (list($id, $name) = db_fetch_row($res)) {
                $targetChoices[$id] = $name;
                $fromChoices[$id]   = $name;
            }
        }

        $ssql = 'SELECT staff_id, CONCAT(firstname, " ", lastname) AS name '
              . 'FROM ' . STAFF_TABLE . ' WHERE isactive=1 ORDER BY firstname, lastname';
        if (($sres = db_query($ssql))) {
            while (list($sid, $sname) = db_fetch_row($sres)) {
                $sid = (int) $sid;
                if ($sid > 0)
                    $staffChoices[$sid] = trim((string) $sname);
            }
        }

        $tsql = 'SELECT team_id, name FROM ' . TEAM_TABLE . ' ORDER BY name';
        if (($tres = db_query($tsql))) {
            while (list($tid, $tname) = db_fetch_row($tres)) {
                $tid = (int) $tid;
                if ($tid > 0)
                    $teamChoices[$tid] = trim((string) $tname);
            }
        }

        $rsql = 'SELECT id, name FROM ' . ROLE_TABLE . ' ORDER BY name';
        if (($rres = db_query($rsql))) {
            while (list($rid, $rname) = db_fetch_row($rres)) {
                $roleChoices[$rid] = $rname;
            }
        }

        // Auto-expand: show last filled rule + 3 empty slots (min 3, max 50)
        $lastFilled   = $this->getLastFilledRule();
        $visibleCount = max(3, min(50, $lastFilled + 3));

        $options = array(
            'workflow_rules_info' => new SectionBreakField(array(
                'label' => 'Workflow Transition Rules',
                'hint'  => 'Rules are evaluated top-to-bottom; the first enabled '
                         . 'rule that matches wins. Fill in a rule and save — '
                         . 'three empty slots always appear below the last filled '
                         . 'rule so you never need to change a count manually.',
            )),
        );

        for ($i = 1; $i <= $visibleCount; $i++) {
            $savedName = (string) $this->get('rule_'.$i.'_name');
            $heading   = $savedName !== ''
                ? sprintf('Rule %d — %s', $i, $savedName)
                : sprintf('Rule %d', $i);

            // Visual separator before each rule
            $options['rule_'.$i.'_section'] = new SectionBreakField(array(
                'label' => $heading,
            ));

            $options['rule_'.$i.'_name'] = new TextboxField(array(
                'label'         => 'Rule ' . $i . ': label',
                'hint'          => 'Optional friendly name for your reference.',
                'configuration' => array('size' => 50, 'length' => 255),
                'default'       => '',
            ));

            $options['rule_'.$i.'_enabled'] = new BooleanField(array(
                'label'   => 'Enable rule ' . $i,
                'default' => false,
            ));

            $options['rule_'.$i.'_from_status'] = new ChoiceField(array(
                'label'   => 'Rule ' . $i . ': only if current status is',
                'hint'    => 'Leave blank to match regardless of current status.',
                'choices' => $fromChoices,
                'default' => '',
            ));

            $options['rule_'.$i.'_staff_ids'] = new ChoiceField(array(
                'label'         => 'Rule ' . $i . ': assigned staff',
                'hint'          => 'Optional. Leave blank to match any staff assignment.',
                'choices'       => $staffChoices,
                'default'       => array(),
                'configuration' => array('multiselect' => true),
            ));

            $options['rule_'.$i.'_team_ids'] = new ChoiceField(array(
                'label'         => 'Rule ' . $i . ': assigned team',
                'hint'          => 'Optional. Leave blank to match any team assignment.',
                'choices'       => $teamChoices,
                'default'       => array(),
                'configuration' => array('multiselect' => true),
            ));

            $options['rule_'.$i.'_role_ids'] = new ChoiceField(array(
                'label'         => 'Rule ' . $i . ': assignee role',
                'hint'          => 'Optional. Leave blank to match any role.',
                'choices'       => $roleChoices,
                'default'       => array(),
                'configuration' => array('multiselect' => true),
            ));

            $options['rule_'.$i.'_target_status'] = new ChoiceField(array(
                'label'   => 'Rule ' . $i . ': set status to',
                'hint'    => 'The status to apply when this rule matches.',
                'choices' => $targetChoices,
                'default' => '',
            ));
        }

        $options['debug_break'] = new SectionBreakField(array(
            'label' => 'Diagnostics',
        ));
        $options['log_debug'] = new BooleanField(array(
            'label'   => 'Write debug log to /tmp/autostatus-debug.log',
            'default' => false,
            'hint'    => 'Enable only when diagnosing issues. Disable in production.',
        ));

        return $options;
    }
}
