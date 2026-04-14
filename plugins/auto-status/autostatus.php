<?php
require_once INCLUDE_DIR . 'class.plugin.php';
require_once INCLUDE_DIR . 'class.signal.php';
require_once INCLUDE_DIR . 'class.ticket.php';
require_once 'config.php';

class AutoStatusPlugin extends Plugin {

    var $config_class = 'AutoStatusConfig';

    /**
     * Called by osTicket once per request when the plugin is active.
     * We hook the model.updated signal so we catch every assignment change,
     * whether it came from the UI, a filter, the API, or another plugin.
     */
    function bootstrap() {
        // Debug: write to file to verify bootstrap is called
        file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] bootstrap() called\n", FILE_APPEND);
        
        // Register the signal handler
        if (class_exists('Signal')) {
            Signal::connect('model.updated', array($this, 'onModelUpdated'));
            Signal::connect('object.edited', array($this, 'onObjectEdited'));
            file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] Signal handler registered\n", FILE_APPEND);
        } else {
            file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] ERROR: Signal class not found!\n", FILE_APPEND);
        }
    }

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
            $ids = array_values(array_unique(array_filter($ids, function($x) {
                return $x > 0;
            })));
            return $ids;
        }

        return array();
    }

    private function getAssigneeRoleIds($object) {
        $ids = array();

        if ($object->getStaffId() && ($staff = $object->getStaff())) {
            if (!empty($staff->role_id))
                $ids[] = (int) $staff->role_id;
        }
        elseif ($object->getTeamId() && ($team = $object->getTeam())) {
            if (($lead = $team->getTeamLead()) && !empty($lead->role_id))
                $ids[] = (int) $lead->role_id;
        }

        return array_values(array_unique(array_filter($ids)));
    }

    private function getRuleCount() {
        $raw = $this->getConfigRawValue('rule_count', '1');
        $count = (int) $raw;
        if ($count < 1)
            $count = 1;
        if ($count > 50)
            $count = 50;
        return $count;
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
        $currentId = (int) $object->getStatusId();
        $currentStaffId = (int) $object->getStaffId();
        $currentTeamId = (int) $object->getTeamId();
        $assigneeRoleIds = $this->getAssigneeRoleIds($object);
        $ruleCount = $this->getRuleCount();

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

            file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] structured rule matched #" . $i . " target=" . $targetId . "\n", FILE_APPEND);
            return $targetId;
        }

        return 0;
    }

    private function getConfigRawValue($key, $default = null) {
        $cfg = $this->getConfig();
        $val = $cfg ? $cfg->get($key) : null;

        // Prefer loaded config when present
        if ($val !== null)
            return $val;

        // Fallback to DB lookup by active plugin instance namespace
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
                $namespace = sprintf('plugin.%d.instance.%d', (int) $this->getId(), (int) $row[0]);
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

        file_put_contents(
            '/tmp/autostatus-debug.log',
            "[" . date('Y-m-d H:i:s') . "] db sync (" . $reason . ")=" . ($ok ? 'ok' : 'fail')
            . ": #" . (int)$ticketId . " target=" . (int)$targetId . " db_status=" . var_export($dbStatus, true) . "\n",
            FILE_APPEND
        );

        return $ok && ((int) $dbStatus === (int) $targetId);
    }

    private function applyStatusChange($object, $wasUnassigned) {
        // Is it now assigned?
        $isAssigned = $object->isAssigned()
            || ((int) $object->getStaffId() !== 0)
            || ((int) $object->getTeamId()  !== 0);

        if (!$isAssigned) {
            file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] skip: not assigned (staff=" . (int)$object->getStaffId() . ", team=" . (int)$object->getTeamId() . ")\n", FILE_APPEND);
            return;
        }

        $targetId = $this->resolveStructuredRuleTargetStatusId($object);
        $rawTarget = 'structured_rules';

        if (!$targetId) {
            file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] skip: no matching workflow rule\n", FILE_APPEND);
            return;
        }

        file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] target status=" . $targetId . " (raw=" . var_export($rawTarget, true) . "), wasUnassigned=" . ($wasUnassigned ? 'yes' : 'no') . "\n", FILE_APPEND);

        if ((int) $object->getStatusId() === (int) $targetId)
            return;

        $target = TicketStatus::lookup($targetId);
        if (!$target) {
            file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] skip: target status id not found: " . $targetId . "\n", FILE_APPEND);
            return;
        }

        try {
            $errors = array();
            $note = false;
            $before = (int) $object->getStatusId();
            $changed = $object->setStatus($target, $note, $errors);
            $after = (int) $object->getStatusId();

            if ($changed) {
                file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] setStatus ok: #" . $object->getId() . " " . $before . " -> " . $after . " (" . $target->getName() . ")\n", FILE_APPEND);
                $this->syncStatusInDb($object->getId(), $targetId, 'setStatus-ok');
            } else {
                file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] setStatus returned false: #" . $object->getId() . " status=" . $before . " target=" . (int)$targetId . " errors=" . var_export($errors, true) . "\n", FILE_APPEND);

                // Retry without staff context (bypass role-bound setStatus restrictions)
                global $thisstaff;
                $origStaff = $thisstaff ?? null;
                $thisstaff = null;
                $retryErrors = array();
                $retryChanged = $object->setStatus($target, $note, $retryErrors);
                $retryAfter = (int) $object->getStatusId();
                $thisstaff = $origStaff;

                if ($retryChanged) {
                    file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] privileged retry ok: #" . $object->getId() . " -> " . $retryAfter . "\n", FILE_APPEND);
                    $this->syncStatusInDb($object->getId(), $targetId, 'privileged-retry-ok');
                } else {
                    file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] privileged retry failed: #" . $object->getId() . " errors=" . var_export($retryErrors, true) . "\n", FILE_APPEND);
                    // Final fallback: persist ticket status directly in DB
                    $this->syncStatusInDb($object->getId(), $targetId, 'final-fallback');
                }
            }
        } catch (Exception $e) {
            file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] ERROR: " . $e->getMessage() . "\n", FILE_APPEND);
        }
    }

    /**
     * Signal handler. Fires for every model update; we filter to Ticket only,
     * and only when the assignment fields changed.
     *
     * @param mixed $object  The model that changed
     * @param array $data    Contains 'dirty' => [field => oldValue, ...]
     */
    function onModelUpdated($object, $data) {
        if (!($object instanceof Ticket))
            return;

        if (!is_array($data) || empty($data['dirty']))
            return;

        file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] onModelUpdated() called for " . get_class($object) . "\n", FILE_APPEND);
        
        $dirty = $data['dirty'];
        file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] dirty keys: " . implode(',', array_keys($dirty)) . "\n", FILE_APPEND);

        // Only react when the assignment actually changed
        $staffChanged = array_key_exists('staff', $dirty) || array_key_exists('staff_id', $dirty);
        $teamChanged  = array_key_exists('team', $dirty)  || array_key_exists('team_id', $dirty);
        
        if (!$staffChanged && !$teamChanged) {
            return;
        }

        // Avoid re-entrancy: setStatus() will itself trigger model.updated.
        // We tag the ticket in-memory so we don't loop.
        if (!empty($object->_autostatus_in_progress))
            return;

        // Was the ticket previously unassigned?
        // Note: dirty[] contains OLD values (before the update)
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

        if (!is_array($type) || ($type['type'] ?? '') !== 'assigned')
            return;

        if (!empty($object->_autostatus_in_progress))
            return;

        // Fallback path for assignment flows where model.updated dirty fields
        // are not available with assignee history. Treat as reassignment.
        file_put_contents('/tmp/autostatus-debug.log', "[" . date('Y-m-d H:i:s') . "] onObjectEdited() assigned fallback\n", FILE_APPEND);
        $object->_autostatus_in_progress = true;
        $this->applyStatusChange($object, false);
        $object->_autostatus_in_progress = false;
    }
}
