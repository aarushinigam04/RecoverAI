// =========================================================
// RecoverAI Command Center
// Dashboard Controller
// =========================================================


const API_URL =
    "http://127.0.0.1:8000/dashboard";


// =========================================================
// LOAD DASHBOARD
// =========================================================

async function loadDashboard() {

    const refreshButton =
        document.getElementById("refresh-button");


    if (refreshButton) {

        refreshButton.textContent =
            "↻ Refreshing...";

        refreshButton.disabled =
            true;

    }


    try {

        const response =
            await fetch(API_URL);


        if (!response.ok) {

            throw new Error(
                `Dashboard API returned ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "RecoverAI Dashboard:",
            data
        );


        // =====================================================
        // STATISTICS
        // =====================================================

        const stats =
            data.statistics || {};


        const totalPayments =
            Number(stats.total_payments) || 0;


        const failedPayments =
            Number(stats.failed_payments) || 0;


        const confirmedRecoveries =
            Number(
                stats.confirmed_successful_payments
            ) || 0;


        const executedActions =
            Number(
                stats.executed_actions
            ) || 0;


        const blockedActions =
            Number(
                stats.blocked_actions
            ) || 0;


        const humanReviewCases =
            Number(
                stats.human_review_cases
            ) || 0;


        const recoveryRate =
            clamp(
                Number(
                    stats.confirmed_payment_recovery_rate_percent
                ) || 0,
                0,
                100
            );


        const executionSuccessRate =
            clamp(
                Number(
                    stats.execution_success_rate_percent
                ) || 0,
                0,
                100
            );


        const recoveredRevenue =
            Number(
                stats.recovered_amount
            ) || 0;


        const revenueAtRisk =
            Number(
                stats.revenue_at_risk
            ) || 0;



        // =====================================================
        // KPI CARDS
        // =====================================================

        setText(
            "total-payments",
            totalPayments
        );


        setText(
            "failed-payments",
            failedPayments
        );


        setText(
            "successful-recoveries",
            confirmedRecoveries
        );


        setText(
            "executed-actions",
            executedActions
        );


        setText(
            "blocked-actions",
            blockedActions
        );


        setText(
            "human-review",
            humanReviewCases
        );


        setText(
            "recovery-rate",
            recoveryRate.toFixed(2) + "%"
        );


        setText(
            "donut-rate",
            recoveryRate.toFixed(2) + "%"
        );


        setText(
            "execution-success-rate",
            executionSuccessRate.toFixed(2) + "%"
        );



        // =====================================================
        // REVENUE
        // =====================================================

        setText(
            "recovered-revenue",
            formatCurrency(
                recoveredRevenue
            )
        );


        setText(
            "revenue-success",
            formatCurrency(
                recoveredRevenue
            )
        );


        setText(
            "revenue-risk",
            formatCurrency(
                revenueAtRisk
            )
        );



        // =====================================================
        // COHORT
        // =====================================================

        setText(
            "cohort-size",
            `${totalPayments} Payments`
        );



        // =====================================================
        // DONUT
        // =====================================================

        updateDonut(
            recoveryRate
        );



        // =====================================================
        // PAYMENT DATA
        // =====================================================

        const payments =
            Array.isArray(
                data.payments
            )
                ? data.payments
                : [];


        const attempts =
            Array.isArray(
                data.payment_attempts
            )
                ? data.payment_attempts
                : [];



        // =====================================================
        // FAILURE ANALYSIS
        // =====================================================
        //
        // Prefer backend-provided analysis.
        // This keeps the dashboard synchronized with
        // the same data used by the API.
        // =====================================================

        let failureAnalysis =
            Array.isArray(
                data.failure_analysis
            )
                ? data.failure_analysis
                : [];


        if (!failureAnalysis.length) {

            failureAnalysis =
                buildFailureAnalysis(
                    payments
                );

        }


        renderFailureAnalysis(
            failureAnalysis
        );



        // =====================================================
        // RECOVERY FUNNEL
        // =====================================================

        renderFunnel(
            {
                failed_payments:
                    failedPayments,

                executed_actions:
                    executedActions,

                confirmed_successful_payments:
                    confirmedRecoveries
            }
        );



        // =====================================================
        // AI DECISION
        // =====================================================

        renderAIDecision(
            data.ai_decision || null
        );



        // =====================================================
        // SAFETY CENTER
        // =====================================================

        setText(
            "safety-approved",
            executedActions
        );


        setText(
            "safety-blocked",
            blockedActions
        );


        setText(
            "safety-human",
            humanReviewCases
        );



        // =====================================================
        // RECENT PAYMENTS
        // =====================================================

        let recentPayments =
            Array.isArray(
                data.recent_payments
            )
                ? data.recent_payments
                : [];


        if (!recentPayments.length) {

            recentPayments =
                payments
                    .slice()
                    .sort(
                        (
                            a,
                            b
                        ) =>
                            Number(
                                b.payment_id
                            ) -
                            Number(
                                a.payment_id
                            )
                    )
                    .slice(
                        0,
                        12
                    );

        }


        renderPayments(
            recentPayments
        );



        // =====================================================
        // RECOVERY ATTEMPTS
        // =====================================================

        renderAttempts(
            attempts
        );



        // =====================================================
        // LAST UPDATED
        // =====================================================

        updateLastUpdated();


        clearDashboardError();

    }


    catch (error) {

        console.error(
            "RecoverAI dashboard error:",
            error
        );


        showError(
            "Unable to load RecoverAI dashboard data. Make sure FastAPI is running."
        );

    }


    finally {

        if (refreshButton) {

            refreshButton.textContent =
                "↻ Refresh";

            refreshButton.disabled =
                false;

        }

    }

}



// =========================================================
// SET TEXT
// =========================================================

function setText(
    id,
    value
) {

    const element =
        document.getElementById(id);


    if (element) {

        element.textContent =
            value;

    }

}



// =========================================================
// CLAMP
// =========================================================

function clamp(
    value,
    minimum,
    maximum
) {

    return Math.max(
        minimum,
        Math.min(
            maximum,
            value
        )
    );

}



// =========================================================
// CURRENCY FORMAT
// =========================================================

function formatCurrency(
    amount
) {

    const value =
        Number(amount) || 0;


    return (
        "₹" +
        value.toLocaleString(
            "en-IN",
            {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }
        )
    );

}



// =========================================================
// DONUT
// =========================================================

function updateDonut(
    recoveryRate
) {

    const donut =
        document.querySelector(
            ".donut"
        );


    if (!donut) {
        return;
    }


    const boundedRate =
        clamp(
            Number(
                recoveryRate
            ) || 0,
            0,
            100
        );


    donut.style.setProperty(
        "--recovery",
        `${boundedRate * 3.6}deg`
    );

}



// =========================================================
// FAILURE ANALYSIS
// =========================================================

function buildFailureAnalysis(
    payments
) {

    const counts = {};


    payments
        .filter(
            payment =>
                String(
                    payment.status || ""
                ).toLowerCase() === "failed"
        )
        .forEach(
            payment => {

                const reason =
                    payment.failure_reason ||
                    "Unknown failure";


                counts[reason] =
                    (
                        counts[reason] || 0
                    ) + 1;

            }
        );


    return Object
        .entries(
            counts
        )
        .map(
            (
                [
                    reason,
                    count
                ]
            ) => ({
                reason,
                count
            })
        )
        .sort(
            (
                a,
                b
            ) =>
                b.count -
                a.count
        );

}



// =========================================================
// RENDER FAILURE ANALYSIS
// =========================================================

function renderFailureAnalysis(
    failures
) {

    const container =
        document.getElementById(
            "failure-analysis"
        );


    if (!container) {
        return;
    }


    container.innerHTML =
        "";


    if (
        !failures ||
        !failures.length
    ) {

        container.innerHTML =
            `
            <div class="empty">
                No failed payments
            </div>
            `;

        return;

    }


    const maximum =
        Math.max(
            ...failures.map(
                item =>
                    Number(
                        item.count
                    ) || 0
            )
        );


    failures
        .slice(
            0,
            10
        )
        .forEach(
            item => {

                const count =
                    Number(
                        item.count
                    ) || 0;


                const percentage =
                    maximum > 0
                        ? (
                            count /
                            maximum
                        ) * 100
                        : 0;


                const row =
                    document.createElement(
                        "div"
                    );


                row.className =
                    "failure-item";


                row.innerHTML =
                    `
                    <div class="failure-label">

                        <span>
                            ${escapeHTML(
                                item.reason
                            )}
                        </span>

                        <strong>
                            ${count}
                        </strong>

                    </div>

                    <div class="failure-track">

                        <span
                            style="width:${percentage}%"
                        ></span>

                    </div>
                    `;


                container.appendChild(
                    row
                );

            }
        );

}



// =========================================================
// RECOVERY FUNNEL
// =========================================================

function renderFunnel(
    stats
) {

    const failed =
        Number(
            stats.failed_payments
        ) || 0;


    const actions =
        Number(
            stats.executed_actions
        ) || 0;


    const recovered =
        Number(
            stats.confirmed_successful_payments
        ) || 0;


    setText(
        "funnel-failed",
        failed
    );


    setText(
        "funnel-actions",
        actions
    );


    setText(
        "funnel-recovered",
        recovered
    );


    const actionsBar =
        document.getElementById(
            "actions-bar"
        );


    const recoveredBar =
        document.getElementById(
            "recovered-bar"
        );


    if (actionsBar) {

        const percentage =
            failed > 0
                ? (
                    actions /
                    failed
                ) * 100
                : 0;


        actionsBar.style.width =
            `${clamp(
                percentage,
                0,
                100
            )}%`;

    }


    if (recoveredBar) {

        const percentage =
            failed > 0
                ? (
                    recovered /
                    failed
                ) * 100
                : 0;


        recoveredBar.style.width =
            `${clamp(
                percentage,
                0,
                100
            )}%`;

    }

}



// =========================================================
// AI DECISION CENTER
// =========================================================

function renderAIDecision(
    decision
) {

    const container =
        document.getElementById(
            "ai-decision"
        );


    if (!container) {
        return;
    }


    if (
        !decision ||
        decision.error
    ) {

        container.innerHTML =
            `
            <div class="empty">

                <strong>
                    RecoverAI Decision Engine
                </strong>

                <small>
                    No AI decision preview is currently available.
                </small>

            </div>
            `;

        return;

    }


    /*
     * Current backend structure:
     *
     * decision
     * ├── payment_id
     * ├── amount
     * ├── failure_reason
     * └── diagnosis
     *     ├── diagnosis
     *     │   ├── category
     *     │   ├── reason
     *     │   └── confidence
     *     ├── recovery
     *     │   ├── recommended_action
     *     │   ├── delay_minutes
     *     │   ├── success_probability
     *     │   └── expected_recovery
     *     ├── risk_flags
     *     ├── requires_human
     *     └── explanation
     *
     * decision.policy
     * ├── policy_decision
     * ├── approved_action
     * └── reason
     */


    const agent =
        decision.diagnosis || {};


    const diagnosis =
        agent.diagnosis || {};


    const recovery =
        agent.recovery || {};


    const policy =
        decision.policy || {};


    const diagnosisCategory =
        diagnosis.category ||
        "Unknown";


    const diagnosisReason =
        diagnosis.reason ||
        decision.failure_reason ||
        "Failure detected";


    const recommendedAction =
        recovery.recommended_action ||
        policy.approved_action ||
        "Review";


    const confidenceValue =
        Number(
            diagnosis.confidence
        );


    const confidence =
        Number.isFinite(
            confidenceValue
        )
            ? (
                confidenceValue <= 1
                    ? confidenceValue * 100
                    : confidenceValue
            )
            : null;


    const probabilityValue =
        Number(
            recovery.success_probability
        );


    const recoveryProbability =
        Number.isFinite(
            probabilityValue
        )
            ? (
                probabilityValue <= 1
                    ? probabilityValue * 100
                    : probabilityValue
            )
            : null;


    const expectedRecovery =
        Number(
            recovery.expected_recovery
        );


    const policyDecision =
        policy.policy_decision ||
        "REVIEW";


    const policyReason =
        policy.reason ||
        "Policy evaluation completed";


    const riskFlags =
        Array.isArray(
            agent.risk_flags
        )
            ? agent.risk_flags
            : [];


    const riskText =
        riskFlags.length
            ? riskFlags.join(", ")
            : "No active risk flags";


    container.innerHTML =
        `

        <div class="decision-card">

            <span>
                PAYMENT
            </span>

            <strong>
                #${escapeHTML(
                    decision.payment_id
                )}
            </strong>

            <small>
                ${formatCurrency(
                    decision.amount
                )}
            </small>

        </div>


        <div class="decision-arrow">
            →
        </div>


        <div class="decision-card">

            <span>
                DIAGNOSIS
            </span>

            <strong>
                ${escapeHTML(
                    diagnosisCategory
                )}
            </strong>

            <small>
                ${escapeHTML(
                    diagnosisReason
                )}
            </small>

        </div>


        <div class="decision-arrow">
            →
        </div>


        <div class="decision-card">

            <span>
                CONFIDENCE
            </span>

            <strong>
                ${
                    confidence !== null
                        ? confidence.toFixed(0) + "%"
                        : "—"
                }
            </strong>

            <small>
                AI diagnostic confidence
            </small>

        </div>


        <div class="decision-arrow">
            →
        </div>


        <div class="decision-card">

            <span>
                RECOVERY
            </span>

            <strong>
                ${
                    recoveryProbability !== null
                        ? recoveryProbability.toFixed(0) + "%"
                        : "—"
                }
            </strong>

            <small>
                Expected success probability
            </small>

        </div>


        <div class="decision-arrow">
            →
        </div>


        <div class="decision-card">

            <span>
                POLICY
            </span>

            <strong class="${policyClass(
                policyDecision
            )}">
                ${escapeHTML(
                    String(
                        policyDecision
                    ).toUpperCase()
                )}
            </strong>

            <small>
                ${escapeHTML(
                    policyReason
                )}
            </small>

        </div>


        <div class="decision-arrow">
            →
        </div>


        <div class="decision-card highlight">

            <span>
                ACTION
            </span>

            <strong>
                ${escapeHTML(
                    formatAction(
                        recommendedAction
                    )
                )}
            </strong>

            <small>
                Controlled execution
            </small>

        </div>


        <div class="decision-extra">

            <div>

                <span>
                    Expected Recovery
                </span>

                <strong>
                    ${
                        Number.isFinite(
                            expectedRecovery
                        )
                            ? formatCurrency(
                                expectedRecovery
                            )
                            : "—"
                    }
                </strong>

            </div>


            <div>

                <span>
                    Delay
                </span>

                <strong>
                    ${
                        Number.isFinite(
                            Number(
                                recovery.delay_minutes
                            )
                        )
                            ? `${Number(
                                recovery.delay_minutes
                            )} min`
                            : "—"
                    }
                </strong>

            </div>


            <div>

                <span>
                    Risk Flags
                </span>

                <strong>
                    ${escapeHTML(
                        riskText
                    )}
                </strong>

            </div>

        </div>

        `;

}



// =========================================================
// POLICY CLASS
// =========================================================

function policyClass(
    decision
) {

    const value =
        String(
            decision || ""
        ).toUpperCase();


    if (
        value === "APPROVED"
    ) {

        return "policy-approved";

    }


    if (
        value === "BLOCKED"
    ) {

        return "policy-blocked";

    }


    if (
        value === "NEEDS_HUMAN"
    ) {

        return "policy-human";

    }


    return "";

}



// =========================================================
// FORMAT ACTION
// =========================================================

function formatAction(
    action
) {

    return String(
        action || "Review"
    )
        .replace(
            /_/g,
            " "
        )
        .replace(
            /\b\w/g,
            letter =>
                letter.toUpperCase()
        );

}



// =========================================================
// PAYMENTS TABLE
// =========================================================

function renderPayments(
    payments
) {

    const table =
        document.getElementById(
            "payments-table"
        );


    if (!table) {
        return;
    }


    table.innerHTML =
        "";


    if (
        !payments ||
        !payments.length
    ) {

        table.innerHTML =
            `
            <tr>

                <td
                    colspan="4"
                    class="empty"
                >
                    No payment records found.
                </td>

            </tr>
            `;

        return;

    }


    payments
        .slice(
            0,
            12
        )
        .forEach(
            payment => {

                const row =
                    document.createElement(
                        "tr"
                    );


                const status =
                    String(
                        payment.status || ""
                    ).toLowerCase();


                let statusClass =
                    "status-other";


                if (
                    status === "success" ||
                    status === "captured" ||
                    status === "paid"
                ) {

                    statusClass =
                        "status-success";

                }


                else if (
                    status === "failed"
                ) {

                    statusClass =
                        "status-failed";

                }


                row.innerHTML =
                    `

                    <td>
                        #${escapeHTML(
                            payment.payment_id
                        )}
                    </td>

                    <td>
                        ${formatCurrency(
                            payment.amount
                        )}
                    </td>

                    <td>

                        <span
                            class="status ${statusClass}"
                        >
                            ${escapeHTML(
                                payment.status ||
                                "unknown"
                            )}
                        </span>

                    </td>

                    <td>
                        ${escapeHTML(
                            payment.failure_reason ||
                            "—"
                        )}
                    </td>

                    `;


                table.appendChild(
                    row
                );

            }
        );

}



// =========================================================
// PAYMENT ATTEMPTS
// =========================================================

function renderAttempts(
    attempts
) {

    const table =
        document.getElementById(
            "attempts-table"
        );


    if (!table) {
        return;
    }


    table.innerHTML =
        "";


    if (
        !attempts ||
        !attempts.length
    ) {

        table.innerHTML =
            `
            <tr>

                <td
                    colspan="4"
                    class="empty"
                >
                    No recovery attempts recorded.
                </td>

            </tr>
            `;

        return;

    }


    const latestAttempts =
        attempts
            .slice()
            .sort(
                (
                    a,
                    b
                ) =>
                    Number(
                        b.attempt_id
                    ) -
                    Number(
                        a.attempt_id
                    )
            )
            .slice(
                0,
                20
            );


    latestAttempts.forEach(
        attempt => {

            const row =
                document.createElement(
                    "tr"
                );


            const status =
                String(
                    attempt.status || ""
                ).toLowerCase();


            let statusClass =
                "status-other";


            if (
                status === "success"
            ) {

                statusClass =
                    "status-success";

            }


            else if (
                status === "failed"
            ) {

                statusClass =
                    "status-failed";

            }


            else if (
                status === "retry_scheduled" ||
                status === "waiting_for_funds" ||
                status === "customer_action_required" ||
                status === "bank_contact_required"
            ) {

                statusClass =
                    "status-executed";

            }


            else if (
                status === "retry_blocked" ||
                status === "blocked"
            ) {

                statusClass =
                    "status-blocked";

            }


            else if (
                status === "human_review_required" ||
                status === "needs_human"
            ) {

                statusClass =
                    "status-review";

            }


            else if (
                status === "pending"
            ) {

                statusClass =
                    "status-pending";

            }


            row.innerHTML =
                `

                <td>
                    #${escapeHTML(
                        attempt.attempt_id
                    )}
                </td>

                <td>
                    #${escapeHTML(
                        attempt.payment_id
                    )}
                </td>

                <td>

                    <span
                        class="status ${statusClass}"
                    >
                        ${escapeHTML(
                            attempt.status ||
                            "unknown"
                        )}
                    </span>

                </td>

                <td>
                    ${escapeHTML(
                        attempt.failure_reason ||
                        "—"
                    )}
                </td>

                `;


            table.appendChild(
                row
            );

        }
    );

}



// =========================================================
// LAST UPDATED
// =========================================================

function updateLastUpdated() {

    const now =
        new Date();


    setText(
        "last-updated",
        now.toLocaleTimeString(
            "en-IN",
            {
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit"
            }
        )
    );

}



// =========================================================
// ERROR MESSAGE
// =========================================================

function showError(
    message
) {

    const main =
        document.querySelector(
            ".main"
        );


    if (!main) {
        return;
    }


    clearDashboardError();


    const error =
        document.createElement(
            "div"
        );


    error.className =
        "dashboard-error";


    error.textContent =
        message;


    main.prepend(
        error
    );

}



// =========================================================
// CLEAR ERROR
// =========================================================

function clearDashboardError() {

    const existing =
        document.querySelector(
            ".dashboard-error"
        );


    if (existing) {

        existing.remove();

    }

}



// =========================================================
// HTML SAFETY
// =========================================================

function escapeHTML(
    value
) {

    return String(
        value ?? ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}



// =========================================================
// SIDEBAR NAVIGATION
// =========================================================

function setupNavigation() {

    const navItems =
        document.querySelectorAll(
            ".nav-item"
        );


    navItems.forEach(
        item => {

            item.addEventListener(
                "click",
                () => {

                    navItems.forEach(
                        nav =>
                            nav.classList.remove(
                                "active"
                            )
                    );


                    item.classList.add(
                        "active"
                    );

                }
            );

        }
    );

}



// =========================================================
// INITIAL LOAD
// =========================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupNavigation();

        loadDashboard();

    }
);



// =========================================================
// AUTOMATIC REFRESH
// =========================================================
//
// No live stream.
// Dashboard refreshes every 60 seconds.
// =========================================================

setInterval(
    loadDashboard,
    60000
);