This module shows the project milestones on the task timeline provided by
`project_timeline`:

- Every milestone with a deadline is drawn as a vertical band on its deadline
  day. When the timeline is grouped by project, the band only covers the row of
  its project; with any other grouping it covers every row and its label also
  shows the project name.
- The band is colored by the milestone status: blue when pending, green when
  reached and red when the deadline has passed without reaching it.
- Tasks planned to end after the deadline of their milestone are highlighted
  with a red dashed border, and their tooltip names the milestone at risk.
