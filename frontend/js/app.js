const API_BASE_URL = "http://localhost:8000";


async function refreshOutreachData() {
    await loadDashboard();

    if (outreachLoaded) {
        await loadOutreachWorkspace();
    }
}


async function loadDashboard() {
    const refreshButton = document.getElementById("refresh-dashboard");

    try {
        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.textContent = "Refreshing…";
        }

        const response = await fetch(
            `${API_BASE_URL}/api/outreach/dashboard/summary`
        );

        if (!response.ok) {
            throw new Error(
                `Dashboard request failed: ${response.status}`
            );
        }

        const data = await response.json();

        updateDashboardMetrics(data.metrics);
        renderReviewQueue(data.review_queue);
        renderReadyToSend(data.ready_to_send);
        renderSentHistory(data.sent_history);

    } catch (error) {
        console.error("Could not load dashboard:", error);
        renderQueueError();

    } finally {
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh";
        }
    }
}

function updateDashboardMetrics(metrics) {
    const qualifiedCompanies = document.getElementById(
        "qualified-companies-count"
    );

    const highIntent = document.getElementById(
        "high-intent-count"
    );

    const pendingReview = document.getElementById(
        "pending-review-count"
    );

    const sent = document.getElementById(
        "sent-count"
    );

    if (qualifiedCompanies) {
        qualifiedCompanies.textContent =
            metrics.qualified_companies;
    }

    if (highIntent) {
        highIntent.textContent =
            metrics.high_intent;
    }

    if (pendingReview) {
        pendingReview.textContent =
            metrics.pending_review;
    }

    if (sent) {
        sent.textContent = metrics.sent;
    }
}

function renderReviewQueue(messages) {
    const queue = document.getElementById("review-queue");

    if (!queue) {
        return;
    }

    if (!messages || messages.length === 0) {
        queue.innerHTML = `
            <div class="queue-loading">
                <div class="empty-icon">✓</div>
                <h4>You're all caught up</h4>
                <p>No outreach is waiting for review.</p>
            </div>
        `;
        return;
    }

    queue.innerHTML = messages.map((message) => `
        <article class="review-item">
            <div class="review-item-main">
                <div class="review-meta">
                    <span class="channel-pill">
                        ${escapeHtml(message.channel)}
                    </span>

                    <span class="status-pill">
                        ${escapeHtml(message.status)}
                    </span>

                    <span class="outreach-id">
                        #${message.id}
                    </span>
                </div>

                <h4>
                    ${escapeHtml(message.subject || "Untitled outreach")}
                </h4>

                <p class="message-preview">
                    ${escapeHtml(message.message_body)}
                </p>
            </div>

            <button
                class="review-button"
                type="button"
                data-outreach-id="${message.id}"
            >
                Review
                <span>→</span>
            </button>
        </article>
    `).join("");
}

function renderQueueError() {
    const queue = document.getElementById("review-queue");

    if (!queue) {
        return;
    }

    queue.innerHTML = `
        <div class="queue-loading">
            <div class="empty-icon">!</div>
            <h4>Couldn't load outreach</h4>
            <p>Check that the FastAPI server is running.</p>
        </div>
    `;
}

function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = value ?? "";
    return element.innerHTML;
}

document.addEventListener(
    "DOMContentLoaded",
    () => {
        loadDashboard();

        const refreshButton = document.getElementById(
            "refresh-dashboard"
        );

        if (refreshButton) {
            refreshButton.addEventListener(
                "click",
                loadDashboard
            );
        }
    }
);


// OUTREACH REVIEW SHEET

async function openOutreachReview(outreachId) {
    const overlay = document.getElementById("review-overlay");
    const content = document.getElementById(
        "review-sheet-content"
    );

    const sheet = document.getElementById(
        "review-sheet"
    );

    const eyebrow = sheet?.querySelector(
        ".review-sheet-header .eyebrow"
    );

    const title = sheet?.querySelector(
        ".review-sheet-header h3"
    );

    if (!overlay || !content) {
        return;
    }

    if (eyebrow) {
        eyebrow.textContent = "HUMAN APPROVAL";
    }

    if (title) {
        title.textContent = "Review Outreach";
    }

    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.classList.add("review-open");

    content.innerHTML = `
        <div class="sheet-loading">
            Loading outreach…
        </div>
    `;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/outreach/${outreachId}/review`
        );

        if (!response.ok) {
            throw new Error(
                `Review request failed: ${response.status}`
            );
        }

        const data = await response.json();

        let companyIntelligence = null;

        try {
            const companyResponse = await fetch(
                `${API_BASE_URL}/api/companies/${data.outreach.company_id}`
            );

            if (companyResponse.ok) {
                companyIntelligence =
                    await companyResponse.json();
            }
        } catch (companyError) {
            console.error(
                "Could not load company intelligence:",
                companyError
            );
        }

        if (data.outreach.status === "REJECTED") {
            if (eyebrow) {
                eyebrow.textContent = "OUTREACH HISTORY";
            }

            if (title) {
                title.textContent = "Rejected Outreach";
            }
        }

        renderOutreachReview(
            data.outreach,
            data.review,
            companyIntelligence
        );

    } catch (error) {
        console.error(
            "Could not load outreach review:",
            error
        );

        content.innerHTML = `
            <div class="sheet-loading">
                Couldn't load this outreach.
            </div>
        `;
    }
}

function renderOutreachReview(
    outreach,
    review,
    companyIntelligence = null
) {
    const content = document.getElementById(
        "review-sheet-content"
    );

    const footer = document.getElementById(
        "review-sheet-footer"
    );

    if (!content || !footer) {
        return;
    }

    const intelligence =
        companyIntelligence || {};

    const company =
        intelligence.company || {};

    const score =
        intelligence.score || null;

    const primaryBuyer =
        intelligence.primary_buyer || null;

    const signals =
        intelligence.signals || [];

    const signalResearch =
        intelligence.signal_research || {
            status: "NOT_RESEARCHED",
            signals_found: 0
        };

    const companyName =
        company.name || "Company";

    const industry =
        company.industry || "Industry not available";

    const country =
        company.country || "Market not available";

    const buyerName = primaryBuyer
        ? `${primaryBuyer.first_name || ""} ${
            primaryBuyer.last_name || ""
        }`.trim()
        : "No ranked buyer available";

    const buyerTitle = primaryBuyer
        ? (
            primaryBuyer.job_title ||
            "Title not available"
        )
        : "";

    const buyerRank = primaryBuyer
        ? primaryBuyer.buyer_rank_score
        : null;

    const signalCards = signals.length
        ? signals.slice(0, 3).map(
            (signal) => `
                <div class="review-evidence-item">
                    <strong>
                        ${escapeHtml(
                            signal.title ||
                            signal.signal_type
                        )}
                    </strong>

                    <span>
                        ${escapeHtml(
                            signal.signal_date ||
                            "Date unavailable"
                        )}
                        ·
                        ${escapeHtml(
                            signal.confidence ||
                            "UNKNOWN"
                        )}
                    </span>
                </div>
            `
        ).join("")
        : `
            <div class="review-evidence-item">
                <strong>
                    ${
                        signalResearch.status ===
                        "RESEARCHED_NO_SIGNALS"
                            ? "No verified signals found"
                            : "Signal research not run yet"
                    }
                </strong>
            </div>
        `;

    content.innerHTML = `
        <div class="sheet-status-row">
            <span class="channel-pill">
                ${escapeHtml(outreach.channel)}
            </span>

            <span class="status-pill">
                ${escapeHtml(outreach.status)}
            </span>

            <span class="outreach-id">
                #${outreach.id}
            </span>
        </div>

        <h4 class="sheet-subject">
            ${escapeHtml(
                outreach.subject || "Untitled outreach"
            )}
        </h4>

        <div class="review-intelligence-grid">
            <section class="review-info-card">
                <span class="review-field-label">
                    WHY THIS COMPANY?
                </span>

                <strong class="review-intelligence-title">
                    ${escapeHtml(companyName)}
                </strong>

                <p>
                    ${escapeHtml(industry)}
                    ·
                    ${escapeHtml(country)}
                </p>

                ${
                    score
                        ? `
                            <div class="review-score-line">
                                <strong>
                                    ${score.total_score}/100
                                </strong>
                                <span>
                                    ${escapeHtml(
                                        score.priority
                                    )}
                                </span>
                            </div>
                        `
                        : ""
                }
            </section>

            <section class="review-info-card">
                <span class="review-field-label">
                    WHY THIS BUYER?
                </span>

                <strong class="review-intelligence-title">
                    ${escapeHtml(buyerName)}
                </strong>

                ${
                    buyerTitle
                        ? `
                            <p>
                                ${escapeHtml(buyerTitle)}
                            </p>
                        `
                        : ""
                }

                ${
                    buyerRank !== null
                        ? `
                            <div class="review-score-line">
                                <strong>
                                    ${buyerRank}/100
                                </strong>
                                <span>BUYER RANK</span>
                            </div>
                        `
                        : ""
                }
            </section>
        </div>

        <section class="review-info-card">
            <span class="review-field-label">
                WHY NOW?
            </span>

            <div class="review-evidence-list">
                ${signalCards}
            </div>
        </section>

        <section class="review-info-card reason-card">
            <span class="review-field-label">
                INTERNAL REASONING
            </span>

            <p>
                ${escapeHtml(
                    outreach.personalisation_reason ||
                    "No personalisation reason recorded."
                )}
            </p>
        </section>

        <section class="review-info-card">
            <span class="review-field-label">
                SUBJECT
            </span>

            <p>
                ${escapeHtml(
                    outreach.subject || "No subject"
                )}
            </p>
        </section>

        <section class="review-info-card message-card">
            <span class="review-field-label">
                MESSAGE
            </span>

            <p class="review-message-body">${escapeHtml(
                outreach.message_body
            )}</p>
        </section>

    `;

    footer.innerHTML = `
        <div class="review-sheet-actions">
            <button
                class="sheet-action reject"
                type="button"
                data-review-action="reject"
                data-outreach-id="${outreach.id}"
                ${review.can_reject ? "" : "disabled"}
            >
                Reject
            </button>

            <button
                class="sheet-action edit"
                type="button"
                data-review-action="edit"
                data-outreach-id="${outreach.id}"
                ${review.can_edit ? "" : "disabled"}
            >
                Edit
            </button>

            <button
                class="sheet-action approve"
                type="button"
                data-review-action="approve"
                data-outreach-id="${outreach.id}"
                ${review.can_approve ? "" : "disabled"}
            >
                Approve
            </button>
        </div>
    `;
}

function closeOutreachReview() {
    const overlay = document.getElementById(
        "review-overlay"
    );

    if (!overlay) {
        return;
    }

    overlay.classList.remove("is-open");
    overlay.setAttribute("aria-hidden", "true");
    document.body.classList.remove("review-open");
}

document.addEventListener("click", (event) => {
    const reviewButton = event.target.closest(
        ".review-button"
    );

    if (reviewButton) {
        openOutreachReview(
            reviewButton.dataset.outreachId
        );

        return;
    }

    if (
        event.target.closest("#close-review") ||
        event.target.matches("[data-close-review]")
    ) {
        closeOutreachReview();
    }
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
        closeOutreachReview();
    }
});


// REVIEW ACTIONS

async function updateOutreachStatus(
    outreachId,
    action
) {
    const actionButtons = document.querySelectorAll(
        ".sheet-action"
    );

    actionButtons.forEach((button) => {
        button.disabled = true;
    });

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/outreach/${outreachId}/${action}`,
            {
                method: "POST",
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                `${action} failed with status ${response.status}`
            );
        }

        await refreshOutreachData();

        closeOutreachReview();

        return data;

    } catch (error) {
        console.error(
            `Could not ${action} outreach:`,
            error
        );

        alert(
            `Could not ${action} outreach: ${error.message}`
        );

        await openOutreachReview(outreachId);
    }
}


document.addEventListener("click", async (event) => {
    const actionButton = event.target.closest(
        "[data-review-action]"
    );

    if (!actionButton) {
        return;
    }

    const action = actionButton.dataset.reviewAction;
    const outreachId = actionButton.dataset.outreachId;

    if (action === "approve") {
        await updateOutreachStatus(
            outreachId,
            "approve"
        );

        return;
    }

    if (action === "reject") {
        const confirmed = window.confirm(
            "Reject this outreach?"
        );

        if (!confirmed) {
            return;
        }

        await updateOutreachStatus(
            outreachId,
            "reject"
        );
    }
});


// OUTREACH EDIT MODE

function openOutreachEdit(outreachId) {
    const subjectElement = document.querySelector(
        ".sheet-subject"
    );

    const subjectCard = document.querySelector(
        ".review-info-card:not(.reason-card):not(.message-card) p"
    );

    const messageElement = document.querySelector(
        ".review-message-body"
    );

    const actions = document.querySelector(
        ".review-sheet-actions"
    );

    if (
        !subjectElement ||
        !subjectCard ||
        !messageElement ||
        !actions
    ) {
        return;
    }

    const currentSubject = subjectCard.textContent.trim();
    const currentMessage = messageElement.textContent;

    subjectCard.parentElement.innerHTML = `
        <span class="review-field-label">
            SUBJECT
        </span>

        <input
            id="edit-outreach-subject"
            class="review-edit-input"
            type="text"
            maxlength="300"
        >
    `;

    messageElement.parentElement.innerHTML = `
        <span class="review-field-label">
            MESSAGE
        </span>

        <textarea
            id="edit-outreach-message"
            class="review-edit-textarea"
            maxlength="10000"
        ></textarea>
    `;

    const subjectInput = document.getElementById(
        "edit-outreach-subject"
    );

    const messageInput = document.getElementById(
        "edit-outreach-message"
    );

    subjectInput.value = currentSubject;
    messageInput.value = currentMessage;

    actions.innerHTML = `
        <button
            class="sheet-action reject"
            type="button"
            data-edit-cancel="${outreachId}"
        >
            Cancel
        </button>

        <button
            class="sheet-action approve save-edit"
            type="button"
            data-edit-save="${outreachId}"
        >
            Save Changes
        </button>
    `;

    subjectInput.focus();
}


async function saveOutreachEdit(outreachId) {
    const subjectInput = document.getElementById(
        "edit-outreach-subject"
    );

    const messageInput = document.getElementById(
        "edit-outreach-message"
    );

    if (!subjectInput || !messageInput) {
        return;
    }

    const subject = subjectInput.value.trim();
    const messageBody = messageInput.value.trim();

    if (!messageBody) {
        alert("Message cannot be empty.");
        return;
    }

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/outreach/${outreachId}`,
            {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    subject: subject || null,
                    message_body: messageBody,
                }),
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                `Edit failed with status ${response.status}`
            );
        }

        await refreshOutreachData();

        await openOutreachReview(
            outreachId
        );

    } catch (error) {
        console.error(
            "Could not edit outreach:",
            error
        );

        alert(
            `Could not save changes: ${error.message}`
        );
    }
}


document.addEventListener("click", async (event) => {
    const editButton = event.target.closest(
        '[data-review-action="edit"]'
    );

    if (editButton) {
        openOutreachEdit(
            editButton.dataset.outreachId
        );

        return;
    }

    const saveButton = event.target.closest(
        "[data-edit-save]"
    );

    if (saveButton) {
        await saveOutreachEdit(
            saveButton.dataset.editSave
        );

        return;
    }

    const cancelButton = event.target.closest(
        "[data-edit-cancel]"
    );

    if (cancelButton) {
        await openOutreachReview(
            cancelButton.dataset.editCancel
        );
    }
});


// READY TO SEND

function renderReadyToSend(messages) {
    const container = document.getElementById(
        "ready-to-send"
    );

    const count = document.getElementById(
        "ready-to-send-count"
    );

    if (count) {
        count.textContent = messages
            ? messages.length
            : 0;
    }

    if (!container) {
        return;
    }

    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="queue-loading">
                <div class="empty-icon">✓</div>
                <h4>Nothing waiting to send</h4>
                <p>
                    Approved outreach will appear here.
                </p>
            </div>
        `;

        return;
    }

    container.innerHTML = messages.map((message) => `
        <article class="review-item send-item">
            <div class="review-item-main">
                <div class="review-meta">
                    <span class="channel-pill">
                        ${escapeHtml(message.channel)}
                    </span>

                    <span class="approved-pill">
                        ${escapeHtml(message.status)}
                    </span>

                    <span class="outreach-id">
                        #${message.id}
                    </span>
                </div>

                <h4>
                    ${escapeHtml(
                        message.subject ||
                        "Untitled outreach"
                    )}
                </h4>

                <p class="message-preview">
                    ${escapeHtml(message.message_body)}
                </p>
            </div>

            <button
                class="execute-button"
                type="button"
                data-execute-id="${message.id}"
            >
                Execute
                <span>→</span>
            </button>
        </article>
    `).join("");
}


// APPROVED OUTREACH EXECUTION

async function executeApprovedOutreach(
    outreachId,
    button
) {
    const originalContent = button.innerHTML;

    button.disabled = true;
    button.innerHTML = `
        Executing…
    `;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/outreach/${outreachId}/execute`,
            {
                method: "POST",
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail ||
                `Execution failed with status ${response.status}`
            );
        }

        button.innerHTML = `
            Sent ✓
        `;

        button.classList.add(
            "execution-success"
        );

        await new Promise((resolve) => {
            setTimeout(resolve, 650);
        });

        await refreshOutreachData();

        return data;

    } catch (error) {
        console.error(
            "Could not execute outreach:",
            error
        );

        button.disabled = false;
        button.innerHTML = originalContent;

        alert(
            `Could not execute outreach: ${error.message}`
        );
    }
}


document.addEventListener(
    "click",
    async (event) => {
        const executeButton = event.target.closest(
            "[data-execute-id]"
        );

        if (!executeButton) {
            return;
        }

        const outreachId =
            executeButton.dataset.executeId;

        await executeApprovedOutreach(
            outreachId,
            executeButton
        );
    }
);


// SENT HISTORY

function renderSentHistory(messages) {
    const container = document.getElementById(
        "sent-history"
    );

    const count = document.getElementById(
        "sent-history-count"
    );

    if (count) {
        count.textContent = messages
            ? messages.length
            : 0;
    }

    if (!container) {
        return;
    }

    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="queue-loading">
                <div class="empty-icon">✓</div>
                <h4>No outreach sent yet</h4>
                <p>
                    Executed outreach will appear here.
                </p>
            </div>
        `;

        return;
    }

    container.innerHTML = messages.map((message) => {
        const sentAt = message.sent_at
            ? new Date(
                message.sent_at.replace(" ", "T") + "Z"
            ).toLocaleString([], {
                day: "numeric",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
            })
            : "Sent";

        return `
            <article class="review-item send-item">
                <div class="review-item-main">
                    <div class="review-meta">
                        <span class="channel-pill">
                            ${escapeHtml(message.channel)}
                        </span>

                        <span class="approved-pill">
                            SENT
                        </span>

                        <span class="outreach-id">
                            #${message.id}
                        </span>
                    </div>

                    <h4>
                        ${escapeHtml(
                            message.subject ||
                            "Untitled outreach"
                        )}
                    </h4>

                    <p class="message-preview">
                        Sent ${escapeHtml(sentAt)}
                    </p>
                </div>

                <button
                    class="execute-button"
                    type="button"
                    data-activity-id="${message.id}"
                >
                    View Activity
                    <span>→</span>
                </button>
            </article>
        `;
    }).join("");
}


// EXECUTION ACTIVITY

function formatActivityTime(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(
        value.replace(" ", "T") + "Z"
    );

    return date.toLocaleString([], {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}


function parseEventData(value) {
    if (!value) {
        return {};
    }

    try {
        return JSON.parse(value);
    } catch (error) {
        console.warn(
            "Could not parse outreach event data:",
            error
        );
        return {};
    }
}


async function openExecutionActivity(outreachId) {
    const overlay = document.getElementById(
        "review-overlay"
    );

    const sheet = document.getElementById(
        "review-sheet"
    );

    const content = document.getElementById(
        "review-sheet-content"
    );

    const eyebrow = sheet?.querySelector(
        ".review-sheet-header .eyebrow"
    );

    const title = sheet?.querySelector(
        ".review-sheet-header h3"
    );

    if (!overlay || !sheet || !content) {
        return;
    }

    if (eyebrow) {
        eyebrow.textContent = "EXECUTION ACTIVITY";
    }

    if (title) {
        title.textContent = "Outreach delivery";
    }

    content.innerHTML = `
        <div class="sheet-loading">
            Loading execution activity…
        </div>
    `;

    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");
    document.body.classList.add("review-open");

    try {
        const [reviewResponse, eventsResponse] =
            await Promise.all([
                fetch(
                    `${API_BASE_URL}/api/outreach/${outreachId}/review`
                ),
                fetch(
                    `${API_BASE_URL}/api/outreach/${outreachId}/events`
                ),
            ]);

        if (!reviewResponse.ok) {
            throw new Error(
                `Outreach request failed: ${reviewResponse.status}`
            );
        }

        if (!eventsResponse.ok) {
            throw new Error(
                `Events request failed: ${eventsResponse.status}`
            );
        }

        const reviewPayload =
            await reviewResponse.json();

        const outreach = reviewPayload.outreach;
        const activity =
            await eventsResponse.json();

        const sentEvent = activity.events.find(
            (event) => event.event_type === "SENT"
        );

        const sentData = sentEvent
            ? parseEventData(sentEvent.event_data)
            : {};

        const providerResponse =
            sentData.response || {};

        const eventRows = activity.events.map(
            (event) => {
                const label = event.event_type
                    .replaceAll("_", " ")
                    .toLowerCase()
                    .replace(/\b\w/g, (character) =>
                        character.toUpperCase()
                    );

                return `
                    <div class="activity-step">
                        <div class="activity-track">
                            <div class="activity-marker">
                                ✓
                            </div>
                        </div>

                        <div class="activity-step-copy">
                            <strong>
                                ${escapeHtml(label)}
                            </strong>

                            <span>
                                ${escapeHtml(
                                    formatActivityTime(
                                        event.occurred_at
                                    )
                                )}
                            </span>
                        </div>
                    </div>
                `;
            }
        ).join("");

        const provider =
            providerResponse.provider ||
            sentData.provider ||
            "—";

        const recipient =
            sentData.recipient ||
            providerResponse.recipient ||
            "—";

        const isSafeTest =
            providerResponse.simulated === true;

        content.innerHTML = `
            <div class="activity-hero">
                <div class="activity-meta">
                    <span class="channel-pill">
                        ${escapeHtml(outreach.channel)}
                    </span>

                    <span class="activity-status-pill">
                        <span></span>
                        ${escapeHtml(activity.status)}
                    </span>

                    <span class="outreach-id">
                        #${outreach.id}
                    </span>
                </div>

                <h4 class="activity-subject">
                    ${escapeHtml(
                        outreach.subject ||
                        "Untitled outreach"
                    )}
                </h4>

                <p class="activity-description">
                    Approved outreach executed through
                    the controlled delivery workflow.
                </p>
            </div>

            <section class="activity-section">
                <div class="activity-section-heading">
                    <span>ACTIVITY</span>

                    <span class="activity-success-label">
                        Completed
                    </span>
                </div>

                <div class="activity-timeline">
                    <div class="activity-step">
                        <div class="activity-track">
                            <div class="activity-marker">
                                ✓
                            </div>
                        </div>

                        <div class="activity-step-copy">
                            <strong>Approved</strong>

                            <span>
                                ${escapeHtml(
                                    formatActivityTime(
                                        outreach.approved_at
                                    )
                                )}
                            </span>
                        </div>
                    </div>

                    ${eventRows}
                </div>
            </section>

            <section class="activity-section">
                <div class="activity-section-heading">
                    <span>EXECUTION DETAILS</span>
                </div>

                <div class="activity-details">
                    <div class="activity-detail-row">
                        <span>Provider</span>

                        <strong>
                            ${escapeHtml(provider)}
                        </strong>
                    </div>

                    <div class="activity-detail-row">
                        <span>Recipient</span>

                        <strong>
                            ${escapeHtml(recipient)}
                        </strong>
                    </div>

                    <div class="activity-detail-row">
                        <span>Mode</span>

                        <strong>
                            ${
                                isSafeTest
                                    ? "Safe test"
                                    : "Live"
                            }
                        </strong>
                    </div>

                    ${
                        providerResponse.provider_message_id
                            ? `
                                <div class="activity-detail-row">
                                    <span>Provider ID</span>

                                    <strong>
                                        ${escapeHtml(
                                            providerResponse
                                                .provider_message_id
                                        )}
                                    </strong>
                                </div>
                            `
                            : ""
                    }
                </div>
            </section>

            <div class="activity-complete">
                <div class="activity-complete-icon">
                    ✓
                </div>

                <div>
                    <strong>
                        Execution successful
                    </strong>

                    <span>
                        ${
                            isSafeTest
                                ? "Completed safely without sending a live email."
                                : "Outreach execution completed."
                        }
                    </span>
                </div>
            </div>
        `;

    } catch (error) {
        console.error(
            "Could not load execution activity:",
            error
        );

        content.innerHTML = `
            <div class="sheet-loading">
                Could not load execution activity.
            </div>
        `;
    }
}

document.addEventListener("click", async (event) => {
    const activityButton = event.target.closest(
        "[data-activity-id]"
    );

    if (!activityButton) {
        return;
    }

    await openExecutionActivity(
        activityButton.dataset.activityId
    );
});


// APP NAVIGATION

function showAppView(viewName) {
    const views = document.querySelectorAll(
        ".app-view"
    );

    const navItems = document.querySelectorAll(
        ".nav-item[data-view]"
    );

    views.forEach((view) => {
        view.classList.remove("active");
    });

    navItems.forEach((item) => {
        item.classList.toggle(
            "active",
            item.dataset.view === viewName
        );
    });

    const target = document.getElementById(
        `${viewName}-view`
    );

    if (target) {
        target.classList.add("active");
    }
}


document.addEventListener("click", async (event) => {
    const navItem = event.target.closest(
        ".nav-item[data-view]"
    );

    if (!navItem) {
        return;
    }

    const viewName = navItem.dataset.view;

    if (viewName === "dashboard") {
        showAppView("dashboard");
        return;
    }

    if (viewName === "companies") {
        showAppView("companies");

        if (!companiesLoaded) {
            await loadCompanies();
        }

        return;
    }

    if (viewName === "outreach") {
        showAppView("outreach");

        if (!outreachLoaded) {
            await loadOutreachWorkspace();
        }

        return;
    }
});


// COMPANY INTELLIGENCE

let companiesLoaded = false;
let selectedCompanyId = null;
let companyProspects = [];
let activeCompanyFilter = "ALL";


function setCompanyMetric(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


function getCompanyPriority(companyItem) {
    return (
        companyItem.relevance?.priority ||
        companyItem.score?.priority ||
        null
    );
}


function getFilteredCompanyProspects() {
    if (activeCompanyFilter === "ALL") {
        return companyProspects;
    }

    if (activeCompanyFilter === "DISQUALIFIED") {
        return companyProspects.filter(
            (item) =>
                item.company.qualification_status ===
                "DISQUALIFIED"
        );
    }

    return companyProspects.filter(
        (item) =>
            item.relevance?.priority ===
            activeCompanyFilter
    );
}


function renderCompaniesList(companies) {
    const container = document.getElementById(
        "companies-list"
    );

    const count = document.getElementById(
        "companies-list-count"
    );

    if (!container) {
        return;
    }

    if (count) {
        count.textContent = companies.length;
    }

    if (!companies.length) {
        container.innerHTML = `
            <div class="queue-loading">
                <div class="empty-icon">◎</div>
                <h4>No companies found</h4>
                <p>
                    Run discovery to populate the
                    intelligence pipeline.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = companies.map((item) => {
        const company = item.company;
        const score = item.score;
        const priority = getCompanyPriority(item);

        const relevance = item.relevance;

        const scoreValue = relevance
            ? `
                <span class="relevance-score-number">
                    ${relevance.relevance_score}
                </span>
                <span class="relevance-score-max">
                    /20
                </span>
            `
            : score
                ? `${score.total_score}/100`
                : "—";

        const priorityValue = priority
            ? priority
            : company.qualification_status;

        return `
            <button
                class="company-list-item"
                data-company-id="${company.id}"
                type="button"
            >
                <div class="company-list-score">
                    ${scoreValue}
                </div>

                <div class="company-list-copy">
                    <strong>${company.name}</strong>

                    <span>
                        ${company.country || "Unknown"}
                        ·
                        ${company.industry || "Unknown industry"}
                    </span>

                    <small>
                        ${company.qualification_status}
                    </small>
                </div>

                <div
                    class="company-priority
                    company-priority-${priorityValue.toLowerCase()}"
                >
                    ${priorityValue}
                </div>
            </button>
        `;
    }).join("");
}


async function loadCompanies() {
    const container = document.getElementById(
        "companies-list"
    );

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/companies`
        );

        if (!response.ok) {
            throw new Error(
                `Companies request failed: ${response.status}`
            );
        }

        const data = await response.json();

        const companies = (data.companies || []).filter(
            (item) =>
                item.company.source === "clay_csv"
        );

        companyProspects = companies;

        const qualified = companies.filter(
            (item) =>
                item.company.qualification_status ===
                "QUALIFIED"
        ).length;

        const highPriority = companies.filter(
            (item) =>
                item.relevance?.priority === "HIGH"
        ).length;

        setCompanyMetric(
            "companies-discovered-count",
            companies.length
        );

        setCompanyMetric(
            "companies-qualified-count",
            qualified
        );

        setCompanyMetric(
            "companies-high-intent-count",
            highPriority
        );

        const filterCounts = {
            ALL: companies.length,
            HIGH: companies.filter(
                (item) =>
                    item.relevance?.priority === "HIGH"
            ).length,
            MEDIUM: companies.filter(
                (item) =>
                    item.relevance?.priority === "MEDIUM"
            ).length,
            LOW: companies.filter(
                (item) =>
                    item.relevance?.priority === "LOW"
            ).length,
            DISQUALIFIED: companies.filter(
                (item) =>
                    item.company.qualification_status ===
                    "DISQUALIFIED"
            ).length,
        };

        Object.entries(filterCounts).forEach(
            ([filter, value]) => {
                const element = document.getElementById(
                    `company-filter-${filter.toLowerCase()}`
                );

                if (element) {
                    element.textContent = value;
                }
            }
        );

        renderCompaniesList(
            getFilteredCompanyProspects()
        );

        companiesLoaded = true;

        if (
            companies.length &&
            selectedCompanyId === null
        ) {
            selectedCompanyId =
                companies[0].company.id;

            await loadCompanyIntelligence(
                selectedCompanyId
            );
        }

    } catch (error) {
        console.error(
            "Could not load companies:",
            error
        );

        if (container) {
            container.innerHTML = `
                <div class="queue-loading">
                    <div class="empty-icon">!</div>

                    <h4>Couldn't load companies</h4>

                    <p>
                        Check that the FastAPI service
                        is running on port 8000.
                    </p>
                </div>
            `;
        }
    }
}


async function loadCompanyIntelligence(companyId) {
    const panel = document.getElementById(
        "company-intelligence-panel"
    );

    if (!panel) {
        return;
    }

    selectedCompanyId = Number(companyId);

    document.querySelectorAll(
        ".company-list-item"
    ).forEach((item) => {
        item.classList.toggle(
            "selected",
            Number(item.dataset.companyId) ===
                selectedCompanyId
        );
    });

    panel.innerHTML = `
        <div class="queue-loading">
            <div class="empty-icon">◎</div>

            <h4>Loading intelligence</h4>

            <p>
                Reading qualification, scoring,
                signals and buyer data.
            </p>
        </div>
    `;

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/companies/${companyId}`
        );

        if (!response.ok) {
            throw new Error(
                `Company request failed: ${response.status}`
            );
        }

        const data = await response.json();

        renderCompanyIntelligence(data);

    } catch (error) {
        console.error(
            "Could not load company intelligence:",
            error
        );

        panel.innerHTML = `
            <div class="company-empty-state">
                <div class="empty-icon">!</div>

                <h4>Couldn't load intelligence</h4>

                <p>
                    The company record could not
                    be retrieved.
                </p>
            </div>
        `;
    }
}


function renderCompanyIntelligence(data) {
    const panel = document.getElementById(
        "company-intelligence-panel"
    );

    if (!panel) {
        return;
    }

    const company = data.company;
    const score = data.score;
    const relevance = data.relevance;
    const buyer = data.primary_buyer;
    const rankedBuyers = data.ranked_buyers || [];
    const signals = data.signals || [];
    const signalResearch = data.signal_research || {
        status: "NOT_RESEARCHED",
        signals_found: 0,
    };
    const outreach = data.outreach;

    if (relevance && !score) {
        const evidence = relevance.evidence || {};

        const evidenceGroups = [
            [
                "Industry evidence",
                evidence.industry || [],
            ],
            [
                "Frontline evidence",
                evidence.frontline || [],
            ],
            [
                "Operations evidence",
                evidence.operations || [],
            ],
        ];

        const evidenceHtml = evidenceGroups
            .map(([label, values]) => `
                <div class="score-row">
                    <div class="score-row-main">
                        <span>${label}</span>

                        <div class="score-row-right">
                            <strong>
                                ${
                                    values.length
                                        ? values.join(", ")
                                        : "No evidence found"
                                }
                            </strong>
                        </div>
                    </div>
                </div>
            `)
            .join("");

        const buyerStatus = rankedBuyers.length
            ? `${rankedBuyers.length} MATCHED`
            : "NOT RUN YET";

        let signalStatus = "NOT RUN YET";

        if (
            signalResearch.status === "SIGNALS_FOUND"
        ) {
            signalStatus = `${signals.length} FOUND`;
        } else if (
            signalResearch.status
            === "RESEARCHED_NO_SIGNALS"
        ) {
            signalStatus = "NO SIGNALS FOUND";
        }

        const signalIntelligenceHtml =
            signalResearch.status === "SIGNALS_FOUND"
            && signals.length
                ? `
                    <section class="intelligence-section">
                        <div class="intelligence-section-title">
                            <span>BUYING SIGNALS</span>

                            <strong>
                                ${signals.length} FOUND
                            </strong>
                        </div>

                        <div class="score-breakdown">
                            ${signals
                                .map((signal) => `
                                    <div class="score-row">
                                        <div class="score-row-main">
                                            <span>
                                                ${signal.signal_type
                                                    .replaceAll("_", " ")}
                                            </span>

                                            <div class="score-row-right">
                                                <strong>
                                                    ${signal.confidence}
                                                </strong>
                                            </div>
                                        </div>

                                        <small>
                                            ${signal.title}
                                            ${
                                                signal.signal_date
                                                    ? ` · ${signal.signal_date}`
                                                    : ""
                                            }
                                        </small>
                                    </div>
                                `)
                                .join("")}
                        </div>
                    </section>
                `
                : "";

        const buyerIntelligenceHtml = buyer
            ? `
                <section class="intelligence-section">
                    <div class="intelligence-section-title">
                        <span>BUYER INTELLIGENCE</span>

                        <strong>
                            ${buyer.rank_label}
                        </strong>
                    </div>

                    <div class="buyer-card">
                        <div class="buyer-avatar">
                            ${buyer.first_name.charAt(0)}
                            ${buyer.last_name.charAt(0)}
                        </div>

                        <div class="buyer-copy">
                            <strong>
                                ${buyer.first_name}
                                ${buyer.last_name}
                            </strong>

                            <span>
                                ${buyer.job_title}
                            </span>

                            <small>
                                ${buyer.buyer_category}
                                · ICP match
                                ${buyer.relevance_score}/10
                                · Buyer rank
                                ${buyer.buyer_rank_score}/100
                            </small>
                        </div>
                    </div>

                    <div class="score-breakdown">
                        <div class="score-row">
                            <div class="score-row-main">
                                <span>Function fit</span>

                                <div class="score-row-right">
                                    <strong>
                                        ${buyer.function_score} / 50
                                    </strong>
                                </div>
                            </div>
                        </div>

                        <div class="score-row">
                            <div class="score-row-main">
                                <span>Seniority</span>

                                <div class="score-row-right">
                                    <strong>
                                        ${buyer.seniority_score} / 30
                                    </strong>
                                </div>
                            </div>
                        </div>

                        <div class="score-row">
                            <div class="score-row-main">
                                <span>Title specificity</span>

                                <div class="score-row-right">
                                    <strong>
                                        ${buyer.specificity_score} / 20
                                    </strong>
                                </div>
                            </div>
                        </div>
                    </div>

                    ${
                        rankedBuyers.length > 1
                            ? `
                                <div class="score-breakdown">
                                    ${rankedBuyers
                                        .slice(1)
                                        .map((matchedBuyer) => `
                                            <div class="score-row">
                                                <div class="score-row-main">
                                                    <span>
                                                        ${matchedBuyer.first_name}
                                                        ${matchedBuyer.last_name}
                                                    </span>

                                                    <div class="score-row-right">
                                                        <strong>
                                                            ${matchedBuyer.buyer_rank_score}
                                                            / 100
                                                        </strong>
                                                    </div>
                                                </div>
                                            </div>
                                        `)
                                        .join("")}
                                </div>
                            `
                            : ""
                    }
                </section>
            `
            : "";

        panel.innerHTML = `
            <div class="company-detail-header">
                <div>
                    <p class="eyebrow">
                        ${company.market}
                        · ${company.source || "Unknown source"}
                    </p>

                    <h3>${company.name}</h3>

                    <p>
                        ${company.country || "Unknown"}
                        ·
                        ${company.industry || "Unknown industry"}
                        ·
                        ${company.employee_count || "—"} employees
                    </p>
                </div>

                <div class="company-total-score">
                    <strong>
                        ${relevance.priority}
                    </strong>

                    <span>
                        FIT
                    </span>
                </div>
            </div>

            <section class="intelligence-section">
                <div class="intelligence-section-title">
                    <span>PRE-ENRICHMENT FIT</span>

                    <strong>
                        ${relevance.priority}
                    </strong>
                </div>

                <div class="score-breakdown">
                    ${evidenceHtml}
                </div>
            </section>

            <section class="intelligence-section">
                <div class="intelligence-section-title">
                    <span>PIPELINE STATUS</span>
                </div>

                <div class="score-breakdown">
                    <div class="score-row">
                        <div class="score-row-main">
                            <span>ICP qualification</span>

                            <div class="score-row-right">
                                <strong>
                                    ${company.qualification_status}
                                </strong>
                            </div>
                        </div>
                    </div>

                    <div class="score-row">
                        <div class="score-row-main">
                            <span>Company source</span>

                            <div class="score-row-right">
                                <strong>
                                    ${company.source || "Unknown"}
                                </strong>
                            </div>
                        </div>
                    </div>

                    <div class="score-row">
                        <div class="score-row-main">
                            <span>Buyer intelligence</span>

                            <div class="score-row-right">
                                <strong>
                                    ${buyerStatus}
                                </strong>
                            </div>
                        </div>
                    </div>

                    <div class="score-row">
                        <div class="score-row-main">
                            <span>Buying signals</span>

                            <div class="score-row-right">
                                <strong>
                                    ${signalStatus}
                                </strong>
                            </div>
                        </div>
                    </div>
                </div>
            </section>

            ${buyerIntelligenceHtml}

            ${signalIntelligenceHtml}

            <section class="intelligence-section">
                <div class="intelligence-section-title">
                    <span>NEXT STEP</span>
                </div>

                <div class="intelligence-empty">
                    ${
                        relevance.priority === "HIGH"
                            ? "Prioritised for buyer and signal enrichment."
                            : relevance.priority === "MEDIUM"
                                ? "Keep for secondary review before enrichment."
                                : "Hold until stronger company-level evidence is available."
                    }
                </div>
            </section>
        `;

        return;
    }

    if (!score) {
        panel.innerHTML = `
            <div class="company-detail-header">
                <div>
                    <p class="eyebrow">
                        ${company.market}
                    </p>

                    <h3>${company.name}</h3>

                    <p>
                        ${company.country}
                        ·
                        ${company.industry || "Unknown industry"}
                        ·
                        ${company.employee_count || "—"} employees
                    </p>
                </div>

                <span class="qualification-pill disqualified">
                    ${company.qualification_status}
                </span>
            </div>

            <div class="disqualified-state">
                <div class="empty-icon">×</div>

                <h4>Stopped before scoring</h4>

                <p>
                    This company did not pass the ICP
                    qualification stage, so buyer
                    intelligence and outreach were
                    not generated.
                </p>
            </div>
        `;

        return;
    }

    let scoreExplanation = {};

    try {
        scoreExplanation = JSON.parse(
            score.score_explanation || "{}"
        );
    } catch (error) {
        console.warn(
            "Could not parse score explanation:",
            error
        );
    }

    const scoreRows = [
        [
            "Industry",
            "industry",
            score.industry_score,
            15,
        ],
        [
            "Company size",
            "company_size",
            score.company_size_score,
            15,
        ],
        [
            "Geography",
            "geography",
            score.geography_score,
            10,
        ],
        [
            "Business model",
            "business_model",
            score.business_model_score,
            10,
        ],
        [
            "Buyer relevance",
            "buyer_relevance",
            score.buyer_relevance_score,
            10,
        ],
        [
            "Intent",
            "intent",
            score.intent_score,
            30,
        ],
        [
            "Data confidence",
            "data_confidence",
            score.data_confidence_score,
            10,
        ],
    ];

    const scoreHtml = scoreRows.map(
        ([label, key, value, max]) => {
            const explanation =
                scoreExplanation[key]?.explanation ||
                "No explanation available.";

            return `
                <button
                    class="score-row"
                    type="button"
                    data-score-explanation
                    aria-expanded="false"
                >
                    <div class="score-row-main">
                        <span>${label}</span>

                        <div class="score-row-right">
                            <div class="score-track">
                                <span
                                    style="width: ${(value / max) * 100}%"
                                ></span>
                            </div>

                            <strong>
                                ${value} / ${max}
                            </strong>
                        </div>
                    </div>

                    <div class="score-explanation">
                        ${explanation}
                    </div>
                </button>
            `;
        }
    ).join("");

    let scoredSignalStatus = "NOT RUN YET";

    if (
        signalResearch.status === "SIGNALS_FOUND"
    ) {
        scoredSignalStatus = `${signals.length} FOUND`;
    } else if (
        signalResearch.status
        === "RESEARCHED_NO_SIGNALS"
    ) {
        scoredSignalStatus = "NO SIGNALS FOUND";
    }

    const signalsHtml = signals.length
        ? signals.map((signal) => `
            <article class="signal-card">
                <div>
                    <small>
                        ${signal.signal_type
                            .replaceAll("_", " ")}
                        ${
                            signal.signal_date
                                ? ` · ${signal.signal_date}`
                                : ""
                        }
                    </small>

                    <strong>${signal.title}</strong>

                    <p>
                        ${signal.description || ""}
                    </p>
                </div>

                <span class="signal-confidence">
                    ${signal.confidence}
                </span>
            </article>
        `).join("")
        : `
            <div class="intelligence-empty">
                ${
                    signalResearch.status
                    === "RESEARCHED_NO_SIGNALS"
                        ? "Research completed. No verified buying signals found."
                        : "Signal research has not been run yet."
                }
            </div>
        `;

    const scoredBuyerStatus = rankedBuyers.length
        ? `${rankedBuyers.length} MATCHED`
        : "NOT RUN YET";

    const buyerHtml = buyer
        ? `
            <div class="buyer-card">
                <div class="buyer-avatar">
                    ${buyer.first_name.charAt(0)}
                    ${buyer.last_name.charAt(0)}
                </div>

                <div class="buyer-copy">
                    <strong>
                        ${buyer.first_name}
                        ${buyer.last_name}
                    </strong>

                    <span>${buyer.job_title}</span>

                    <small>
                        ${buyer.buyer_category}
                        · ICP match
                        ${buyer.relevance_score}/10
                        · Buyer rank
                        ${buyer.buyer_rank_score}/100
                    </small>
                </div>
            </div>

            ${
                rankedBuyers.length > 1
                    ? `
                        <div class="score-breakdown">
                            ${rankedBuyers
                                .slice(1)
                                .map((matchedBuyer) => `
                                    <div class="score-row">
                                        <div class="score-row-main">
                                            <span>
                                                ${matchedBuyer.first_name}
                                                ${matchedBuyer.last_name}
                                            </span>

                                            <div class="score-row-right">
                                                <strong>
                                                    ${matchedBuyer.buyer_rank_score}
                                                    / 100
                                                </strong>
                                            </div>
                                        </div>
                                    </div>
                                `)
                                .join("")}
                        </div>
                    `
                    : ""
            }
        `
        : `
            <div class="intelligence-empty">
                Buyer intelligence has not identified
                an ICP-matching contact yet.
            </div>
        `;

    const enrichmentJobs =
        data.enrichment_jobs || [];

    const completedEnrichmentJobs =
        enrichmentJobs.filter(
            (job) => job.status === "COMPLETED"
        );

    const enrichmentFieldLabels = {
        employee_count: "Employee count",
        business_model: "Business model",
    };

    const enrichmentFieldValues = {
        employee_count: company.employee_count
            ? `${company.employee_count} employees`
            : "Recovered",
        business_model:
            company.business_model || "Recovered",
    };

    const enrichmentFieldsHtml =
        completedEnrichmentJobs.map((job) => `
            <div class="enrichment-field">
                <div>
                    <span>
                        ${
                            enrichmentFieldLabels[
                                job.enrichment_type
                            ] ||
                            job.enrichment_type
                        }
                    </span>

                    <strong>
                        ${
                            enrichmentFieldValues[
                                job.enrichment_type
                            ] ||
                            "Recovered"
                        }
                    </strong>
                </div>

                <span class="enrichment-complete">
                    COMPLETED
                </span>
            </div>
        `).join("");

    const enrichmentHtml = enrichmentJobs.length
        ? `
            <section class="intelligence-section enrichment-section">
                <div class="intelligence-section-title">
                    <span>ENRICHMENT JOURNEY</span>

                    <strong>
                        ${completedEnrichmentJobs.length}
                        /
                        ${enrichmentJobs.length}
                    </strong>
                </div>

                <div class="enrichment-journey">
                    <div class="enrichment-step">
                        <span class="enrichment-step-number">
                            01
                        </span>

                        <div>
                            <strong>Incomplete profile</strong>

                            <p>
                                ${enrichmentJobs.length}
                                missing fields required
                                enrichment.
                            </p>
                        </div>
                    </div>

                    <div class="enrichment-connector"></div>

                    <div class="enrichment-step">
                        <span class="enrichment-step-number">
                            02
                        </span>

                        <div>
                            <strong>
                                ${(
                                    enrichmentJobs[0]?.provider ||
                                    "provider"
                                ).toUpperCase()}
                                enrichment
                            </strong>

                            <p>
                                Missing company data was
                                recovered before scoring.
                            </p>
                        </div>
                    </div>

                    <div class="enrichment-fields">
                        ${enrichmentFieldsHtml}
                    </div>

                    <div class="enrichment-connector"></div>

                    <div class="enrichment-step">
                        <span class="enrichment-step-number">
                            03
                        </span>

                        <div>
                            <strong>Re-qualified</strong>

                            <p>
                                ${company.qualification_status}
                                · Final score
                                ${score.total_score}
                                · ${score.priority}
                            </p>
                        </div>
                    </div>
                </div>
            </section>
        `
        : "";

    const outreachHtml = outreach
        ? `
            <div class="company-outreach-card">
                <div>
                    <span>OUTREACH</span>
                    <strong>${outreach.status}</strong>
                </div>

                <p>
                    ${outreach.subject || "No subject"}
                </p>
            </div>
        `
        : `
            <div class="company-outreach-card muted">
                <div>
                    <span>OUTREACH</span>
                    <strong>NOT CREATED</strong>
                </div>

                <p>
                    No outreach message exists for
                    this company yet.
                </p>
            </div>
        `;

    panel.innerHTML = `
        <div class="company-detail-header">
            <div>
                <p class="eyebrow">
                    ${company.market}
                </p>

                <h3>${company.name}</h3>

                <p>
                    ${company.country}
                    ·
                    ${company.industry}
                    ·
                    ${company.employee_count || "—"} employees
                </p>
            </div>

            <div class="company-total-score">
                <strong>${score.total_score}</strong>
                <span>${score.priority}</span>
            </div>
        </div>

        <section class="intelligence-section">
            <div class="intelligence-section-title">
                <span>WHY IT FITS</span>
                <strong>${score.total_score} / 100</strong>
            </div>

            <div class="score-breakdown">
                ${scoreHtml}
            </div>
        </section>

        ${enrichmentHtml}

        <section class="intelligence-section">
            <div class="intelligence-section-title">
                <span>BUYING SIGNALS</span>
                <strong>${scoredSignalStatus}</strong>
            </div>

            <div class="signals-list">
                ${signalsHtml}
            </div>
        </section>

        <section class="intelligence-section">
            <div class="intelligence-section-title">
                <span>BUYER INTELLIGENCE</span>
                <strong>${scoredBuyerStatus}</strong>
            </div>

            ${buyerHtml}
        </section>

        ${outreachHtml}
    `;
}


document.addEventListener("click", async (event) => {
    const companyItem = event.target.closest(
        ".company-list-item"
    );

    if (!companyItem) {
        return;
    }

    await loadCompanyIntelligence(
        companyItem.dataset.companyId
    );
});


document.addEventListener("click", (event) => {
    const scoreRow = event.target.closest(
        "[data-score-explanation]"
    );

    if (!scoreRow) {
        return;
    }

    const isOpen = scoreRow.classList.toggle(
        "explanation-open"
    );

    scoreRow.setAttribute(
        "aria-expanded",
        String(isOpen)
    );
});


// OUTREACH WORKSPACE

let outreachLoaded = false;
let outreachWorkspaceData = null;
let activeOutreachFilter = "ALL";


function setOutreachMetric(id, value) {
    const element = document.getElementById(id);

    if (element) {
        element.textContent = value;
    }
}


function getOutreachWorkspaceMessages() {
    if (!outreachWorkspaceData) {
        return [];
    }

    return [
        ...(outreachWorkspaceData.review_queue || []),
        ...(outreachWorkspaceData.ready_to_send || []),
        ...(outreachWorkspaceData.sent_history || []),
        ...(outreachWorkspaceData.rejected_history || []),
    ];
}


function renderOutreachWorkspace() {
    const container = document.getElementById(
        "outreach-list"
    );

    if (!container || !outreachWorkspaceData) {
        return;
    }

    const messages = getOutreachWorkspaceMessages()
        .filter((message) => {
            return (
                activeOutreachFilter === "ALL" ||
                message.status === activeOutreachFilter
            );
        });

    if (!messages.length) {
        container.innerHTML = `
            <div class="queue-loading">
                <div class="empty-icon">✓</div>
                <h4>No outreach here</h4>
                <p>
                    No messages match this lifecycle state.
                </p>
            </div>
        `;
        return;
    }

    container.innerHTML = messages.map((message) => {
        let actionHtml = "";

        if (message.status === "DRAFT") {
            actionHtml = `
                <button
                    class="review-button"
                    type="button"
                    data-outreach-id="${message.id}"
                >
                    Review
                    <span>→</span>
                </button>
            `;
        }

        if (message.status === "APPROVED") {
            actionHtml = `
                <button
                    class="execute-button"
                    type="button"
                    data-execute-id="${message.id}"
                >
                    Execute
                    <span>→</span>
                </button>
            `;
        }

        if (message.status === "SENT") {
            actionHtml = `
                <button
                    class="execute-button"
                    type="button"
                    data-activity-id="${message.id}"
                >
                    View Activity
                    <span>→</span>
                </button>
            `;
        }

        if (message.status === "REJECTED") {
            actionHtml = `
                <button
                    class="review-button"
                    type="button"
                    data-outreach-id="${message.id}"
                >
                    View Details
                    <span>→</span>
                </button>
            `;
        }

        const statusClass = (
            message.status === "APPROVED" ||
            message.status === "SENT"
        )
            ? "approved-pill"
            : "status-pill";

        return `
            <article
                class="review-item send-item"
                data-outreach-status="${escapeHtml(
                    message.status
                )}"
            >
                <div class="review-item-main">
                    <div class="review-meta">
                        <span class="channel-pill">
                            ${escapeHtml(message.channel)}
                        </span>

                        <span class="${statusClass}">
                            ${escapeHtml(message.status)}
                        </span>

                        <span class="outreach-id">
                            #${message.id}
                        </span>
                    </div>

                    <h4>
                        ${escapeHtml(
                            message.subject ||
                            "Untitled outreach"
                        )}
                    </h4>

                    <p class="message-preview">
                        ${escapeHtml(message.message_body)}
                    </p>
                </div>

                ${actionHtml}
            </article>
        `;
    }).join("");
}


async function loadOutreachWorkspace() {
    const refreshButton = document.getElementById(
        "refresh-outreach"
    );

    try {
        if (refreshButton) {
            refreshButton.disabled = true;
            refreshButton.textContent = "Refreshing…";
        }

        const response = await fetch(
            `${API_BASE_URL}/api/outreach/dashboard/summary`
        );

        if (!response.ok) {
            throw new Error(
                `Outreach request failed: ${response.status}`
            );
        }

        const data = await response.json();

        outreachWorkspaceData = data;

        setOutreachMetric(
            "outreach-review-count",
            data.metrics.pending_review
        );

        setOutreachMetric(
            "outreach-approved-count",
            data.metrics.approved
        );

        setOutreachMetric(
            "outreach-sent-count",
            data.metrics.sent
        );

        setOutreachMetric(
            "outreach-rejected-count",
            data.metrics.rejected
        );

        renderOutreachWorkspace();

        outreachLoaded = true;

    } catch (error) {
        console.error(
            "Could not load outreach workspace:",
            error
        );

        const container = document.getElementById(
            "outreach-list"
        );

        if (container) {
            container.innerHTML = `
                <div class="queue-loading">
                    <div class="empty-icon">!</div>
                    <h4>Couldn't load outreach</h4>
                    <p>
                        Check that the FastAPI server is running.
                    </p>
                </div>
            `;
        }

    } finally {
        if (refreshButton) {
            refreshButton.disabled = false;
            refreshButton.textContent = "Refresh";
        }
    }
}


document.addEventListener("click", async (event) => {
    const filterButton = event.target.closest(
        "[data-outreach-filter]"
    );

    if (filterButton) {
        activeOutreachFilter =
            filterButton.dataset.outreachFilter;

        document.querySelectorAll(
            ".outreach-filter"
        ).forEach((button) => {
            button.classList.toggle(
                "active",
                button === filterButton
            );
        });

        renderOutreachWorkspace();
        return;
    }

    const refreshButton = event.target.closest(
        "#refresh-outreach"
    );

    if (refreshButton) {
        await loadOutreachWorkspace();
    }
});


// Company prospect filters

document.addEventListener("click", async (event) => {
    const filterButton = event.target.closest(
        "[data-company-filter]"
    );

    if (!filterButton) {
        return;
    }

    activeCompanyFilter =
        filterButton.dataset.companyFilter;

    document.querySelectorAll(
        "[data-company-filter]"
    ).forEach((button) => {
        button.classList.toggle(
            "active",
            button === filterButton
        );
    });

    const filtered =
        getFilteredCompanyProspects();

    renderCompaniesList(filtered);

    if (!filtered.length) {
        selectedCompanyId = null;
        return;
    }

    selectedCompanyId =
        filtered[0].company.id;

    await loadCompanyIntelligence(
        selectedCompanyId
    );
});


// COMPANY PROSPECT REPLENISHMENT

let companiesReplenishing = false;


function setReplenishmentButtonState(
    isLoading,
    label = null
) {
    const button = document.getElementById(
        "replenish-companies-button"
    );

    if (!button) {
        return;
    }

    button.disabled = isLoading;

    button.classList.toggle(
        "is-loading",
        isLoading
    );

    const labelElement = button.querySelector(
        "span:last-child"
    );

    if (labelElement) {
        labelElement.textContent = (
            label ||
            (isLoading ? "Checking..." : "Replenish")
        );
    }
}


function getReplenishmentResultLabel(result) {
    const newAccounts = result.new_accounts || 0;
    const qualified = result.qualified || 0;
    const needsReview = result.needs_review || 0;

    if (newAccounts === 0) {
        return "Up to date";
    }

    if (needsReview > 0) {
        return (
            `${newAccounts} new · ` +
            `${qualified} qualified · ` +
            `${needsReview} review`
        );
    }

    return (
        `${newAccounts} new · ` +
        `${qualified} qualified`
    );
}


async function replenishCompanies() {
    if (companiesReplenishing) {
        return;
    }

    companiesReplenishing = true;
    setReplenishmentButtonState(
        true,
        "Checking..."
    );

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/companies/replenish`,
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    icp_id: 3,
                    source: "clay_csv",
                    limit: 1000,
                }),
            }
        );

        if (!response.ok) {
            let message = (
                `Replenishment failed: ${response.status}`
            );

            try {
                const errorData = await response.json();

                if (errorData.detail) {
                    message = errorData.detail;
                }
            } catch (parseError) {
                // Keep the HTTP fallback message.
            }

            throw new Error(message);
        }

        const result = await response.json();

        selectedCompanyId = null;

        await loadCompanies();

        setReplenishmentButtonState(
            false,
            getReplenishmentResultLabel(result)
        );

        window.setTimeout(() => {
            setReplenishmentButtonState(
                false,
                "Replenish"
            );
        }, 5000);

    } catch (error) {
        console.error(
            "Could not replenish companies:",
            error
        );

        setReplenishmentButtonState(
            false,
            "Try again"
        );

        window.setTimeout(() => {
            setReplenishmentButtonState(
                false,
                "Replenish"
            );
        }, 5000);

    } finally {
        companiesReplenishing = false;
    }
}


document
    .getElementById("replenish-companies-button")
    ?.addEventListener(
        "click",
        replenishCompanies
    );
