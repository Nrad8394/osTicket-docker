<?php
require_once INCLUDE_DIR . 'class.plugin.php';
require_once INCLUDE_DIR . 'class.signal.php';
require_once INCLUDE_DIR . 'class.ticket.php';
require_once INCLUDE_DIR . 'class.sla.php';
require_once 'config.php';

class AutoSlaPlugin extends Plugin {

    var $config_class = 'AutoSlaConfig';

    function bootstrap() {
        $this->log('bootstrap() called');
        Signal::connect('ticket.created', array($this, 'onTicketCreated'));
        Signal::connect('model.updated',  array($this, 'onModelUpdated'));
        Signal::connect('object.edited',  array($this, 'onObjectEdited'));
    }

    function onTicketCreated($ticket) {
        if ($ticket instanceof Ticket)
            $this->apply($ticket, true);
    }

    function onModelUpdated($object, $data) {
        if (!($object instanceof Ticket))
            return;
        if (!empty($object->_autosla_in_progress))
            return;
        $this->apply($object, false);
    }

    function onObjectEdited($object, $type) {
        if (!($object instanceof Ticket))
            return;
        if (!empty($object->_autosla_in_progress))
            return;

        $this->log(sprintf('onObjectEdited() type=%s', var_export($type, true)));
        $this->apply($object, false);
    }

    // ---------------------------------------------------------------
    // Helpers: config parsing and fallback
    // ---------------------------------------------------------------

    private function isTruthy($value) {
        if (is_bool($value))
            return $value;
        if (is_numeric($value))
            return ((int) $value) !== 0;
        $s = strtolower(trim((string) $value));
        return in_array($s, array('1', 'true', 'yes', 'on'), true);
    }

    private function extractId($raw) {
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
                    return $this->extractId($decoded);
            }
            if (is_numeric($trim))
                return (int) $trim;
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

    private function syncSlaInDb($ticketId, $targetId, $reason) {
        $sql = 'UPDATE ' . TICKET_TABLE
             . ' SET sla_id=' . db_input((int) $targetId)
             . ' WHERE ticket_id=' . db_input((int) $ticketId)
             . ' LIMIT 1';

        $ok = db_query($sql) ? true : false;

        $checkSql = 'SELECT sla_id FROM ' . TICKET_TABLE
                  . ' WHERE ticket_id=' . db_input((int) $ticketId)
                  . ' LIMIT 1';
        $dbSla = null;
        if (($res = db_query($checkSql)) && ($row = db_fetch_row($res)))
            $dbSla = (int) $row[0];

        $this->log(sprintf(
            'db SLA sync (%s)=%s: #%d target=%d db_sla=%s',
            $reason, $ok ? 'ok' : 'fail',
            (int) $ticketId, (int) $targetId,
            var_export($dbSla, true)
        ));

        return $ok && ((int) $dbSla === (int) $targetId);
    }

    private function getManagedSlaIds() {
        $ids = array();

        $types = AutoSlaConfig::parseList(
            $this->getConfigRawValue('type_values', 'Enhancement,Bug,New System')
        );
        $severities = AutoSlaConfig::parseList(
            $this->getConfigRawValue('severity_values', 'Major,Medium,Minor')
        );

        foreach ($types as $tLabel) {
            $tKey = AutoSlaConfig::slug($tLabel);
            foreach ($severities as $sLabel) {
                $sKey = AutoSlaConfig::slug($sLabel);
                $raw = $this->getConfigRawValue("map_{$tKey}_{$sKey}", '');
                $id = $this->extractId($raw);
                if ($id > 0)
                    $ids[] = $id;
            }
        }

        return array_values(array_unique($ids));
    }

    // ---------------------------------------------------------------
    // Core logic
    // ---------------------------------------------------------------

    private function apply(Ticket $ticket, $isNew) {
        $typeVar = mb_strtolower(trim((string) $this->getConfigRawValue('field_name_type', 'type')) ?: 'type');
        $sevVar  = mb_strtolower(trim((string) $this->getConfigRawValue('field_name_severity', 'severity')) ?: 'severity');

        list($typeUsed, $typeRaw) = $this->readAnswerAny($ticket, array($typeVar, 'issue_type', 'type'));
        list($sevUsed, $sevRaw)   = $this->readAnswerAny($ticket, array($sevVar, 'issue_severity', 'severity'));

        $this->log(sprintf('apply(isNew=%s) ticket=#%d typeVar=%s type=%s sevVar=%s sev=%s',
            $isNew ? 'Y' : 'N', $ticket->getId(),
            var_export($typeUsed, true), var_export($typeRaw, true),
            var_export($sevUsed, true), var_export($sevRaw, true)));

        if ($typeRaw === null || $sevRaw === null)
            return;

        // Match against admin-configured value lists
        $typeSlug = $this->matchSlug($typeRaw,
            $this->getConfigRawValue('type_values', 'Enhancement,Bug,New System'));
        $sevSlug  = $this->matchSlug($sevRaw,
            $this->getConfigRawValue('severity_values', 'Major,Medium,Minor'));

        $this->log(sprintf('slugs: type=%s sev=%s', var_export($typeSlug, true), var_export($sevSlug, true)));

        if (!$typeSlug || !$sevSlug)
            return;

        $targetRaw = $this->getConfigRawValue("map_{$typeSlug}_{$sevSlug}", '');
        $targetId = $this->extractId($targetRaw);
        $this->log(sprintf('map_%s_%s raw=%s => targetId=%d',
            $typeSlug, $sevSlug, var_export($targetRaw, true), $targetId));

        if (!$targetId)
            return;

        if (!SLA::lookup($targetId)) {
            $this->log('skip: SLA id not found: ' . $targetId);
            return;
        }

        $currentId = (int) $ticket->getSLAId();
        if ($currentId === $targetId)
            return;

        $overwrite = $this->isTruthy($this->getConfigRawValue('overwrite_existing', 0));
        if ($currentId && !$overwrite) {
            // Keep manual/foreign SLA selections when overwrite is disabled,
            // but still allow remapping if the current SLA is one managed by
            // this plugin's Type x Severity matrix.
            $managed = $this->getManagedSlaIds();
            if (!in_array($currentId, $managed, true)) {
                $this->log(sprintf(
                    'skip: existing SLA %d preserved (overwrite disabled)',
                    $currentId
                ));
                return;
            }

            $this->log(sprintf(
                'remap allowed: existing SLA %d is matrix-managed',
                $currentId
            ));
        }

        $this->log(sprintf('setting SLA id=%d on ticket #%d (was %d)', $targetId, $ticket->getId(), $currentId));

        $ticket->_autosla_in_progress = true;
        try {
            $ok = $ticket->setSLAId($targetId);

            if ($ok) {
                $this->syncSlaInDb($ticket->getId(), $targetId, 'setSLAId-ok');
            } else {
                $this->log('setSLAId returned false; using DB fallback');
                $this->syncSlaInDb($ticket->getId(), $targetId, 'setSLAId-fallback');
            }

            if ($ok && $this->isTruthy($this->getConfigRawValue('log_note', 1))) {
                $sla = SLA::lookup($targetId);
                $ticket->logNote(
                    'SLA auto-assigned',
                    sprintf('SLA set to "%s" based on Type="%s", Severity="%s".',
                        $sla ? $sla->getName() : $targetId, $typeRaw, $sevRaw),
                    'SYSTEM',
                    false
                );
            }
            $this->log('setSLAId result: ' . ($ok ? 'ok' : 'failed'));
        } catch (Exception $e) {
            $this->log('ERROR: ' . $e->getMessage());
            error_log('AutoSlaPlugin: ' . $e->getMessage());
        }
        $ticket->_autosla_in_progress = false;
    }

    // ---------------------------------------------------------------
    // Custom field reading
    // ---------------------------------------------------------------

    private function normalizeAnswerValue($val) {
        if (is_array($val)) {
            if (empty($val))
                return '';
            return $this->normalizeAnswerValue(reset($val));
        }

        if (is_object($val) && method_exists($val, 'getName'))
            $val = $val->getName();

        if (!is_string($val))
            $val = (string) $val;

        $val = trim($val);
        if ($val === '')
            return '';

        // Choice/list answers can be serialized maps like {"59":"Minor"}
        if ($val[0] === '{' || $val[0] === '[') {
            $decoded = json_decode($val, true);
            if (json_last_error() === JSON_ERROR_NONE)
                return trim((string) $this->normalizeAnswerValue($decoded));
        }

        return $val;
    }

    /**
     * Read a custom field answer from the ticket by field variable name.
     * Returns the normalized string value, or null if not found / empty.
     */
    private function readAnswer(Ticket $ticket, $variable) {
        // Primary path: Ticket::getAnswer() keyed by lowercase variable name
        if (method_exists($ticket, 'getAnswer')) {
            $ans = $ticket->getAnswer(mb_strtolower($variable));
            if ($ans !== null && $ans !== false) {
                $val = method_exists($ans, 'getValue') ? $ans->getValue() : null;
                if ($val === null || $val === false)
                    $val = (string) $ans; // __toString / toString fallback
                $val = $this->normalizeAnswerValue($val);
                if ($val !== '')
                    return $val;
            }
        }

        // Fallback: scan loadDynamicData() — returns [varname => DynamicFormEntryAnswer]
        if (method_exists($ticket, 'loadDynamicData')) {
            foreach ($ticket->loadDynamicData() as $tag => $answer) {
                if (strcasecmp($tag, $variable) !== 0)
                    continue;
                $val = method_exists($answer, 'getValue') ? $answer->getValue() : (string) $answer;
                $val = $this->normalizeAnswerValue($val);
                if ($val !== '')
                    return $val;
            }
        }

        return null;
    }

    private function readAnswerAny(Ticket $ticket, array $variables) {
        foreach ($variables as $var) {
            $var = mb_strtolower(trim((string) $var));
            if ($var === '')
                continue;

            $value = $this->readAnswer($ticket, $var);
            if ($value !== null)
                return array($var, $value);
        }

        return array(null, null);
    }

    // ---------------------------------------------------------------
    // Value matching (data-driven, not hardcoded)
    // ---------------------------------------------------------------

    /**
     * Given a raw field value and a comma-separated list of configured
     * labels, return the slug of the first label that matches
     * (exact case-insensitive, then slug comparison).
     * Returns null if no match found.
     */
    private function matchSlug($rawValue, $configList) {
        $configured = AutoSlaConfig::parseList($configList);
        $rawNorm    = mb_strtolower(trim($rawValue));

        foreach ($configured as $label) {
            if (mb_strtolower($label) === $rawNorm)
                return AutoSlaConfig::slug($label);
            // slug match handles minor differences (spaces vs underscores)
            if (AutoSlaConfig::slug($label) === AutoSlaConfig::slug($rawValue))
                return AutoSlaConfig::slug($label);
        }
        return null;
    }

    // ---------------------------------------------------------------
    // Debug logging
    // ---------------------------------------------------------------

    private function isDebug() {
        return $this->isTruthy($this->getConfigRawValue('log_debug', 0));
    }

    private function log($msg) {
        if (!$this->isDebug())
            return;
        file_put_contents(
            '/tmp/autosla-debug.log',
            '[' . date('Y-m-d H:i:s') . '] ' . $msg . "\n",
            FILE_APPEND
        );
    }
}
