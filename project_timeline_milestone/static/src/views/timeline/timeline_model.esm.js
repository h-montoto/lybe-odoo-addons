/* Copyright 2026 LyBe Creators
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import { TimelineModel } from "@web_timeline/views/timeline/timeline_model.esm";
import { _t } from "@web/core/l10n/translation";
import { escape } from "@web/core/utils/strings";
import { patch } from "@web/core/utils/patch";

patch(TimelineModel.prototype, {
    _event_data_transform(record) {
        const item = super._event_data_transform(...arguments);
        if (record.is_late_for_milestone) {
            item.className = "o_timeline_task_milestone_late";
            // vis-timeline renders the tooltip as HTML.
            item.title = _t(
                "Planned to end after the deadline of the milestone %s",
                escape(record.milestone_id[1]),
            ).toString();
        }
        return item;
    },
});
