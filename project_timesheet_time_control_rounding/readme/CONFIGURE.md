Go to *Timesheets → Configuration → Settings* and, in the *Time Encoding*
block, fill in *Timer Rounding*:

- *Minimum duration* (minutes).
- *Round up to* (minutes).

Both values are set per company and default to 0, which keeps the real
duration. For example, with a minimum of 15 and a period of 15:

| Timer stopped at | Recorded duration |
| --- | --- |
| 00:04 | 00:15 |
| 00:16 | 00:30 |
| 00:30 | 00:30 |
