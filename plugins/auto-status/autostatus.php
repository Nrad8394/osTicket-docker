<?php
require_once INCLUDE_DIR . 'class.plugin.php';
require_once INCLUDE_DIR . 'class.signal.php';
require_once INCLUDE_DIR . 'class.ticket.php';
require_once 'config.php';

class AutoStatusPlugin extends Plugin {

    var $config_class = 'AutoStatusConfig';

    function bootstrap() {
        $this->log('bootstrap() called');

        if (class_exists('Signal')) {
            Signal::connect('model.updated', array($this, 'onModelUpdated'));
            Signal::connect('object.edited', array($this, 'onObjectEdited'));
            $this->log('Signal handlers registered');
        } else {
            $this->log('ERROR: Signal class not found!');
        }
    }

    // ---------------------------------------------------------------
    // Helpers: value extraction
    // ---------------------------------------------------------------

    private function valueToId($value) {
        if (is_object($value) && method_exists($value, 'getId'))
            return (int) $value->getId();
        if (is_array($value) && isset($value['id']))
            return (int) $value['id'];
        return (int) $value;
    }

    private function chooseDirtyValue($dirty, $keys, $fallback) {
        foreach ($keys as $key) {
            if (array_key_exists($key, $dirty))
                return $this->valueToId($dirty[$key]);
        }
        return $fallback;
    }

    private function extractStatusId($raw) {
        if (is_numeric($raw))
            return (int) $raw;

        if (is_array($raw)) {
            if (empty($raw))
                return 0;
            $keys = array_keys($raw);
            if (isset($keys[0]) && is_numeric($keys[0]))
                return (int) $keys[0];
            $first = reset($raw);
            if (is_numeric($first))
                return (int) $first;
            return 0;
        }

        if (is_string($raw)) {
            $trim = trim($raw);
            if ($trim === '')
                return 0;
            if ($trim[0] === '{' || $trim[0] === '[') {
                $decoded = json_decode($trim, true);
                if (json_last_error() === JSON_ERROR_NONE)
                    return $this->extractStatusId($decoded);
            }
            if (is_numeric($trim))
                return (int) $trim;
        }

        return 0;
    }

    private function extractIds($raw) {
        if ($raw === null)
            return array();

        if (is_numeric($raw))
            return array((int) $raw);

        if (is_string($raw)) {
            $trim = trim($raw);
            if ($trim === '')
                return array();
            if ($trim[0] === '{' || $trim[0] === '[') {
                $decoded = json_decode($trim, true);
                if (json_last_error() === JSON_ERROR_NONE)
                    return $this->extractIds($decoded);
            }
            $parts = array_map('trim', explode(',', $trim));
            $ids = array();
            foreach ($parts as $p) {
                if ($p !== '' && is_numeric($p))
                    $ids[] = (int) $p;
            }
            return array_values(array_unique($ids));
        }

        if (is_array($raw)) {
            $ids = array();
            foreach ($raw as $k => $v) {
                if (is_numeric($k))
                    $ids[] = (int) $k;
                if (is_numeric($v))
                    $ids[] = (int) $v;
            }
            return array_values(array_unique(array_filter($ids, function ($x) {
                return $x > 0;
            })));
        }

        return array();
    }

    private function getAssigneeRoleIds($object) {
        $ids = array();
        if ($object->getStaffId() && ($staff = $object->getStaff())) {
            if (!empty($staff->role_id))
                $ids[] = (int) $staff->role_id;
        } elseif ($object->getTeamId() && ($team = $object->getTeam())) {
            if (($lead = $team->getTeamLead()) && !empty($lead->role_id))
                $ids[] = (int) $lead->role_id;
        }
        return array_values(array_unique(array_filter($ids)));
    }

    // ---------------------------------------------------------------
    // Rule resolution (auto-detect rule count)
    // ---------------------------------------------------------------

    private function getLastFilledRule() {
        for ($i = 50; $i >= 1; $i--) {
            if ($this->getConfigRawValue('rule_'.$i.'_enabled', 0)
                    || $this->getConfigRawValue('rule_'.$i.'_target_status', '')
                    || $this->getConfigRawValue('rule_'.$i.'_name', ''))
                return $i;
        }
        return 0;
    }

    private function isTruthy($value) {
        if (is_bool($value))
            return $value;
        if (is_numeric($value))
            return ((int) $value) !== 0;
        $s = strtolower(trim((string) $value));
        return in_array($s, array('1', 'true', 'yes', 'on'), true);
    }

    private function resolveStructuredRuleTargetStatusId($object) {
        $currentId      = (int) $object->getStatusId();
        $currentStaffId = (int) $object->getStaffId();
        $currentTeamId  = (int) $object->getTeamId();
        $assigneeRoleIds = $this->getAssigneeRoleIds($object);
        $ruleCount      = $this->getLastFilledRule();

        for ($i = 1; $i <= $ruleCount; $i++) {
            if (!$this->isTruthy($this->getConfigRawValue('rule_'.$i.'_enabled', 0)))
                continue;

            $fromId = $this->extractStatusId($this->getConfigRawValue('rule_'.$i.'_from_status', ''));
            if ($fromId && $fromId !== $currentId)
                continue;

            $ruleStaffIds = $this->extractIds($this->getConfigRawValue('rule_'.$i.'_staff_ids', array()));
            if ($ruleStaffIds) {
                if ($currentStaffId <= 0 || !in_array($currentStaffId, $ruleStaffIds, true))
                    continue;
            }

            $ruleTeamIds = $this->extractIds($this->getConfigRawValue('rule_'.$i.'_team_ids', array()));
            if ($ruleTeamIds) {
                if ($currentTeamId <= 0 || !in_array($currentTeamId, $ruleTeamIds, true))
                    continue;
            }

            $ruleRoleIds = $this->extractIds($this->getConfigRawValue('rule_'.$i.'_role_ids', array()));
            if ($ruleRoleIds) {
                if (!$assigneeRoleIds || !array_intersect($ruleRoleIds, $assigneeRoleIds))
                    continue;
            }

            $targetId = $this->extractStatusId($this->getConfigRawValue('rule_'.$i.'_target_status', ''));
            if (!$targetId)
                continue;

            $this->log('structured rule matched #' . $i . ' target=' . $targetId);
            return $targetId;
        }

        return 0;
    }

    private function getConfigRawValue($key, $default = null) {
        $cfg = $this->getConfig();
        $val = $cfg ? $cfg->get($key) : null;

        if ($val !== null)
            return $val;

        // Fallback: direct DB lookup by plugin instance namespace
        $namespace = null;
        if ($cfg && method_exists($cfg, 'getInstance')) {
            $instance = $cfg->getInstance();
            if ($instance && method_exists($instance, 'getNamespace'))
                $namespace = $instance->getNamespace();
        }

        if (!$namespace) {
            $sql = 'SELECT id FROM ' . PLUGIN_INSTANCE_TABLE
                . ' WHERE plugin_id=' . db_input((int) $this->getId())
                . ' AND (flags & ' . PluginInstance::FLAG_ENABLED . ') > 0'
                . ' ORDER BY id LIMIT 1';
            if (($res = db_query($sql)) && ($row = db_fetch_row($res)))
                $namespace = sprintf('plugin.%d.instance.%d',
                    (int) $this->getId(), (int) $row[0]);
        }

        if ($namespace) {
            $sql = 'SELECT value FROM ' . CONFIG_TABLE
                . ' WHERE namespace=' . db_input($namespace)
                . ' AND `key`=' . db_input($key)
                . ' LIMIT 1';
            if (($res = db_query($sql)) && ($row = db_fetch_row($res)))
                return $row[0];
        }

        return $default;
    }

    // ---------------------------------------------------------------
    // Status application
    // ---------------------------------------------------------------

    private function syncStatusInDb($ticketId, $targetId, $reason) {
        $sql = 'UPDATE ' . TICKET_TABLE
             . ' SET status_id=' . db_input((int) $targetId)
             . ' WHERE ticket_id=' . db_input((int) $ticketId)
             . ' LIMIT 1';

        $ok = db_query($sql) ? true : false;

        $checkSql = 'SELECT status_id FROM ' . TICKET_TABLE
                  . ' WHERE ticket_id=' . db_input((int) $ticketId)
                  . ' LIMIT 1';
        $dbStatus = null;
        if (($res = db_query($checkSql)) && ($row = db_fetch_row($res)))
            $dbStatus = (int) $row[0];

        $this->log(sprintf(
            'db sync (%s)=%s: #%d target=%d db_status=%s',
            $reason, $ok ? 'ok' : 'fail',
            (int) $ticketId, (int) $targetId,
            var_export($dbStatus, true)
        ));

        return $ok && ((int) $dbStatus === (int) $targetId);
    }

    private function applyStatusChange($object, $wasUnassigned) {
        $isAssigned = $object->isAssigned()
            || ((int) $object->getStaffId() !== 0)
            || ((int) $object->getTeamId()  !== 0);

        if (!$isAssigned) {
            $this->log(sprintf('skip: not assigned (staff=%d, team=%d)',
                (int) $object->getStaffId(), (int) $object->getTeamId()));
            return;
        }

        $targetId = $this->resolveStructuredRuleTargetStatusId($object);

        if (!$targetId) {
            $this->log('skip: no matching workflow rule');
            return;
        }

        $this->log(sprintf('target status=%d, wasUnassigned=%s',
            $targetId, $wasUnassigned ? 'yes' : 'no'));

        if ((int) $object->getStatusId() === (int) $targetId)
            return;

        $target = TicketStatus::lookup($targetId);
        if (!$target) {
            $this->log('skip: target status id not found: ' . $targetId);
            return;
        }

        try {
            $errors  = array();
            $note    = false;
            $before  = (int) $object->getStatusId();
            $changed = $object->setStatus($target, $note, $errors);
            $after   = (int) $object->getStatusId();

            if ($changed) {
                $this->log(sprintf('setStatus ok: #%d %d -> %d (%s)',
                    $object->getId(), $before, $after, $target->getName()));
                $this->syncStatusInDb($object->getId(), $targetId, 'setStatus-ok');
            } else {
                $this->log(sprintf('setStatus returned false: #%d status=%d target=%d errors=%s',
                    $object->getId(), $before, (int) $targetId,
                    var_export($errors, true)));

                // Retry without staff context to bypass role-bound restrictions
                global $thisstaff;
                $origStaff = isset($thisstaff) ? $thisstaff : null;
                $thisstaff = null;
                $retryErrors  = array();
                $retryChanged = $object->setStatus($target, $note, $retryErrors);
                $retryAfter   = (int) $object->getStatusId();
                $thisstaff    = $origStaff;

                if ($retryChanged) {
                    $this->log('privileged retry ok: #' . $object->getId() . ' -> ' . $retryAfter);
                    $this->syncStatusInDb($object->getId(), $targetId, 'privileged-retry-ok');
                } else {
                    $this->log('privileged retry failed: #' . $object->getId()
                        . ' errors=' . var_export($retryErrors, true));
                    $this->syncStatusInDb($object->getId(), $targetId, 'final-fallback');
                }
            }
        } catch (Exception $e) {
            $this->log('ERROR: ' . $e->getMessage());
        }
    }

    // ---------------------------------------------------------------
    // Signal handlers
    // ---------------------------------------------------------------

    function onModelUpdated($object, $data) {
        if (!($object instanceof Ticket))
            return;
        if (!is_array($data) || empty($data['dirty']))
            return;

        $this->log('onModelUpdated() called for ' . get_class($object));

        $dirty        = $data['dirty'];
        $staffChanged = array_key_exists('staff',   $dirty) || array_key_exists('staff_id', $dirty);
        $teamChanged  = array_key_exists('team',    $dirty) || array_key_exists('team_id',  $dirty);

        if (!$staffChanged && !$teamChanged)
            return;

        if (!empty($object->_autostatus_in_progress))
            return;

        $oldStaff = $staffChanged
            ? $this->chooseDirtyValue($dirty, array('staff_id', 'staff'), (int) $object->getStaffId())
            : (int) $object->getStaffId();
        $oldTeam = $teamChanged
            ? $this->chooseDirtyValue($dirty, array('team_id', 'team'), (int) $object->getTeamId())
            : (int) $object->getTeamId();

        $wasUnassigned = ($oldStaff === 0 && $oldTeam === 0);

        $object->_autostatus_in_progress = true;
        $this->applyStatusChange($object, $wasUnassigned);
        $object->_autostatus_in_progress = false;
    }

    function onObjectEdited($object, $type) {
        if (!($object instanceof Ticket))
            return;
        if (!is_array($type) || (isset($type['type']) ? $type['type'] : '') !== 'assigned')
            return;
        if (!empty($object->_autostatus_in_progress))
            return;

        $this->log('onObjectEdited() assigned fallback');
        $object->_autostatus_in_progress = true;
        $this->applyStatusChange($object, false);
        $object->_autostatus_in_progress = false;
    }

    // ---------------------------------------------------------------
    // Debug logging
    // ---------------------------------------------------------------

    private function isDebug() {
        $cfg = $this->getConfig();
        return $cfg && $cfg->get('log_debug');
    }

    private function log($msg) {
        if (!$this->isDebug())
            return;
        file_put_contents(
            '/tmp/autostatus-debug.log',
            '[' . date('Y-m-d H:i:s') . '] ' . $msg . "\n",
            FILE_APPEND
        );
    }
}
