function validateForm() {
    const income = parseFloat(document.getElementById("income").value);
    const expenses = parseFloat(document.getElementById("expenses").value);
    const returnRate = parseFloat(document.getElementById("return_rate").value);
    const years = parseInt(document.getElementById("years").value);
    const inflationRate = parseFloat(document.getElementById("inflation_rate").value);

    if (income <= 0) {
        alert("Monthly income must be greater than 0.");
        return false;
    }

    if (expenses < 0) {
        alert("Monthly expenses cannot be negative.");
        return false;
    }

    if (expenses > income) {
        alert("Expenses cannot be greater than income.");
        return false;
    }

    if (returnRate < 0 || returnRate > 100) {
        alert("Annual return rate must be between 0 and 100.");
        return false;
    }

    if (years <= 0 || years > 100) {
        alert("Investment duration must be between 1 and 100 years.");
        return false;
    }

    if (inflationRate < 0 || inflationRate > 50) {
        alert("Inflation rate must be between 0 and 50.");
        return false;
    }

    return true;
}