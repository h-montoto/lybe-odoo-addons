This module adds two settings to the task timer provided by
`project_timesheet_time_control`:

- **Minimum duration**: a stopped timer never records less than this number
  of minutes.
- **Rounding period**: the recorded duration is rounded up to the next
  multiple of this number of minutes.

The rules only apply to durations measured by the timer, whether it is
stopped from a task, a project, a timesheet line or the *Start work* wizard.
Durations typed by hand are kept as they are.
