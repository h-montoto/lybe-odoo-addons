/* Copyright 2026 LyBe Creators
 * License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl). */
import { KeepLast } from "@web/core/utils/concurrency";
import { TimelineRenderer } from "@web_timeline/views/timeline/timeline_renderer.esm";
import { escape } from "@web/core/utils/strings";
import { patch } from "@web/core/utils/patch";

const { DateTime } = luxon;

// Task items use the numeric task id. A non-numeric id can never collide with
// them, and draw_dependencies() skips it because it has no task data.
export const MILESTONE_ITEM_PREFIX = "milestone_";

patch(TimelineRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        // Only the milestones of the latest load are drawn, so a slow answer
        // for a previous search never lands on top of the current one.
        this.milestoneKeepLast = new KeepLast();
    },

    get showsMilestones() {
        return (
            this.model.model_name === "project.task" &&
            "project_id" in this.fields
        );
    },

    async on_data_loaded(records) {
        await super.on_data_loaded(...arguments);
        if (!this.showsMilestones) {
            return;
        }
        const projectIds = [
            ...new Set(
                records.map(
                    (record) => record.project_id && record.project_id[0],
                ),
            ),
        ].filter(Boolean);
        const milestones = await this.milestoneKeepLast.add(
            projectIds.length
                ? this.orm.call(
                      "project.milestone",
                      "get_timeline_milestones",
                      [projectIds],
                  )
                : Promise.resolve([]),
        );
        const groupedByProject = this.model.last_group_bys[0] === "project_id";
        this.timeline.itemsData.add(
            milestones.map((milestone) =>
                this.milestoneToTimelineItem(milestone, groupedByProject),
            ),
        );
    },

    /**
     * Grouped by project, a milestone only shades the row of its project.
     * Otherwise it spans every row, so its label names the project too.
     *
     * @param {Object} milestone Values from project.milestone.get_timeline_milestones
     * @param {Boolean} groupedByProject
     * @returns {Object} vis-timeline background item
     */
    milestoneToTimelineItem(milestone, groupedByProject) {
        const deadline = DateTime.fromISO(milestone.deadline);
        const label = groupedByProject
            ? milestone.name
            : `${milestone.project_name} · ${milestone.name}`;
        const item = {
            id: `${MILESTONE_ITEM_PREFIX}${milestone.id}`,
            type: "background",
            start: deadline.startOf("day").toJSDate(),
            end: deadline.endOf("day").toJSDate(),
            content: `<div class="o_timeline_milestone_label">${escape(label)}</div>`,
            className: `o_timeline_milestone o_timeline_milestone_${milestone.status}`,
        };
        if (groupedByProject) {
            item.group = milestone.project_id;
        }
        return item;
    },
});
