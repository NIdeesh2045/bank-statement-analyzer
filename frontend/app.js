/* ============================================================
   BANK STATEMENT ANALYZER
   FRONTEND JAVASCRIPT
============================================================ */

/* ============================================================
   CONFIGURATION
============================================================ */

const API = "http://127.0.0.1:8000";


/* ============================================================
   GLOBAL STATE
============================================================ */

let currentStatementId = null;

let allTransactions = [];

let incomeExpenseChart = null;
let categoryChart = null;
let monthlyFinancialChart = null;
let savingsChart = null;
let topCategoryChart = null;
let dailySpendingChart = null;


/* ============================================================
   BASIC HELPERS
============================================================ */

function formatMoney(value) {

    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "₹ 0.00";
    }

    return "₹ " + number.toLocaleString(
        "en-IN",
        {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }
    );
}


function safeNumber(value) {

    const number = Number(value);

    return Number.isFinite(number)
        ? number
        : 0;
}


function escapeHtml(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


/* ============================================================
   TRANSACTION HELPERS
============================================================ */

function getTransactionType(transaction) {

    return String(
        transaction?.transaction_type ||
        transaction?.type ||
        ""
    )
        .trim()
        .toUpperCase();
}


function getTransactionAmount(transaction) {

    return safeNumber(
        transaction?.amount ??
        transaction?.transaction_amount ??
        0
    );
}


function getTransactionDate(transaction) {

    return String(
        transaction?.transaction_date ||
        transaction?.date ||
        ""
    ).trim();
}


function getTransactionCategory(transaction) {

    return String(
        transaction?.category ||
        "Other"
    ).trim() || "Other";
}


function getTransactionDescription(transaction) {

    return String(
        transaction?.description ||
        transaction?.narration ||
        "No description"
    ).trim() || "No description";
}


/* ============================================================
   ERROR HANDLING
============================================================ */

function showError(message) {

    const element =
        document.getElementById("errorMessage");

    if (!element) {
        return;
    }

    element.innerText =
        message || "Something went wrong.";

    element.style.display = "block";
}


function hideError() {

    const element =
        document.getElementById("errorMessage");

    if (!element) {
        return;
    }

    element.innerText = "";

    element.style.display = "none";
}


/* ============================================================
   API REQUEST HELPER
============================================================ */

async function apiRequest(
    endpoint,
    options = {}
) {

    const token =
        localStorage.getItem("access_token");

    const headers = {
        ...(options.headers || {})
    };

    if (token) {

        headers["Authorization"] =
            `Bearer ${token}`;
    }

    const response =
        await fetch(
            `${API}${endpoint}`,
            {
                ...options,
                headers: headers
            }
        );

    let data = null;

    try {

        data = await response.json();

    }
    catch {

        data = null;
    }

    if (!response.ok) {

        const message =
            data?.detail ||
            data?.message ||
            "Request failed.";

        throw new Error(message);
    }

    return data;
}


/* ============================================================
   LOGIN
============================================================ */

window.loginUser =
    async function loginUser() {

        hideError();

        const emailElement =
            document.getElementById("loginEmail");

        const passwordElement =
            document.getElementById("loginPassword");

        if (!emailElement || !passwordElement) {
            return;
        }

        const email =
            emailElement.value.trim();

        const password =
            passwordElement.value;

        if (!email || !password) {

            showError(
                "Please enter email and password."
            );

            return;
        }

        try {

            const data =
                await apiRequest(
                    "/login",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email: email,
                            password: password
                        })
                    }
                );

            if (!data?.access_token) {

                throw new Error(
                    "Login token was not received."
                );
            }

            localStorage.setItem(
                "access_token",
                data.access_token
            );

            if (data.user_name) {

                localStorage.setItem(
                    "user_name",
                    data.user_name
                );
            }

            if (data.email) {

                localStorage.setItem(
                    "user_email",
                    data.email
                );
            }
            else {

                localStorage.setItem(
                    "user_email",
                    email
                );
            }

            const loginScreen =
                document.getElementById(
                    "loginScreen"
                );

            const dashboard =
                document.querySelector(
                    ".container"
                );

            if (loginScreen) {

                loginScreen.style.display =
                    "none";
            }

            if (dashboard) {

                dashboard.style.display =
                    "block";
            }

            updateUserInfo();

            await loadDashboard();

        }
        catch (error) {

            console.error(
                "Login error:",
                error
            );

            showError(
                error.message ||
                "Invalid email or password."
            );
        }
    };


/* ============================================================
   UPDATE USER INFORMATION
============================================================ */

function updateUserInfo() {

    const userName =
        localStorage.getItem("user_name");

    const userEmail =
        localStorage.getItem("user_email");

    const nameElements =
        document.querySelectorAll(
            "#userName, #username, .user-name"
        );

    nameElements.forEach(
        element => {

            if (userName) {

                element.innerText =
                    userName;
            }
        }
    );

    const emailElements =
        document.querySelectorAll(
            "#userEmail, .user-email"
        );

    emailElements.forEach(
        element => {

            if (userEmail) {

                element.innerText =
                    userEmail;
            }
        }
    );
}


/* ============================================================
   LOGOUT
============================================================ */

window.logoutUser =
    function logoutUser() {

        localStorage.removeItem(
            "access_token"
        );

        localStorage.removeItem(
            "user_name"
        );

        localStorage.removeItem(
            "user_email"
        );

        currentStatementId = null;

        allTransactions = [];

        resetDashboard();

        const loginScreen =
            document.getElementById(
                "loginScreen"
            );

        const dashboard =
            document.querySelector(
                ".container"
            );

        if (dashboard) {

            dashboard.style.display =
                "none";
        }

        if (loginScreen) {

            loginScreen.style.display =
                "flex";
        }
    };


/* ============================================================
   REGISTRATION
============================================================ */

window.registerUser =
    async function registerUser() {

        hideError();

        const nameElement =
            document.getElementById(
                "registerName"
            );

        const emailElement =
            document.getElementById(
                "registerEmail"
            );

        const passwordElement =
            document.getElementById(
                "registerPassword"
            );

        if (
            !nameElement ||
            !emailElement ||
            !passwordElement
        ) {
            return;
        }

        const name =
            nameElement.value.trim();

        const email =
            emailElement.value.trim();

        const password =
            passwordElement.value;

        if (!name || !email || !password) {

            showError(
                "Please fill all registration fields."
            );

            return;
        }

        try {

            const data =
                await apiRequest(
                    "/register",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            name: name,
                            email: email,
                            password: password
                        })
                    }
                );

            console.log(
                "Registration successful:",
                data
            );

            alert(
                "Registration successful. Please login."
            );

        }
        catch (error) {

            console.error(
                "Registration error:",
                error
            );

            showError(
                error.message ||
                "Registration failed."
            );
        }
    };


/* ============================================================
   API URL
============================================================ */

function apiUrl(endpoint) {

    if (
        currentStatementId === null ||
        currentStatementId === undefined
    ) {

        return endpoint;
    }

    const separator =
        endpoint.includes("?")
            ? "&"
            : "?";

    return (
        endpoint +
        separator +
        `statement_id=${encodeURIComponent(
            currentStatementId
        )}`
    );
}


/* ============================================================
   RESET DASHBOARD
============================================================ */

function resetDashboard() {

    currentStatementId = null;

    allTransactions = [];

    const ids = [

        "totalIncome",
        "totalExpense",
        "currentBalance",
        "highestExpense",
        "transactionCount",
        "healthScore",
        "savingsRate",
        "totalSavings",
        "topCategory",
        "spendingStatus",
        "analyticsCategory",
        "averageTransaction",
        "recommendation"

    ];

    ids.forEach(
        id => {

            const element =
                document.getElementById(id);

            if (!element) {
                return;
            }

            element.innerText =
                id === "healthScore"
                    ? "0/100"
                    : "₹ 0.00";
        }
    );

    const status =
        document.getElementById(
            "spendingStatus"
        );

    if (status) {

        status.innerText =
            "No spending data available.";
    }

    const recommendation =
        document.getElementById(
            "recommendation"
        );

    if (recommendation) {

        recommendation.innerText =
            "No recommendation available.";
    }

    const topCategory =
        document.getElementById(
            "topCategory"
        );

    if (topCategory) {

        topCategory.innerText =
            "N/A";
    }

    const analyticsCategory =
        document.getElementById(
            "analyticsCategory"
        );

    if (analyticsCategory) {

        analyticsCategory.innerText =
            "N/A";
    }

    const transactionTable =
        document.getElementById(
            "transactionTable"
        );

    if (transactionTable) {

        transactionTable.innerHTML = `
            <tr>
                <td colspan="5">
                    No transactions found.
                </td>
            </tr>
        `;
    }

    const filterSummary =
        document.getElementById(
            "filterSummary"
        );

    if (filterSummary) {

        filterSummary.innerText = "";
    }

    [
        incomeExpenseChart,
        categoryChart,
        monthlyFinancialChart,
        savingsChart,
        topCategoryChart,
        dailySpendingChart
    ].forEach(
        chart => {

            if (chart) {

                try {
                    chart.destroy();
                }
                catch {

                    /* Ignore chart destroy errors */
                }
            }
        }
    );

    incomeExpenseChart = null;
    categoryChart = null;
    monthlyFinancialChart = null;
    savingsChart = null;
    topCategoryChart = null;
    dailySpendingChart = null;
}


/* ============================================================
   LATEST STATEMENT
============================================================ */

async function loadLatestStatement() {

    try {

        const data =
            await apiRequest(
                "/latest-statement"
            );
        console.log("LATEST STATEMENT RESPONSE:", data);

        if (
            data?.success &&
            data?.statement
        ) {

            setCurrentStatement(
                data.statement
            );

            return true;
        }

        if (data?.statement) {

            setCurrentStatement(
                data.statement
            );

            return true;
        }

        setNoStatement();

        return false;

    }
    catch (error) {

        console.error(
            "Latest statement error:",
            error
        );

        setNoStatement();

        return false;
    }
}


/* ============================================================
   SET CURRENT STATEMENT
============================================================ */
function setCurrentStatement(statement) {
    if (!statement) {
        setNoStatement();
        return;
    }

    currentStatementId =
        statement.statement_id ??
        statement.id ??
        statement.statementId ??
        null;

    const fileName =
        statement.file_name ??
        statement.filename ??
        statement.fileName ??
        statement.name ??
        "Unknown Statement";

    const statementId =
        currentStatementId ??
        "-";

    const fileElement = document.getElementById("statementFile");
    const idElement = document.getElementById("statementId");

    if (fileElement) {
        fileElement.innerText = fileName;
    }

    if (idElement) {
        idElement.innerText = `Statement ID: ${statementId}`;
    }

    console.log("Current statement:", statement);
    console.log("Current statement ID:", currentStatementId);
    console.log("Current statement file:", fileName);
}


/* ============================================================
   NO STATEMENT
============================================================ */

function setNoStatement() {

    currentStatementId = null;

    const fileNameElement =
        document.getElementById(
            "fileName"
        );

    if (fileNameElement) {

        fileNameElement.innerText =
            "No statement selected";
    }

    const statementIdElement =
        document.getElementById(
            "statementId"
        );

    if (statementIdElement) {

        statementIdElement.innerText =
            "-";
    }

    const selectedStatementElement =
        document.getElementById(
            "selectedStatement"
        );

    if (selectedStatementElement) {

        selectedStatementElement.innerText =
            "No statement selected";
    }
}


/* ============================================================
   UPLOAD STATEMENT
============================================================ */

window.uploadStatement =
    async function uploadStatement() {

        hideError();

        const fileInput =
            document.getElementById(
                "statementFile"
            );

        if (!fileInput || !fileInput.files.length) {

            showError(
                "Please select a PDF statement."
            );

            return;
        }

        const file =
            fileInput.files[0];

        const fileName =
            file.name.toLowerCase();

        if (!fileName.endsWith(".pdf")) {

            showError(
                "Only PDF files are allowed."
            );

            return;
        }

        try {

            const formData =
                new FormData();

            formData.append(
                "file",
                file
            );

            const data =
                await apiRequest(
                    "/upload-statement",
                    {
                        method: "POST",
                        body: formData
                    }
                );

            console.log(
                "Upload successful:",
                data
            );

            alert(
                "Statement uploaded successfully."
            );

            fileInput.value = "";

            await loadDashboard();

        }
        catch (error) {

            console.error(
                "Upload error:",
                error
            );

            showError(
                error.message ||
                "Statement upload failed."
            );
        }
    };


/* ============================================================
   STATEMENT HISTORY
============================================================ */

async function loadStatements() {

    const select =
        document.getElementById(
            "statementSelect"
        );

    const count =
        document.getElementById(
            "statementCount"
        );

    if (!select) {
        return;
    }

    try {

        const data =
            await apiRequest(
                "/statements"
            );

        const statements =
            Array.isArray(data?.statements)
                ? data.statements
                : Array.isArray(data)
                    ? data
                    : [];

        select.innerHTML = "";

        if (!statements.length) {

            select.innerHTML = `
                <option value="">
                    No statements available
                </option>
            `;

            if (count) {

                count.innerText =
                    "0 statements available";
            }

            return;
        }

        if (count) {

            count.innerText =
                `${statements.length} statement${
                    statements.length === 1
                        ? ""
                        : "s"
                } available`;
        }

        statements.sort(
            (a, b) =>
                Number(b.statement_id) -
                Number(a.statement_id)
        );

        statements.forEach(
            statement => {

                const option =
                    document.createElement(
                        "option"
                    );

                option.value =
                    statement.statement_id;

                option.textContent =
                    `${statement.file_name || "Unnamed statement"} — ID ${
                        statement.statement_id
                    }${
                        statement.upload_date
                            ? " — " +
                              statement.upload_date
                            : ""
                    }`;

                select.appendChild(
                    option
                );
            }
        );

        if (currentStatementId !== null) {

            const exists =
                statements.some(
                    statement =>
                        Number(
                            statement.statement_id
                        ) ===
                        Number(
                            currentStatementId
                        )
                );

            if (exists) {

                select.value =
                    currentStatementId;

            }
            else if (statements.length > 0) {

                select.value =
                    statements[0].statement_id;

            }
            else {

                select.value = "";
            }

        }
        else if (statements.length > 0) {

            select.value =
                statements[0].statement_id;

        }
        else {

            select.value = "";
        }

        select.onchange =
            async function () {

                if (!this.value) {
                    return;
                }

                await selectStatement(
                    Number(this.value)
                );
            };

    }
    catch (error) {

        console.error(
            "Statement history error:",
            error
        );

        select.innerHTML = `
            <option value="">
                Unable to load statements
            </option>
        `;

        if (count) {

            count.innerText =
                "Unable to load statement history.";
        }
    }
}


/* ============================================================
   SELECT STATEMENT
============================================================ */

async function selectStatement(
    statementId
) {

    const id =
        Number(statementId);

    if (!Number.isFinite(id)) {
        return;
    }

    hideError();

    currentStatementId = id;

    const select =
        document.getElementById(
            "statementSelect"
        );

    if (select) {

        select.value = id;
    }

    /*
     * Reset transaction filters.
     */

    const searchInput =
        document.getElementById(
            "transactionSearch"
        );

    if (searchInput) {

        searchInput.value = "";
    }

    const typeFilter =
        document.getElementById(
            "transactionTypeFilter"
        );

    if (typeFilter) {

        typeFilter.value = "";
    }

    const categoryFilter =
        document.getElementById(
            "categoryFilter"
        );

    if (categoryFilter) {

        categoryFilter.value = "";
    }

    const startDate =
        document.getElementById(
            "startDate"
        );

    if (startDate) {

        startDate.value = "";
    }

    const endDate =
        document.getElementById(
            "endDate"
        );

    if (endDate) {

        endDate.value = "";
    }

    setDashboardLoading();

    try {

        const data =
            await apiRequest(
                "/statements"
            );

        const statements =
            Array.isArray(data?.statements)
                ? data.statements
                : Array.isArray(data)
                    ? data
                    : [];

        const selected =
            statements.find(
                statement =>
                    Number(
                        statement.statement_id
                    ) === id
            );

        if (selected) {

            setCurrentStatement(
                selected
            );
        }

        await loadDashboardData();

    }
    catch (error) {

        console.error(
            "Statement selection error:",
            error
        );

        showError(
            error.message ||
            "Unable to load selected statement."
        );
    }
}


/* ============================================================
   DELETE SELECTED STATEMENT
============================================================ */

window.deleteSelectedStatement =
    async function deleteSelectedStatement() {

        if (currentStatementId === null) {

            alert(
                "Please select a statement first."
            );

            return;
        }

        const confirmed =
            confirm(
                "Are you sure you want to delete this statement?"
            );

        if (!confirmed) {
            return;
        }

        try {

            await apiRequest(
                `/statements/${currentStatementId}`,
                {
                    method: "DELETE"
                }
            );

            alert(
                "Statement deleted successfully."
            );

            currentStatementId = null;

            allTransactions = [];

            resetDashboard();

            await loadStatements();

            const select =
                document.getElementById(
                    "statementSelect"
                );

            if (
                select &&
                select.value
            ) {

                await selectStatement(
                    Number(select.value)
                );
            }

        }
        catch (error) {

            console.error(
                "Delete statement error:",
                error
            );

            showError(
                error.message ||
                "Unable to delete statement."
            );
        }
    };


/* ============================================================
   DASHBOARD LOADING STATE
============================================================ */

function setDashboardLoading() {

    const ids = [

        "totalIncome",
        "totalExpense",
        "currentBalance",
        "highestExpense"

    ];

    ids.forEach(
        id => {

            const element =
                document.getElementById(id);

            if (element) {

                element.innerText =
                    "Loading...";
            }
        }
    );

    const transactionCount =
        document.getElementById(
            "transactionCount"
        );

    if (transactionCount) {

        transactionCount.innerText =
            "Loading...";
    }
}


/* ============================================================
   SUMMARY
============================================================ */

async function loadSummary() {

    let totalCredit = 0;
    let totalDebit = 0;

    allTransactions.forEach(transaction => {

        const amount =
            getTransactionAmount(transaction);

        const type =
            getTransactionType(transaction);

        if (type === "CREDIT") {
            totalCredit += amount;
        }

        if (type === "DEBIT") {
            totalDebit += amount;
        }

    });

    document.getElementById(
        "totalTransactions"
    ).innerText =
        allTransactions.length;

    document.getElementById(
        "totalCredit"
    ).innerText =
        formatMoney(totalCredit);

    document.getElementById(
        "totalDebit"
    ).innerText =
        formatMoney(totalDebit);
}


/* ============================================================
   BALANCE
============================================================ */

async function loadBalance() {

    let balance = 0;

    allTransactions.forEach(transaction => {

        const amount =
            getTransactionAmount(transaction);

        const type =
            getTransactionType(transaction);

        if (type === "CREDIT") {
            balance += amount;
        }

        if (type === "DEBIT") {
            balance -= amount;
        }

    });

    const balanceElement =
        document.getElementById("balance");

    if (balanceElement) {
        balanceElement.innerText =
            formatMoney(balance);
    }

    console.log(
        "Current balance:",
        balance
    );
}


/* ============================================================
   HIGHEST EXPENSE
============================================================ */

async function loadHighestExpense() {

    try {

        const expenses = allTransactions.filter(
            transaction =>
                getTransactionType(transaction) === "DEBIT"
        );

        const element =
            document.getElementById("highestExpense");

        if (!expenses.length) {

            if (element) {
                element.innerText = "No expense found.";
            }

            return;
        }

        let highestExpense = expenses[0];

        expenses.forEach(transaction => {

            const currentAmount =
                getTransactionAmount(transaction);

            const highestAmount =
                getTransactionAmount(highestExpense);

            if (currentAmount > highestAmount) {
                highestExpense = transaction;
            }

        });

        const amount =
            getTransactionAmount(highestExpense);

        const description =
            highestExpense.description ||
            highestExpense.narration ||
            highestExpense.details ||
            "N/A";

        const category =
            highestExpense.category ||
            "Other";

        const date =
            highestExpense.transaction_date ||
            highestExpense.date ||
            "N/A";

        if (element) {

            element.innerHTML = `
                <div class="highest-amount">
                    ${formatMoney(amount)}
                </div>

                <div>
                    <strong>Description:</strong>
                    ${escapeHtml(description)}
                </div>

                <div>
                    <strong>Category:</strong>
                    ${escapeHtml(category)}
                </div>

                <div>
                    <strong>Date:</strong>
                    ${escapeHtml(date)}
                </div>
            `;
        }

        console.log(
            "Highest expense:",
            highestExpense
        );

    } catch (error) {

        console.error(
            "Highest expense error:",
            error
        );

        const element =
            document.getElementById("highestExpense");

        if (element) {
            element.innerText =
                "Unable to calculate highest expense.";
        }
    }
}


/* ============================================================
   CATEGORY SUMMARY
============================================================ */

async function loadCategorySummary() {
    try {
        const categoryTotals = {};

        allTransactions.forEach(transaction => {
            const type = getTransactionType(transaction);
            const amount = getTransactionAmount(transaction);

            if (type !== "DEBIT") return;

            const category =
                transaction.category ||
                "Other";

            if (!categoryTotals[category]) {
                categoryTotals[category] = 0;
            }

            categoryTotals[category] += amount;
        });

        const element =
            document.getElementById("categorySummary");

        if (!element) return;

        const categories =
            Object.entries(categoryTotals)
                .sort((a, b) => b[1] - a[1]);

        if (!categories.length) {
            element.innerHTML =
                "<p>No expense data available.</p>";
            return;
        }

        element.innerHTML = categories
            .map(([category, amount]) => `
                <div class="category-row">
                    <span>${escapeHtml(category)}</span>
                    <strong>${formatMoney(amount)}</strong>
                </div>
            `)
            .join("");

        console.log(
            "Category summary:",
            categoryTotals
        );

    } catch (error) {
        console.error(
            "Category summary error:",
            error
        );

        const element =
            document.getElementById("categorySummary");

        if (element) {
            element.innerText =
                "Unable to calculate category summary.";
        }
    }
}


/* ============================================================
   CATEGORY ANALYSIS
============================================================ */

async function loadCategoryAnalysis() {

    const data =
        await apiRequest(
            apiUrl("/category-analysis")
        );

    console.log(
        "Category analysis loaded:",
        data
    );
}


/* ============================================================
   TRANSACTIONS
============================================================ */

async function loadTransactions() {

    const data =
        await apiRequest(
            apiUrl("/transactions")
        );

    let transactions = [];

    if (Array.isArray(data)) {

        transactions = data;

    }
    else if (
        Array.isArray(
            data?.transactions
        )
    ) {

        transactions =
            data.transactions;

    }
    else if (
        Array.isArray(
            data?.data
        )
    ) {

        transactions =
            data.data;
    }

    allTransactions =
        transactions;

    renderTransactions(
        allTransactions
    );

    updateTransactionCount(
        allTransactions.length
    );

    populateCategoryFilter(
        allTransactions
    );

    return allTransactions;
}


/* ============================================================
   TRANSACTION COUNT
============================================================ */

function updateTransactionCount(
    count
) {

    const element =
        document.getElementById(
            "transactionCount"
        );

    if (!element) {
        return;
    }

    const number =
        Number(count);

    if (!Number.isFinite(number)) {

        element.innerText =
            "0 transactions";

        return;
    }

    element.innerText =
        `${number} transaction${
            number === 1
                ? ""
                : "s"
        }`;
}


/* ============================================================
   EXPORT TRANSACTIONS
============================================================ */

window.exportTransactions =
    async function exportTransactions() {

        if (currentStatementId === null) {

            showError(
                "Please select a statement first."
            );

            return;
        }

        try {

            const token =
                localStorage.getItem(
                    "access_token"
                );

            const response =
                await fetch(
                    `${API}/export-transactions?statement_id=${encodeURIComponent(
                        currentStatementId
                    )}`,
                    {
                        method: "GET",

                        headers: token
                            ? {
                                Authorization:
                                    `Bearer ${token}`
                            }
                            : {}
                    }
                );

            if (!response.ok) {

                let message =
                    "Export failed.";

                try {

                    const errorData =
                        await response.json();

                    message =
                        errorData?.detail ||
                        errorData?.message ||
                        message;

                }
                catch {

                    /* Ignore JSON parse error */
                }

                throw new Error(message);
            }

            const blob =
                await response.blob();

            const url =
                window.URL.createObjectURL(
                    blob
                );

            const link =
                document.createElement(
                    "a"
                );

            link.href = url;

            link.download =
                `transactions_statement_${currentStatementId}.csv`;

            document.body.appendChild(
                link
            );

            link.click();

            link.remove();

            window.URL.revokeObjectURL(
                url
            );

        }
        catch (error) {

            console.error(
                "Export error:",
                error
            );

            showError(
                error.message ||
                "Unable to export transactions."
            );
        }
    };


/* ============================================================
   POPULATE CATEGORY FILTER
============================================================ */

function populateCategoryFilter(
    transactions
) {

    const select =
        document.getElementById(
            "categoryFilter"
        );

    if (!select) {
        return;
    }

    const currentValue =
        select.value;

    const categories =
        [
            ...new Set(
                (transactions || [])
                    .map(
                        transaction =>
                            getTransactionCategory(
                                transaction
                            )
                    )
                    .filter(Boolean)
            )
        ]
        .sort(
            (a, b) =>
                a.localeCompare(b)
        );

    select.innerHTML = `
        <option value="">
            All Categories
        </option>
    `;

    categories.forEach(
        category => {

            const option =
                document.createElement(
                    "option"
                );

            option.value =
                category;

            option.textContent =
                category;

            select.appendChild(
                option
            );
        }
    );

    if (
        categories.includes(
            currentValue
        )
    ) {

        select.value =
            currentValue;
    }
}


/* ============================================================
   APPLY TRANSACTION FILTERS
============================================================ */

function applyTransactionFilters() {

    let filtered =
        [...allTransactions];

    const searchElement =
        document.getElementById(
            "transactionSearch"
        );

    const typeElement =
        document.getElementById(
            "transactionTypeFilter"
        );

    const categoryElement =
        document.getElementById(
            "categoryFilter"
        );

    const startElement =
        document.getElementById(
            "startDate"
        );

    const endElement =
        document.getElementById(
            "endDate"
        );

    const search =
        searchElement
            ? searchElement.value
                .trim()
                .toLowerCase()
            : "";

    const type =
        typeElement
            ? typeElement.value
                .trim()
                .toUpperCase()
            : "";

    const category =
        categoryElement
            ? categoryElement.value
                .trim()
                .toLowerCase()
            : "";

    const startDate =
        startElement
            ? startElement.value
            : "";

    const endDate =
        endElement
            ? endElement.value
            : "";

    if (search) {

        filtered =
            filtered.filter(
                transaction => {

                    const description =
                        getTransactionDescription(
                            transaction
                        ).toLowerCase();

                    const transactionCategory =
                        getTransactionCategory(
                            transaction
                        ).toLowerCase();

                    return (
                        description.includes(
                            search
                        ) ||
                        transactionCategory.includes(
                            search
                        )
                    );
                }
            );
    }

    if (type && type !== "ALL") {

    filtered =
        filtered.filter(
            transaction =>
                getTransactionType(
                    transaction
                ) === type
        );
}

    if (category) {

        filtered =
            filtered.filter(
                transaction =>
                    getTransactionCategory(
                        transaction
                    )
                        .toLowerCase() ===
                    category
            );
    }

    if (startDate) {

        filtered =
            filtered.filter(
                transaction => {

                    const date =
                        parseTransactionDate(
                            getTransactionDate(
                                transaction
                            )
                        );

                    const start =
                        parseTransactionDate(
                            startDate
                        );

                    if (!date || !start) {
                        return false;
                    }

                    return date >= start;
                }
            );
    }

    if (endDate) {

        filtered =
            filtered.filter(
                transaction => {

                    const date =
                        parseTransactionDate(
                            getTransactionDate(
                                transaction
                            )
                        );

                    const end =
                        parseTransactionDate(
                            endDate
                        );

                    if (!date || !end) {
                        return false;
                    }

                    return date <= end;
                }
            );
    }

    renderTransactions(
        filtered
    );

    updateTransactionCount(
        filtered.length
    );

    updateFilterSummary(
        filtered.length
    );
}


/* ============================================================
   FILTER SUMMARY
============================================================ */

function updateFilterSummary(
    count
) {

    const element =
        document.getElementById(
            "filterSummary"
        );

    if (!element) {
        return;
    }

    if (
        count === allTransactions.length
    ) {

        element.innerText = "";

        return;
    }

    element.innerText =
        `Showing ${count} of ${allTransactions.length} transactions`;
}


/* ============================================================
   CLEAR FILTERS
============================================================ */

function clearTransactionFilters() {

    const ids = [

        "transactionSearch",
        "transactionTypeFilter",
        "categoryFilter",
        "startDate",
        "endDate"

    ];

    ids.forEach(
        id => {

            const element =
                document.getElementById(id);

            if (element) {

                element.value = "";
            }
        }
    );

    renderTransactions(
        allTransactions
    );

    updateTransactionCount(
        allTransactions.length
    );

    updateFilterSummary(
        allTransactions.length
    );
}


/* ============================================================
   DATE COMPARISON
============================================================ */

function compareDates(
    dateA,
    dateB
) {

    const a =
        parseTransactionDate(
            dateA
        );

    const b =
        parseTransactionDate(
            dateB
        );

    if (!a || !b) {
        return 0;
    }

    if (a < b) {
        return -1;
    }

    if (a > b) {
        return 1;
    }

    return 0;
}


/* ============================================================
   RENDER TRANSACTIONS
============================================================ */

function renderTransactions(
    transactions
) {

    const table =
        document.getElementById(
            "transactionTable"
        );

    if (!table) {
        return;
    }

    if (
        !Array.isArray(transactions) ||
        !transactions.length
    ) {

        table.innerHTML = `
            <tr>
                <td colspan="5">
                    No transactions found.
                </td>
            </tr>
        `;

        return;
    }

    table.innerHTML = "";

    transactions.forEach(
        transaction => {

            const row =
                document.createElement(
                    "tr"
                );

            const type =
                getTransactionType(
                    transaction
                );

            const typeClass =
                type === "CREDIT"
                    ? "credit"
                    : "debit";

            const sign =
                type === "CREDIT"
                    ? "+"
                    : "-";

            row.innerHTML = `

                <td>
                    ${escapeHtml(
                        getTransactionDate(
                            transaction
                        )
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        getTransactionDescription(
                            transaction
                        )
                    )}
                </td>

                <td class="${typeClass}">
                    ${sign}
                    ${formatMoney(
                        getTransactionAmount(
                            transaction
                        )
                    )}
                </td>

                <td class="${typeClass}">
                    ${escapeHtml(
                        type || "UNKNOWN"
                    )}
                </td>

                <td>
                    ${escapeHtml(
                        getTransactionCategory(
                            transaction
                        )
                    )}
                </td>

            `;

            table.appendChild(
                row
            );
        }
    );
}


/* ============================================================
   INSIGHTS
============================================================ */

async function loadInsights() {

    try {

        const data =
            await apiRequest(
                apiUrl("/insights")
            );

        const element =
            document.getElementById(
                "insights"
            );

        if (!element) {
            return;
        }

        element.innerHTML = `

            <div class="insight-item">

                💰 Total income:

                <strong>
                    ${formatMoney(
                        data?.income
                    )}
                </strong>

            </div>

            <div class="insight-item">

                💸 Total expenses:

                <strong>
                    ${formatMoney(
                        data?.expense
                    )}
                </strong>

            </div>

            <div class="insight-item">

                📊 Expense ratio:

                <strong>
                    ${
                        safeNumber(
                            data?.expense_percentage
                        ).toFixed(2)
                    }%
                </strong>

            </div>

            <div class="insight-item">

                🏷️ Highest spending category:

                <strong>
                    ${escapeHtml(
                        data?.highest_category ||
                        "Other"
                    )}
                </strong>

                —

                ${formatMoney(
                    data?.highest_category_amount
                )}

            </div>

            <div class="insight-item">

                🔎 Largest expense:

                <strong>
                    ${escapeHtml(
                        data?.highest_expense ||
                        "N/A"
                    )}
                </strong>

                —

                ${formatMoney(
                    data?.highest_expense_amount
                )}

            </div>

            <div class="insight-item">

                💵 Current balance:

                <strong>
                    ${formatMoney(
                        data?.balance
                    )}
                </strong>

            </div>

        `;

    }
    catch (error) {

        console.error(
            "Insights error:",
            error
        );

        calculateLocalInsights();
    }
}


/* ============================================================
   LOCAL INSIGHTS FALLBACK
============================================================ */

function calculateLocalInsights() {

    let income = 0;

    let expense = 0;

    const categories = {};

    allTransactions.forEach(
        transaction => {

            const amount =
                getTransactionAmount(
                    transaction
                );

            const type =
                getTransactionType(
                    transaction
                );

            if (type === "CREDIT") {

                income += amount;
            }

            if (type === "DEBIT") {

                expense += amount;

                const category =
                    getTransactionCategory(
                        transaction
                    );

                categories[category] =
                    (
                        categories[category] ||
                        0
                    ) +
                    amount;
            }
        }
    );

    const categoryEntries =
        Object.entries(
            categories
        )
        .sort(
            (a, b) =>
                b[1] - a[1]
        );

    const highestCategory =
        categoryEntries[0];

    const expenses =
        allTransactions.filter(
            transaction =>
                getTransactionType(
                    transaction
                ) === "DEBIT"
        );

    const highestExpense =
        expenses.length
            ? expenses.reduce(
                (max, current) =>
                    getTransactionAmount(
                        current
                    ) >
                    getTransactionAmount(
                        max
                    )
                        ? current
                        : max
            )
            : null;

    const balance =
        income - expense;

    const expensePercentage =
        income > 0
            ? (
                expense /
                income *
                100
            )
            : 0;

    const element =
        document.getElementById(
            "insights"
        );

    if (!element) {
        return;
    }

    element.innerHTML = `

        <div class="insight-item">

            💰 Total income:

            <strong>
                ${formatMoney(income)}
            </strong>

        </div>

        <div class="insight-item">

            💸 Total expenses:

            <strong>
                ${formatMoney(expense)}
            </strong>

        </div>

        <div class="insight-item">

            📊 Expense ratio:

            <strong>
                ${expensePercentage.toFixed(2)}%
            </strong>

        </div>

        <div class="insight-item">

            🏷️ Highest spending category:

            <strong>
                ${escapeHtml(
                    highestCategory?.[0] ||
                    "Other"
                )}
            </strong>

            —

            ${formatMoney(
                highestCategory?.[1] || 0
            )}

        </div>

        <div class="insight-item">

            🔎 Largest expense:

            <strong>
                ${escapeHtml(
                    highestExpense
                        ? getTransactionDescription(
                            highestExpense
                        )
                        : "N/A"
                )}
            </strong>

            —

            ${formatMoney(
                highestExpense
                    ? getTransactionAmount(
                        highestExpense
                    )
                    : 0
            )}

        </div>

        <div class="insight-item">

            💵 Current balance:

            <strong>
                ${formatMoney(balance)}
            </strong>

        </div>

    `;
}


/* ============================================================
   ANALYTICS
============================================================ */

async function loadAnalytics() {

    try {

        /*
         * Calculate analytics directly from the
         * transactions already loaded on the dashboard.
         */

        calculateLocalAnalytics();

        console.log(
            "Analytics loaded successfully from transactions."
        );

    }
    catch (error) {

        console.error(
            "Analytics error:",
            error
        );

        const healthElement =
            document.getElementById("healthScore");

        const savingsRateElement =
            document.getElementById("savingsRate");

        const savingsElement =
            document.getElementById("totalSavings");

        const topCategoryElement =
            document.getElementById("topCategory");

        const spendingStatusElement =
            document.getElementById("spendingStatus");

        const analyticsCategoryElement =
            document.getElementById("analyticsCategory");

        const averageTransactionElement =
            document.getElementById("averageTransaction");

        const recommendationElement =
            document.getElementById("recommendation");

        if (healthElement) {
            healthElement.innerText = "0/100";
        }

        if (savingsRateElement) {
            savingsRateElement.innerText = "0.00%";
        }

        if (savingsElement) {
            savingsElement.innerText = formatMoney(0);
        }

        if (topCategoryElement) {
            topCategoryElement.innerText = "N/A";
        }

        if (spendingStatusElement) {
            spendingStatusElement.innerText =
                "Unable to calculate spending status.";
        }

        if (analyticsCategoryElement) {
            analyticsCategoryElement.innerText = "N/A";
        }

        if (averageTransactionElement) {
            averageTransactionElement.innerText =
                formatMoney(0);
        }

        if (recommendationElement) {
            recommendationElement.innerText =
                "Unable to generate recommendation.";
        }
    }
}


/* ============================================================
   LOCAL ANALYTICS FALLBACK
============================================================ */

function calculateLocalAnalytics() {

    let income = 0;

    let expense = 0;

    const categories = {};

    allTransactions.forEach(
        transaction => {

            const amount =
                getTransactionAmount(
                    transaction
                );

            const type =
                getTransactionType(
                    transaction
                );

            if (type === "CREDIT") {

                income += amount;
            }

            if (type === "DEBIT") {

                expense += amount;

                const category =
                    getTransactionCategory(
                        transaction
                    );

                categories[category] =
                    (
                        categories[category] ||
                        0
                    ) +
                    amount;
            }
        }
    );

    const savings =
        income - expense;

    const savingsRate =
        income > 0
            ? (
                savings /
                income *
                100
            )
            : 0;

    const categoryEntries =
        Object.entries(
            categories
        )
        .sort(
            (a, b) =>
                b[1] - a[1]
        );

    const topCategory =
        categoryEntries[0];

    const averageTransaction =
        allTransactions.length > 0
            ? (
                income +
                expense
            ) /
            allTransactions.length
            : 0;

    let healthScore = 50;

    if (savingsRate >= 20) {

        healthScore += 30;

    }
    else if (savingsRate >= 10) {

        healthScore += 20;

    }
    else if (savingsRate >= 0) {

        healthScore += 10;

    }
    else {

        healthScore -= 20;
    }

    if (income > expense) {

        healthScore += 10;

    }
    else {

        healthScore -= 10;
    }

    healthScore =
        Math.max(
            0,
            Math.min(
                100,
                healthScore
            )
        );

    let spendingStatus;

    if (income <= 0) {

        spendingStatus =
            "No income data available.";

    }
    else if (expense > income) {

        spendingStatus =
            "Your expenses are higher than your income.";

    }
    else if (savingsRate < 10) {

        spendingStatus =
            "Your savings rate is relatively low.";

    }
    else if (savingsRate < 20) {

        spendingStatus =
            "Your spending is manageable, but savings could improve.";

    }
    else {

        spendingStatus =
            "Your spending is healthy and you are maintaining good savings.";
    }

    let recommendation;

    if (expense > income) {

        recommendation =
            "Reduce unnecessary expenses and focus on increasing your savings.";

    }
    else if (savingsRate < 10) {

        recommendation =
            "Try to save at least 10% of your monthly income.";

    }
    else if (savingsRate < 20) {

        recommendation =
            "Consider increasing your savings rate toward 20%.";

    }
    else {

        recommendation =
            "Keep maintaining your current saving habits.";
    }

    const healthElement =
        document.getElementById(
            "healthScore"
        );

    const savingsRateElement =
        document.getElementById(
            "savingsRate"
        );

    const savingsElement =
        document.getElementById(
            "totalSavings"
        );

    const topCategoryElement =
        document.getElementById(
            "topCategory"
        );

    const spendingStatusElement =
        document.getElementById(
            "spendingStatus"
        );

    const analyticsCategoryElement =
        document.getElementById(
            "analyticsCategory"
        );

    const averageTransactionElement =
        document.getElementById(
            "averageTransaction"
        );

    const recommendationElement =
        document.getElementById(
            "recommendation"
        );

    if (healthElement) {

        healthElement.innerText =
            `${healthScore}/100`;
    }

    if (savingsRateElement) {

        savingsRateElement.innerText =
            `${savingsRate.toFixed(2)}%`;
    }

    if (savingsElement) {

        savingsElement.innerText =
            formatMoney(savings);
    }

    if (topCategoryElement) {

        topCategoryElement.innerText =
            topCategory?.[0] ||
            "N/A";
    }

    if (spendingStatusElement) {

        spendingStatusElement.innerText =
            spendingStatus;
    }

    if (analyticsCategoryElement) {

        analyticsCategoryElement.innerText =
            `${topCategory?.[0] || "N/A"} — ${
                formatMoney(
                    topCategory?.[1] || 0
                )
            }`;
    }

    if (averageTransactionElement) {

        averageTransactionElement.innerText =
            formatMoney(
                averageTransaction
            );
    }

    if (recommendationElement) {

        recommendationElement.innerText =
            recommendation;
    }
}


/* ============================================================
   CHART DEFAULTS
============================================================ */

function chartDefaults() {

    if (
        typeof Chart === "undefined"
    ) {

        return;
    }

    Chart.defaults.font.family =
        "Arial, Helvetica, sans-serif";

    Chart.defaults.font.size =
        13;

    Chart.defaults.color =
        "#555";
}


/* ============================================================
   EMPTY CHART HANDLING
============================================================ */

function showEmptyChart(
    canvas,
    message = "No data available"
) {

    if (
        !canvas ||
        !canvas.parentElement
    ) {

        return;
    }

    const container =
        canvas.parentElement;

    canvas.style.display =
        "none";

    const old =
        container.querySelector(
            ".empty-chart"
        );

    if (old) {

        old.remove();
    }

    const div =
        document.createElement(
            "div"
        );

    div.className =
        "empty-chart";

    div.innerText =
        message;

    container.appendChild(
        div
    );
}


function prepareCanvas(
    canvas
) {

    if (!canvas) {
        return;
    }

    canvas.style.display =
        "block";

    if (!canvas.parentElement) {
        return;
    }

    const empty =
        canvas.parentElement.querySelector(
            ".empty-chart"
        );

    if (empty) {

        empty.remove();
    }
}


/* ============================================================
   INCOME VS EXPENSE CHART
============================================================ */

function createIncomeExpenseChart() {

    const canvas =
        document.getElementById(
            "incomeExpenseChart"
        );

    if (!canvas) {
        return;
    }

    prepareCanvas(canvas);

    if (incomeExpenseChart) {

        incomeExpenseChart.destroy();
    }

    let income = 0;

    let expense = 0;

    allTransactions.forEach(
        transaction => {

            const amount =
                getTransactionAmount(
                    transaction
                );

            const type =
                getTransactionType(
                    transaction
                );

            if (type === "CREDIT") {

                income += amount;
            }

            if (type === "DEBIT") {

                expense += amount;
            }
        }
    );

    if (
        income === 0 &&
        expense === 0
    ) {

        showEmptyChart(
            canvas,
            "No income or expense data"
        );

        return;
    }

    incomeExpenseChart =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {

                    labels: [
                        "Income",
                        "Expenses"
                    ],

                    datasets: [
                        {
                            label: "Amount",

                            data: [
                                income,
                                expense
                            ],

                            borderWidth: 1,

                            borderRadius: 8
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {
                            display: false
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    context =>
                                        formatMoney(
                                            context.raw
                                        )
                            }
                        }
                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                callback:
                                    value =>
                                        "₹ " +
                                        Number(
                                            value
                                        ).toLocaleString(
                                            "en-IN"
                                        )
                            }
                        }
                    }
                }
            }
        );
}


/* ============================================================
   CATEGORY CHART
============================================================ */

function createCategoryChart() {

    const canvas =
        document.getElementById(
            "categoryChart"
        );

    if (!canvas) {
        return;
    }

    prepareCanvas(canvas);

    if (categoryChart) {

        categoryChart.destroy();
    }

    const totals = {};

    allTransactions.forEach(
        transaction => {

            if (
                getTransactionType(
                    transaction
                ) !== "DEBIT"
            ) {

                return;
            }

            const category =
                getTransactionCategory(
                    transaction
                );

            const amount =
                getTransactionAmount(
                    transaction
                );

            totals[category] =
                (
                    totals[category] ||
                    0
                ) +
                amount;
        }
    );

    const entries =
        Object.entries(
            totals
        )
        .sort(
            (a, b) =>
                b[1] - a[1]
        );

    if (!entries.length) {

        showEmptyChart(
            canvas,
            "No spending category data"
        );

        return;
    }

    categoryChart =
        new Chart(
            canvas,
            {
                type: "doughnut",

                data: {

                    labels:
                        entries.map(
                            item =>
                                item[0]
                        ),

                    datasets: [
                        {
                            data:
                                entries.map(
                                    item =>
                                        item[1]
                                ),

                            borderWidth: 2
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    cutout: "60%",

                    plugins: {

                        legend: {

                            position: "right"
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    context => {

                                        const total =
                                            context
                                                .dataset
                                                .data
                                                .reduce(
                                                    (
                                                        a,
                                                        b
                                                    ) =>
                                                        a +
                                                        b,
                                                    0
                                                );

                                        const percentage =
                                            total > 0
                                                ? (
                                                    context.raw /
                                                    total *
                                                    100
                                                ).toFixed(
                                                    1
                                                )
                                                : 0;

                                        return `${formatMoney(
                                            context.raw
                                        )} (${percentage}%)`;
                                    }
                            }
                        }
                    }
                }
            }
        );
}


/* ============================================================
   MONTHLY FINANCIAL DATA
============================================================ */

function getMonthlyFinancialData() {

    const monthly = {};

    allTransactions.forEach(
        transaction => {

            const date =
                getTransactionDate(
                    transaction
                );

            if (!date) {
                return;
            }

            const parsedDate =
                parseTransactionDate(
                    date
                );

            if (!parsedDate) {
                return;
            }

            const monthKey =
                `${parsedDate.getFullYear()}-${String(
                    parsedDate.getMonth() + 1
                ).padStart(2, "0")}`;

            if (!monthly[monthKey]) {

                monthly[monthKey] = {

                    income: 0,

                    expense: 0
                };
            }

            const amount =
                getTransactionAmount(
                    transaction
                );

            const type =
                getTransactionType(
                    transaction
                );

            if (type === "CREDIT") {

                monthly[monthKey].income +=
                    amount;
            }

            if (type === "DEBIT") {

                monthly[monthKey].expense +=
                    amount;
            }
        }
    );

    return Object.entries(
        monthly
    )
    .sort(
        (a, b) =>
            a[0].localeCompare(
                b[0]
            )
    )
    .map(
        ([month, values]) => ({

            month,

            income:
                values.income,

            expense:
                values.expense,

            savings:
                values.income -
                values.expense
        })
    );
}


/* ============================================================
   PARSE TRANSACTION DATE
============================================================ */

function parseTransactionDate(
    value
) {

    if (!value) {
        return null;
    }

    const text =
        String(value).trim();

    /*
     * DD-MM-YYYY or DD/MM/YYYY
     */

    const ddmmyyyy =
        text.match(
            /^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/
        );

    if (ddmmyyyy) {

        const day =
            Number(
                ddmmyyyy[1]
            );

        const month =
            Number(
                ddmmyyyy[2]
            ) - 1;

        const year =
            Number(
                ddmmyyyy[3]
            );

        const parsed =
            new Date(
                year,
                month,
                day
            );

        if (
            parsed.getFullYear() === year &&
            parsed.getMonth() === month &&
            parsed.getDate() === day
        ) {

            return parsed;
        }
    }

    /*
     * YYYY-MM-DD
     */

    const yyyymmdd =
        text.match(
            /^(\d{4})-(\d{1,2})-(\d{1,2})$/
        );

    if (yyyymmdd) {

        const year =
            Number(
                yyyymmdd[1]
            );

        const month =
            Number(
                yyyymmdd[2]
            ) - 1;

        const day =
            Number(
                yyyymmdd[3]
            );

        const parsed =
            new Date(
                year,
                month,
                day
            );

        if (
            parsed.getFullYear() === year &&
            parsed.getMonth() === month &&
            parsed.getDate() === day
        ) {

            return parsed;
        }
    }

    /*
     * ISO / browser-supported date
     */

    const date =
        new Date(text);

    if (
        !Number.isNaN(
            date.getTime()
        )
    ) {

        return date;
    }

    return null;
}


/* ============================================================
   MONTHLY FINANCIAL CHART
============================================================ */

function createMonthlyFinancialChart() {

    const canvas =
        document.getElementById(
            "monthlyFinancialChart"
        );

    if (!canvas) {
        return;
    }

    prepareCanvas(canvas);

    if (monthlyFinancialChart) {

        monthlyFinancialChart.destroy();
    }

    const data =
        getMonthlyFinancialData();

    if (!data.length) {

        showEmptyChart(
            canvas,
            "No monthly financial data"
        );

        return;
    }

    const labels =
        data.map(
            item => {

                const parts =
                    item.month.split("-");

                const date =
                    new Date(
                        Number(parts[0]),
                        Number(parts[1]) - 1,
                        1
                    );

                return date.toLocaleDateString(
                    "en-IN",
                    {
                        month: "short",
                        year: "numeric"
                    }
                );
            }
        );

    monthlyFinancialChart =
        new Chart(
            canvas,
            {
                data: {

                    labels: labels,

                    datasets: [

                        {
                            type: "bar",

                            label: "Income",

                            data:
                                data.map(
                                    item =>
                                        item.income
                                ),

                            borderWidth: 1
                        },

                        {
                            type: "bar",

                            label: "Expenses",

                            data:
                                data.map(
                                    item =>
                                        item.expense
                                ),

                            borderWidth: 1
                        },

                        {
                            type: "line",

                            label: "Savings",

                            data:
                                data.map(
                                    item =>
                                        item.savings
                                ),

                            borderWidth: 2,

                            tension: 0.3,

                            fill: false
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    interaction: {

                        mode: "index",

                        intersect: false
                    },

                    plugins: {

                        tooltip: {

                            callbacks: {

                                label:
                                    context =>
                                        `${context.dataset.label}: ${
                                            formatMoney(
                                                context.raw
                                            )
                                        }`
                            }
                        }
                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                callback:
                                    value =>
                                        "₹ " +
                                        Number(
                                            value
                                        ).toLocaleString(
                                            "en-IN"
                                        )
                            }
                        }
                    }
                }
            }
        );
}


/* ============================================================
   SAVINGS CHART
============================================================ */

function createSavingsChart() {

    const canvas =
        document.getElementById(
            "savingsChart"
        );

    if (!canvas) {
        return;
    }

    prepareCanvas(canvas);

    if (savingsChart) {

        savingsChart.destroy();
    }

    const data =
        getMonthlyFinancialData();

    if (!data.length) {

        showEmptyChart(
            canvas,
            "No savings data"
        );

        return;
    }

    savingsChart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {

                    labels:
                        data.map(
                            item =>
                                item.month
                        ),

                    datasets: [
                        {

                            label:
                                "Savings",

                            data:
                                data.map(
                                    item =>
                                        item.savings
                                ),

                            borderWidth: 2,

                            tension: 0.3,

                            fill: false
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        tooltip: {

                            callbacks: {

                                label:
                                    context =>
                                        formatMoney(
                                            context.raw
                                        )
                            }
                        }
                    },

                    scales: {

                        y: {

                            ticks: {

                                callback:
                                    value =>
                                        "₹ " +
                                        Number(
                                            value
                                        ).toLocaleString(
                                            "en-IN"
                                        )
                            }
                        }
                    }
                }
            }
        );
}


/* ============================================================
   TOP CATEGORY CHART
============================================================ */

function createTopCategoryChart() {

    const canvas =
        document.getElementById(
            "topCategoryChart"
        );

    if (!canvas) {
        return;
    }

    prepareCanvas(canvas);

    if (topCategoryChart) {

        topCategoryChart.destroy();
    }

    const totals = {};

    allTransactions.forEach(
        transaction => {

            if (
                getTransactionType(
                    transaction
                ) !== "DEBIT"
            ) {

                return;
            }

            const category =
                getTransactionCategory(
                    transaction
                );

            totals[category] =
                (
                    totals[category] ||
                    0
                ) +
                getTransactionAmount(
                    transaction
                );
        }
    );

    const entries =
        Object.entries(
            totals
        )
        .sort(
            (a, b) =>
                b[1] - a[1]
        )
        .slice(
            0,
            10
        );

    if (!entries.length) {

        showEmptyChart(
            canvas,
            "No category spending data"
        );

        return;
    }

    topCategoryChart =
        new Chart(
            canvas,
            {
                type: "bar",

                data: {

                    labels:
                        entries.map(
                            item =>
                                item[0]
                        ),

                    datasets: [
                        {

                            label:
                                "Spending",

                            data:
                                entries.map(
                                    item =>
                                        item[1]
                                ),

                            borderWidth: 1
                        }
                    ]
                },

                options: {

                    indexAxis: "y",

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        legend: {
                            display: false
                        },

                        tooltip: {

                            callbacks: {

                                label:
                                    context =>
                                        formatMoney(
                                            context.raw
                                        )
                            }
                        }
                    },

                    scales: {

                        x: {

                            beginAtZero: true,

                            ticks: {

                                callback:
                                    value =>
                                        "₹ " +
                                        Number(
                                            value
                                        ).toLocaleString(
                                            "en-IN"
                                        )
                            }
                        }
                    }
                }
            }
        );
}


/* ============================================================
   DAILY SPENDING CHART
============================================================ */

function createDailySpendingChart() {

    const canvas =
        document.getElementById(
            "dailySpendingChart"
        );

    if (!canvas) {
        return;
    }

    prepareCanvas(canvas);

    if (dailySpendingChart) {

        dailySpendingChart.destroy();
    }

    const daily = {};

    allTransactions.forEach(
        transaction => {

            if (
                getTransactionType(
                    transaction
                ) !== "DEBIT"
            ) {

                return;
            }

            const date =
                getTransactionDate(
                    transaction
                );

            if (!date) {
                return;
            }

            const parsed =
                parseTransactionDate(
                    date
                );

            if (!parsed) {
                return;
            }

            const key =
                `${parsed.getFullYear()}-${String(
                    parsed.getMonth() + 1
                ).padStart(2, "0")}-${String(
                    parsed.getDate()
                ).padStart(2, "0")}`;

            daily[key] =
                (
                    daily[key] ||
                    0
                ) +
                getTransactionAmount(
                    transaction
                );
        }
    );

    const entries =
        Object.entries(
            daily
        )
        .sort(
            (a, b) =>
                a[0].localeCompare(
                    b[0]
                )
        );

    if (!entries.length) {

        showEmptyChart(
            canvas,
            "No daily spending data"
        );

        return;
    }

    dailySpendingChart =
        new Chart(
            canvas,
            {
                type: "line",

                data: {

                    labels:
                        entries.map(
                            item =>
                                item[0]
                        ),

                    datasets: [
                        {

                            label:
                                "Daily Spending",

                            data:
                                entries.map(
                                    item =>
                                        item[1]
                                ),

                            borderWidth: 2,

                            tension: 0.25,

                            fill: false
                        }
                    ]
                },

                options: {

                    responsive: true,

                    maintainAspectRatio: false,

                    plugins: {

                        tooltip: {

                            callbacks: {

                                label:
                                    context =>
                                        formatMoney(
                                            context.raw
                                        )
                            }
                        }
                    },

                    scales: {

                        y: {

                            beginAtZero: true,

                            ticks: {

                                callback:
                                    value =>
                                        "₹ " +
                                        Number(
                                            value
                                        ).toLocaleString(
                                            "en-IN"
                                        )
                            }
                        }
                    }
                }
            }
        );
}


/* ============================================================
   LOAD ALL CHARTS
============================================================ */

function loadAllCharts() {

    chartDefaults();

    if (
        typeof Chart === "undefined"
    ) {

        console.warn(
            "Chart.js is not loaded."
        );

        return;
    }

    createIncomeExpenseChart();

    createCategoryChart();

    createMonthlyFinancialChart();

    createSavingsChart();

    createTopCategoryChart();

    createDailySpendingChart();
}


/* ============================================================
   LOAD DASHBOARD DATA
============================================================ */

async function loadDashboardData() {

    if (
        currentStatementId === null
    ) {

        resetDashboard();

        return;
    }

    try {

        /*
         * Transactions MUST load first.
         */

        await loadTransactions();

        /*
         * Other dashboard APIs.
         */

        await Promise.allSettled([

            loadSummary(),

            loadBalance(),

            loadHighestExpense(),

            loadCategorySummary(),

            loadCategoryAnalysis(),

            loadInsights(),

            loadAnalytics()

        ]);

        /*
         * Charts after transactions.
         */

        loadAllCharts();

    }
    catch (error) {

        console.error(
            "Dashboard loading error:",
            error
        );

        showError(
            "Some dashboard data could not be loaded."
        );

        loadAllCharts();
    }
}


/* ============================================================
   INITIAL DASHBOARD
============================================================ */

async function loadDashboard() {

    hideError();

    setDashboardLoading();

    try {

        /*
         * STEP 1:
         * Find latest statement.
         */

        const statementFound =
            await loadLatestStatement();

        /*
         * STEP 2:
         * Load statement history.
         */

        await loadStatements();

        /*
         * STEP 3:
         * No statement.
         */

        if (!statementFound) {

            resetDashboard();

            /*
             * Keep statement history
             * visible even when empty.
             */

            await loadStatements();

            return;
        }

        /*
         * STEP 4:
         * Load current dashboard.
         */

        await loadDashboardData();

    }
    catch (error) {

        console.error(
            "Initial dashboard error:",
            error
        );

        resetDashboard();

        showError(
            "Unable to load dashboard."
        );
    }
}


/* ============================================================
   START APPLICATION
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const loginScreen =
            document.getElementById(
                "loginScreen"
            );

        const dashboard =
            document.querySelector(
                ".container"
            );

        /*
         * Always show login screen when
         * index.html is opened.
         */

        localStorage.removeItem(
            "access_token"
        );

        if (loginScreen) {

            loginScreen.style.display =
                "flex";
        }

        if (dashboard) {

            dashboard.style.display =
                "none";
        }

        /*
         * Transaction filter listeners.
         */

        const search =
            document.getElementById(
                "transactionSearch"
            );

        if (search) {

            search.addEventListener(
                "input",
                applyTransactionFilters
            );
        }

        const typeFilter =
            document.getElementById(
                "transactionTypeFilter"
            );

        if (typeFilter) {

            typeFilter.addEventListener(
                "change",
                applyTransactionFilters
            );
        }

        const categoryFilter =
            document.getElementById(
                "categoryFilter"
            );

        if (categoryFilter) {

            categoryFilter.addEventListener(
                "change",
                applyTransactionFilters
            );
        }

        const startDate =
            document.getElementById(
                "startDate"
            );

        if (startDate) {

            startDate.addEventListener(
                "change",
                applyTransactionFilters
            );
        }

        const endDate =
            document.getElementById(
                "endDate"
            );

        if (endDate) {

            endDate.addEventListener(
                "change",
                applyTransactionFilters
            );
        }
    }
);