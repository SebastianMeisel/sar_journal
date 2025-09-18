PRIO_NAMES = {0:"EMERG", 1:"ALERT", 2:"CRIT", 3:"ERR", 4:"WARNING", 5:"NOTICE", 6:"INFO", 7:"DEBUG"}

PRIO_STYLES = {
    0: "bold white on red3",
    1: "bold white on dark_red",
    2: "bold red",
    3: "red3",
    4: "yellow3",
    5: "cyan",
    6: "white",
    7: "dim",
}

STAT_PRESETS = {
    "cpu": {"sar_opts": ["-u", "ALL"], "want": ["%user", "%system", "%iowait", "%idle"]},
    "load": {"sar_opts": ["-q"], "want": ["runq-sz", "ldavg-1", "ldavg-5"]},
    "mem":  {"sar_opts": ["-r"], "want": ["kbmemfree", "kbmemused", "%memused"]},
    "disk": {"sar_opts": ["-b"], "want": ["tps", "rtps", "wtps"]},
    "net":  {"sar_opts": ["-n", "DEV"], "want": ["IFACE", "rxpck/s", "txpck/s"]},
    "edev": {"sar_opts": ["-n", "EDEV"], "want": ["rxerr/s", "txerr/s", "coll/s", "rxdrop/s", "txdrop/s", "txcarr/s", "rxcarr/s", "rxfram/s"]},
    "etcp": {"sar_opts": ["-n", "ETCP"], "want": ["atmptf/s", "estres/s", "retrseg/s", "isegerr/s", "orts/s"]},
}
