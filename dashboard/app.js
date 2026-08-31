async function loadDashboard() {

    const refreshButton =
        document.getElementById("refresh-button");


    // ---------------------------------------------------------
    // Refresh button state
    // ---------------------------------------------------------

    if (refreshButton) {

        refreshButton.textContent = "Refreshing...";

        refreshButton.disabled = true;

    }


    try {

        // -----------------------------------------------------
        // Get dashboard data from FastAPI
        // -----------------------------------------------------

        const response = await fetch(
            "http://127.0.0.1:8000/dashboard"
        );


        if (!response.ok) {

            throw new Error(
                "Failed to load dashboard data"
            );

        }


        const data = await response.json();


        console.log("Dashboard data:", data);


        // =====================================================
        // STATISTICS
        // =====================================================

        const statistics = data.statistics;


        // Total payments

        document.getElementById(
            "total-payments"
        ).textContent =
            statistics.total_payments;


        // Failed payments

        document.getElementById(
            "failed-payments"
        ).textContent =
            statistics.failed_payments;


        // Successful payments

        document.getElementById(
            "successful-payments"
        ).textContent =
            statistics.successful_payments;


        // Confirmed successful recoveries

        document.getElementById(
            "confirmed-successful-payments"
        ).textContent =
            statistics.confirmed_successful_payments;


        // Confirmed recovery rate

        document.getElementById(
            "recovery-rate"
        ).textContent =
            statistics.confirmed_payment_recovery_rate_percent
            + "%";


        // Executed actions

        document.getElementById(
            "executed-actions"
        ).textContent =
            statistics.executed_actions;


        // Blocked actions

        document.getElementById(
            "blocked-actions"
        ).textContent =
            statistics.blocked_actions;


        // Human review

        document.getElementById(
            "human-review"
        ).textContent =
            statistics.human_review_cases;


        // =====================================================
        // PAYMENTS TABLE
        // =====================================================

        const paymentsTable =
            document.getElementById(
                "payments-table"
            );


        paymentsTable.innerHTML = "";


        data.payments.forEach(
            payment => {

                const row =
                    document.createElement("tr");


                // -------------------------------------------------
                // Status class
                // -------------------------------------------------

                let statusClass =
                    "status-other";


                if (
                    payment.status === "failed"
                ) {

                    statusClass =
                        "status-failed";

                }

                else if (
                    payment.status === "success"
                ) {

                    statusClass =
                        "status-success";

                }


                // -------------------------------------------------
                // Row
                // -------------------------------------------------

                row.innerHTML = `

                    <td>
                        ${payment.payment_id}
                    </td>

                    <td>
                        ₹${Number(
                            payment.amount
                        ).toLocaleString("en-IN")}
                    </td>

                    <td>
                        ${payment.currency}
                    </td>

                    <td>

                        <span
                            class="status-badge ${statusClass}"
                        >
                            ${payment.status}
                        </span>

                    </td>

                    <td>
                        ${payment.failure_reason || "-"}
                    </td>

                `;


                paymentsTable.appendChild(row);

            }
        );


        // =====================================================
        // RECOVERY ACTIONS TABLE
        // =====================================================

        const attemptsTable =
            document.getElementById(
                "attempts-table"
            );


        attemptsTable.innerHTML = "";


        data.payment_attempts.forEach(
            attempt => {


                let attemptStatusClass =
                    "status-other";


                const status =
                    (
                        attempt.status || ""
                    ).toLowerCase();


                // -------------------------------------------------
                // Status mapping
                // -------------------------------------------------

                if (
                    status === "failed"
                ) {

                    attemptStatusClass =
                        "status-failed";

                }

                else if (
                    status === "success"
                ) {

                    attemptStatusClass =
                        "status-success";

                }

                else if (
                    status === "retry_scheduled" ||

                    status === "waiting_for_funds" ||

                    status === "customer_action_required" ||

                    status === "bank_contact_required"
                ) {

                    attemptStatusClass =
                        "status-executed";

                }

                else if (
                    status === "retry_blocked" ||

                    status === "blocked"
                ) {

                    attemptStatusClass =
                        "status-blocked";

                }

                else if (
                    status === "human_review_required" ||

                    status === "needs_human"
                ) {

                    attemptStatusClass =
                        "status-review";

                }

                else if (
                    status === "pending"
                ) {

                    attemptStatusClass =
                        "status-pending";

                }


                // -------------------------------------------------
                // Create row
                // -------------------------------------------------

                const row =
                    document.createElement("tr");


                row.innerHTML = `

                    <td>
                        ${attempt.attempt_id}
                    </td>

                    <td>
                        ${attempt.payment_id}
                    </td>

                    <td>

                        <span
                            class="status-badge ${attemptStatusClass}"
                        >
                            ${attempt.status}
                        </span>

                    </td>

                    <td>
                        ${attempt.failure_reason || "-"}
                    </td>

                `;


                attemptsTable.appendChild(row);

            }
        );


    }

    catch (error) {

        console.error(
            "Dashboard error:",
            error
        );


        alert(
            "Unable to load dashboard data."
        );

    }


    finally {

        if (refreshButton) {

            refreshButton.textContent =
                "Refresh Dashboard";

            refreshButton.disabled =
                false;

        }

    }

}


// =============================================================
// INITIAL LOAD
// =============================================================

loadDashboard();


// =============================================================
// AUTOMATIC REFRESH
// =============================================================

setInterval(
    loadDashboard,
    60000
);