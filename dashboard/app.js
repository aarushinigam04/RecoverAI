async function loadDashboard() {

    const refreshButton = document.getElementById("refresh-button");

    if (refreshButton) {
        refreshButton.textContent = "Refreshing...";
        refreshButton.disabled = true;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/dashboard");

        if (!response.ok) {
            throw new Error("Failed to load dashboard data");
        }

        const data = await response.json();

        // -----------------------------
        // Statistics
        // -----------------------------

        document.getElementById("total-payments").textContent =
            data.statistics.total_payments;

        document.getElementById("failed-payments").textContent =
            data.statistics.failed_payments;

        document.getElementById("executed-actions").textContent =
            data.statistics.executed_actions;

        document.getElementById("blocked-actions").textContent =
            data.statistics.blocked_actions;

        document.getElementById("human-review").textContent =
            data.statistics.human_review_cases;


        // -----------------------------
        // Failed Payments Table
        // -----------------------------

        const paymentsTable =
            document.getElementById("payments-table");

        paymentsTable.innerHTML = "";

        data.payments.forEach(payment => {

            const row = document.createElement("tr");

            let statusClass = "status-other";

            if (payment.status === "failed") {
                statusClass = "status-failed";
            } else if (payment.status === "success") {
                statusClass = "status-success";
            }

            row.innerHTML = `
                <td>${payment.payment_id}</td>
                <td>₹${payment.amount}</td>
                <td>${payment.currency}</td>
                <td>
                    <span class="status-badge ${statusClass}">
                        ${payment.status}
                    </span>
                </td>
                <td>${payment.failure_reason || "-"}</td>
            `;

            paymentsTable.appendChild(row);
        });


        // -----------------------------
        // Recovery Actions Table
        // -----------------------------

        const attemptsTable =
            document.getElementById("attempts-table");

        attemptsTable.innerHTML = "";

        data.payment_attempts.forEach(attempt => {

            let attemptStatusClass = "status-other";

            const status = attempt.status.toLowerCase();

            if (status === "failed") {

                attemptStatusClass = "status-failed";

            } else if (status === "success") {

                attemptStatusClass = "status-success";

            } else if (
                status === "retry_scheduled" ||
                status === "waiting_for_funds" ||
                status === "customer_action_required" ||
                status === "bank_contact_required"
            ) {

                attemptStatusClass = "status-executed";

            } else if (status === "retry_blocked") {

                attemptStatusClass = "status-blocked";

            } else if (status === "human_review_required") {

                attemptStatusClass = "status-review";

            } else if (status === "pending") {

                attemptStatusClass = "status-pending";
            }

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${attempt.attempt_id}</td>
                <td>${attempt.payment_id}</td>
                <td>
                    <span class="status-badge ${attemptStatusClass}">
                        ${attempt.status}
                    </span>
                </td>
                <td>${attempt.failure_reason || "-"}</td>
            `;

            attemptsTable.appendChild(row);
        });

    } catch (error) {

        console.error("Dashboard error:", error);

        alert("Unable to load dashboard data.");

    } finally {

        if (refreshButton) {
            refreshButton.textContent = "Refresh Dashboard";
            refreshButton.disabled = false;
        }
    }
}


// Load dashboard when page opens
loadDashboard();
// Automatically refresh dashboard every 60 seconds
setInterval(loadDashboard, 60000);