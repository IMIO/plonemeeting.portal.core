import { BasePattern } from "@patternslib/patternslib/src/core/basepattern";
import events from "@patternslib/patternslib/src/core/events";
import registry from "@patternslib/patternslib/src/core/registry";

const SUBMITTING_CLASS = "is-submitting";

/**
 * Let a form reach the server only once.
 *
 * Declare it on a submit button, or on the form itself:
 *
 *     <button type="submit" class="pat-single-submit">Sync</button>
 *
 * The impatient double click, or Enter held down, is dropped before it leaves
 * the browser. Nothing is ever `disabled`: a control disabled while the form
 * is being serialized is left out of the payload, and z3c.form dispatches on
 * the name of the button that was pressed. The buttons are made unclickable
 * and marked as busy through CSS instead.
 *
 * This only spares the user a pointless round trip. Whatever the form triggers
 * still needs to be safe against a request arriving twice.
 */
class SingleSubmit extends BasePattern {
    static get name() {
        return "single-submit";
    }

    static get trigger() {
        return ".pat-single-submit";
    }

    init() {
        const form = this.el.form || this.el.closest("form");
        if (!form) {
            return;
        }

        const reset = () => {
            for (const el of [form, ...form.querySelectorAll(`.${SUBMITTING_CLASS}`)]) {
                el.classList.remove(SUBMITTING_CLASS);
            }
        };

        // Bubble phase on purpose: pat-validation is initialised before us and
        // stops the event there when the form is invalid, so a submit rejected
        // by validation does not spend the one submit we allow.
        //
        // A fixed id keeps one listener per form, however many of its buttons
        // declare the pattern.
        events.add_event_listener(form, "submit", "single-submit", (event) => {
            if (form.classList.contains(SUBMITTING_CLASS)) {
                event.preventDefault();
                return;
            }
            form.classList.add(SUBMITTING_CLASS);
            event.submitter?.classList.add(SUBMITTING_CLASS);
        });

        // Coming back through the history cache restores the DOM as we left
        // it, busy buttons included.
        events.add_event_listener(window, "pageshow", `single-submit-${this.uuid}`, (event) => {
            if (event.persisted) {
                reset();
            }
        });
    }
}

registry.register(SingleSubmit);

export default SingleSubmit;
