<?php
require_once INCLUDE_DIR . 'class.plugin.php';
require_once INCLUDE_DIR . 'class.forms.php';
require_once INCLUDE_DIR . 'class.ticket.php';

class AutoStatusConfig extends PluginConfig {

    private function normalizeRuleCount($raw) {
        $count = (int) $raw;
        if ($count < 1)
            $count = 1;
        if ($count > 50)
            $count = 50;
        return $count;
    }

    function getOptions() {
        // Build dropdown lists from live system data
        $targetChoices = array('' => '— Do not change —');
        $fromChoices = array('' => 'Any current status');
        $staffChoices = array();
        $teamChoices = array();
        $roleChoices = array();

        $sql = 'SELECT id, name FROM ' . TICKET_STATUS_TABLE
             . ' ORDER BY name';
        if (($res = db_query($sql))) {
            while (list($id, $name) = db_fetch_row($res)) {
                $targetChoices[$id] = $name;
                $fromChoices[$id] = $name;
            }
        }

        $ssql = 'SELECT staff_id, CONCAT(firstname, " ", lastname) AS name '
              . 'FROM ' . STAFF_TABLE . ' WHERE isactive=1 ORDER BY firstname, lastname';
        if (($sres = db_query($ssql))) {
            while (list($sid, $sname) = db_fetch_row($sres)) {
                $sid = (int) $sid;
                if ($sid <= 0)
                    continue;
                $staffChoices[$sid] = trim((string) $sname);
            }
        }

        $tsql = 'SELECT team_id, name FROM ' . TEAM_TABLE . ' ORDER BY name';
        if (($tres = db_query($tsql))) {
            while (list($tid, $tname) = db_fetch_row($tres)) {
                $tid = (int) $tid;
                if ($tid <= 0)
                    continue;
                $teamChoices[$tid] = trim((string) $tname);
            }
        }

        $rsql = 'SELECT id, name FROM ' . ROLE_TABLE . ' ORDER BY name';
        if (($rres = db_query($rsql))) {
            while (list($rid, $rname) = db_fetch_row($rres)) {
                $roleChoices[$rid] = $rname;
            }
        }

        $configuredCount = $this->normalizeRuleCount($this->get('rule_count'));

        $options = array(
            'workflow_rules_info' => new SectionBreakField(array(
                'label' => 'Workflow transition rules (recommended)',
                'hint'  => 'Fully configurable rules. No pre-made flow. '
                         . 'Set rule count, save, and only that many rules will be shown. '
                         . 'Increase later whenever needed. First matching enabled rule wins.',
            )),
            'rule_count' => new TextboxField(array(
                'label' => 'Number of rules to configure',
                'hint'  => 'Choose how many rules to use (1-50).',
                'configuration' => array('size' => 5, 'length' => 2),
                'default' => (string) $configuredCount,
            )),
        );

        for ($i = 1; $i <= $configuredCount; $i++) {
            $label = 'Rule ' . $i;

            $options['rule_'.$i.'_name'] = new TextboxField(array(
                'label' => $label . ' label',
                'hint'  => 'Optional name for your reference.',
                'configuration' => array('size' => 50, 'length' => 255),
                'default' => '',
            ));

            $options['rule_'.$i.'_enabled'] = new BooleanField(array(
                'label' => 'Enable rule '.$i.' — '.$label,
                'default' => false,
            ));

            $options['rule_'.$i.'_from_status'] = new ChoiceField(array(
                'label' => 'Rule '.$i.' current status',
                'choices' => $fromChoices,
                'default' => '',
            ));

            $options['rule_'.$i.'_staff_ids'] = new ChoiceField(array(
                'label' => 'Rule '.$i.' staff assignee(s)',
                'hint'  => 'Optional. Select one or more staff. Leave blank to match any staff.',
                'choices' => $staffChoices,
                'default' => array(),
                'configuration' => array('multiselect' => true),
            ));

            $options['rule_'.$i.'_team_ids'] = new ChoiceField(array(
                'label' => 'Rule '.$i.' team assignee(s)',
                'hint'  => 'Optional. Select one or more teams. Leave blank to match any team.',
                'choices' => $teamChoices,
                'default' => array(),
                'configuration' => array('multiselect' => true),
            ));

            $options['rule_'.$i.'_role_ids'] = new ChoiceField(array(
                'label' => 'Rule '.$i.' assignee role(s)',
                'hint'  => 'Optional. Select one or more roles. Leave blank to match any role.',
                'choices' => $roleChoices,
                'default' => array(),
                'configuration' => array('multiselect' => true),
            ));

            $options['rule_'.$i.'_target_status'] = new ChoiceField(array(
                'label' => 'Rule '.$i.' target status',
                'choices' => $targetChoices,
                'default' => '',
            ));
        }

        return $options;
    }
}
