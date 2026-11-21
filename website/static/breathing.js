const circle = document.getElementById("breathingCircle");
const phaseText = document.getElementById("breathingPhase");
const timerText = document.getElementById("breathingTimer");

let countdownInterval;
let breathingTimeout;

function startBreathing() {
    // Clear any previous timers
    clearTimeout(breathingTimeout);
    clearInterval(countdownInterval);

    // Start ONE breathing cycle
    breathingCycle();
}

function breathingCycle() {
    // Inhale
    runPhase("Breathe In", 4, "breathe-in");

    // Hold
    setTimeout(() => {
        runPhase("Hold", 4, "breathe-hold");
    }, 4000);

    // Exhale
    setTimeout(() => {
        runPhase("Release", 6, "breathe-out");
    }, 8000);

    // Reset after full cycle (STOP)
    breathingTimeout = setTimeout(() => {
        circle.className = "breathing-circle-advanced";
        phaseText.innerText = "Done 🌿";
        timerText.innerText = "";
    }, 14000);
}

function runPhase(text, seconds, cssClass) {
    clearInterval(countdownInterval);

    phaseText.innerText = text;
    circle.className = `breathing-circle-advanced ${cssClass}`;

    let timeLeft = seconds;
    timerText.innerText = timeLeft;

    countdownInterval = setInterval(() => {
        timeLeft--;
        timerText.innerText = timeLeft;
        if (timeLeft <= 0) clearInterval(countdownInterval);
    }, 1000);
}
