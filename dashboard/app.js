async function loadDashboard() {
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
        // Payments Table
        // -----------------------------

        const paymentsTable =
            document.getElementById("payments-table");

        paymentsTable.innerHTML = "";

        data.payments.forEach(payment => {

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${payment.payment_id}</td>
                <td>₹${payment.amount}</td>
                <td>${payment.currency}</td>
                <td>${payment.status}</td>
                <td>${payment.failure_reason || "-"}</td>
            `;

            paymentsTable.appendChild(row);
        });


        // -----------------------------
        // Payment Attempts Table
        // -----------------------------

        const attemptsTable =
            document.getElementById("attempts-table");

        attemptsTable.innerHTML = "";

        data.payment_attempts.forEach(attempt => {

            const row = document.createElement("tr");

            row.innerHTML = `
                <td>${attempt.attempt_id}</td>
                <td>${attempt.payment_id}</td>
                <td>${attempt.status}</td>
                <td>${attempt.failure_reason || "-"}</td>
            `;

            attemptsTable.appendChild(row);
        });

    } catch (error) {

        console.error("Dashboard error:", error);

        alert("Unable to load dashboard data.");
    }
}


// Load dashboard when page opens
loadDashboard();