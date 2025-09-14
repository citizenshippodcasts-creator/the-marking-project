// This is the full JavaScript for the frontend.
// It handles routing, fetching data, and building the HTML for each page.

// The base URL for your backend API. Render will provide this.
// For local testing, you might use: 'http://127.0.0.1:5000'
const API_BASE_URL = ''; // This will be set automatically by Render

const contentArea = document.getElementById('content-area');
const mainTitle = document.getElementById('main-title');

// --- ROUTING ---
// Decides which page to show based on the URL
function router() {
    const path = window.location.hash.slice(1) || '/'; // Use hash for routing
    const params = path.split('/');

    if (path === '/') {
        loadHomePage();
    } else if (params[1] === 'subjects' && params.length === 3) {
        loadEssayListPage(params[2]);
    } else if (params[1] === 'essays' && params.length === 3) {
        loadMarkingToolPage(params[2]);
    } else {
        contentArea.innerHTML = '<h2>404 - Page Not Found</h2>';
    }
}

// --- PAGE LOADERS ---

// Loads the list of subjects onto the homepage
async function loadHomePage() {
    mainTitle.innerHTML = `<a href="/">TheMarkingProject</a>`;
    contentArea.innerHTML = '<div class="placeholder-box"><h2>Loading Subjects...</h2></div>';
    try {
        const response = await fetch(`${API_BASE_URL}/api/subjects`);
        if (!response.ok) throw new Error('Network response was not ok');
        const subjects = await response.json();

        let html = '<h3>Choose a subject to begin:</h3><div class="subject-list">';
        subjects.forEach(subject => {
            html += `<div onclick="navigateTo('/subjects/${subject.id}')"><h2>${subject.name}</h2></div>`;
        });
        html += '</div>';
        contentArea.innerHTML = html;
    } catch (error) {
        console.error('Failed to load subjects:', error);
        contentArea.innerHTML = '<div class="placeholder-box"><h2>Error loading subjects. Please try again later.</h2></div>';
    }
}

// Loads the list of essays for a given subject
async function loadEssayListPage(subjectId) {
    contentArea.innerHTML = '<div class="placeholder-box"><h2>Loading Essays...</h2></div>';
    try {
        const response = await fetch(`${API_BASE_URL}/api/essays/subject/${subjectId}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        
        mainTitle.innerHTML = `<a href="/">${data.subject_name} Essays</a>`;

        let html = '<a href="#" onclick="navigateTo(\'/\')" class="back-link">&larr; Back to Subjects</a>';
        if (data.essays.length === 0) {
            html += '<p>No essays found for this subject yet.</p>';
        } else {
            data.essays.forEach(essay => {
                html += `
                    <div class="essay-card" onclick="navigateTo('/essays/${essay.id}')">
                        <div class="essay-card-content">
                            <h2>${essay.title}</h2>
                            <p>${essay.description || ''}</p>
                            <div class="meta-tags">
                                <span>${essay.qualification || ''}</span>
                                <span>${essay.exam_board || ''}</span>
                                <span>${essay.response_count} examples available</span>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        contentArea.innerHTML = html;
    } catch (error) {
        console.error('Failed to load essays:', error);
        contentArea.innerHTML = '<div class="placeholder-box"><h2>Error loading essays. Please try again later.</h2></div>';
    }
}

// Loads the full marking tool for a specific essay
async function loadMarkingToolPage(essayId) {
    contentArea.innerHTML = '<div class="placeholder-box"><h2>Loading Marking Tool...</h2></div>';
    try {
        const response = await fetch(`${API_BASE_URL}/api/essays/${essayId}`);
        if (!response.ok) throw new Error('Network response was not ok');
        const essay = await response.json();

        mainTitle.innerHTML = `<a href="/">${essay.title}</a>`;

        let studentOptions = '<option value="">-- Choose a student --</option>';
        essay.responses.forEach((resp, index) => {
            studentOptions += `<option value="${index}">${resp.student_name} (${resp.grade}/${essay.total_marks} marks)</option>`;
        });

        const html = `
            <a href="#" onclick="navigateTo('/subjects/${essay.subject.id}')" class="back-link">&larr; Back to Essay List</a>
            <div class="overview-section">
                <h3>Essay Details</h3>
                <div class="question-box">
                    <div class="question-text">${essay.full_question}</div>
                    <div class="question-marks">${essay.mark_scheme || ''}</div>
                </div>
                <div class="batch-info">
                    <div class="info-card"><strong>Total Marks:</strong><br>${essay.total_marks}</div>
                    <div class="info-card"><strong>Class Average:</strong><br>${essay.average_grade.toFixed(1)}/${essay.total_marks}</div>
                </div>
            </div>
            <div class="student-selector">
                <label for="student-dropdown">Select Student to View Marked Work:</label>
                <select id="student-dropdown">${studentOptions}</select>
            </div>
            <div id="students-container">
                 <div class="placeholder-box">
                    <p>Please select a student from the dropdown to see their work.</p>
                </div>
            </div>
        `;
        contentArea.innerHTML = html;
        
        // Add event listener to the new dropdown
        const dropdown = document.getElementById('student-dropdown');
        dropdown.addEventListener('change', () => showStudent(essay.responses, essay.total_marks));

    } catch (error) {
        console.error('Failed to load marking tool:', error);
        contentArea.innerHTML = '<div class="placeholder-box"><h2>Error loading marking tool. Please try again later.</h2></div>';
    }
}


function showStudent(responses, totalMarks) {
    const dropdown = document.getElementById('student-dropdown');
    const selectedIndex = dropdown.value;
    const container = document.getElementById('students-container');

    if (selectedIndex === "") {
        container.innerHTML = `<div class="placeholder-box"><p>Please select a student from the dropdown to see their work.</p></div>`;
        return;
    }

    const studentData = responses[selectedIndex];
    
    // Process highlights and comments
    let answerHtml = studentData.full_text;
    if (studentData.highlights) {
        studentData.highlights.forEach(h => {
             // Basic replacement - a more robust solution would handle overlapping highlights
            answerHtml = answerHtml.replace(h.text, 
                `<span class="highlight highlight-${h.type}">${h.text}<span class="comment">${h.comment}</span></span>`
            );
        });
    }

    let strengthsHtml = studentData.feedback.strengths.map(s => `<li>${s}</li>`).join('');
    let improvementsHtml = studentData.feedback.improvements.map(i => `<li>${i}</li>`).join('');

    const studentHtml = `
        <div class="student-work active">
            <div class="student-header">
                ${studentData.student_name} - Candidate: ${studentData.candidate_number} - Grade: ${studentData.grade}/${totalMarks}
            </div>
            <div class="student-content">
                <div class="answer-section">
                    <div class="answer-header">Student Response:</div>
                    <div class="student-answer">${answerHtml}</div>
                </div>
                
                <!-- We can add the 'Improved Section' logic here if needed -->

                <div class="feedback-section">
                    <div class="feedback-header">Detailed Feedback</div>
                    <div class="feedback-grid">
                        <div class="feedback-column strengths">
                            <h4>✅ Strengths</h4>
                            <ul>${strengthsHtml}</ul>
                        </div>
                        <div class="feedback-column improvements">
                            <h4>🔄 Areas for Improvement</h4>
                            <ul>${improvementsHtml}</ul>
                        </div>
                    </div>
                    <div class="next-steps">
                        <strong>Next Steps:</strong> ${studentData.feedback.next_steps}
                    </div>
                    <div class="grade-box">
                        Grade: ${studentData.grade}/${totalMarks} marks
                    </div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = studentHtml;
}


// --- NAVIGATION ---
function navigateTo(path) {
    window.location.hash = path;
}

// Listen for hash changes to route
window.addEventListener('hashchange', router);
// Initial load
router();
