const firebaseConfig = {
    apiKey: "AIzaSyAjYvet05v6rzEIzBhp4vtxw-C5IGWeW2c",
    authDomain: "getamanna-south-mv.firebaseapp.com",
    projectId: "getamanna-south-mv",
    storageBucket: "getamanna-south-mv.firebasestorage.app",
    messagingSenderId: "105394338078",
    appId: "1:105394338078:web:0d8d2296c495a97e37310f",
    measurementId: "G-RX0Q3YZ91W"
};

firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();

let currentUserData = null;

window.addEventListener("DOMContentLoaded", () => {
    const dateInput = document.getElementById("att-date");
    if (dateInput) dateInput.valueAsDate = new Date();
});

// 1. AUTH STATE & LOGIN
auth.onAuthStateChanged(async (user) => {
    if (user) {
        document.getElementById("login-section").classList.add("hidden");
        document.getElementById("user-info").classList.remove("hidden");

        const roleRef = db.collection("user_roles").doc(user.email.toLowerCase());
        const roleDoc = await roleRef.get();
        if (roleDoc.exists) {
            currentUserData = roleDoc.data();
        } else {
            currentUserData = { email: user.email, name: "ප්‍රධාන පරිපාලක", role: "admin", admissionNo: "" };
            await roleRef.set(currentUserData);
        }

        document.getElementById("welcome-text").innerText = `ආයුබෝවන්, ${currentUserData.name} (${currentUserData.role.toUpperCase()})`;

        if (currentUserData.role === "parent") {
            document.getElementById("parent-portal").classList.remove("hidden");
            await loadParentPortal(currentUserData.admissionNo);
        } else {
            document.getElementById("staff-dashboard").classList.remove("hidden");
            await loadAllClasses();
        }
    } else {
        document.getElementById("login-section").classList.remove("hidden");
        document.getElementById("user-info").classList.add("hidden");
        document.getElementById("staff-dashboard").classList.add("hidden");
        document.getElementById("parent-portal").classList.add("hidden");
    }
});

window.login = async () => {
    const email = document.getElementById("login-email").value.trim();
    const pass = document.getElementById("login-password").value.trim();
    const errEl = document.getElementById("login-error");
    errEl.innerText = "";
    try {
        await auth.signInWithEmailAndPassword(email, pass);
    } catch (e) {
           errEl.innerText = "දෝෂය: " + e.message;
    }
};

window.logout = () => auth.signOut();

window.showTab = (tabId, btn) => {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.add("hidden"));
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.getElementById(tabId).classList.remove("hidden");
    btn.classList.add("active");
};

// 2. CLASSES & STUDENTS
window.createClass = async () => {
    const year = document.getElementById("cls-year").value;
    const grade = document.getElementById("cls-grade").value;
    const stream = document.getElementById("cls-stream").value.trim() || "General";
    const section = document.getElementById("cls-section").value.trim().toUpperCase();
    const teacher = document.getElementById("cls-teacher").value.trim();

    if (!grade || !section) return alert("ශ්‍රේණිය සහ පන්තිය (Section) ඇතුළත් කරන්න.");
    const classLabel = `${year} - ${grade} ශ්‍රේණිය (${stream}) - ${section}`;

    await db.collection("classes").add({ year, grade, stream, section, teacher, classLabel });
    alert("නව පන්තිය සාර්ථකව සාදන ලදී!");
    await loadAllClasses();
};

async function loadAllClasses() {
    const snap = await db.collection("classes").get();
    let options = `<option value="">-- පන්තිය තෝරන්න --</option>`;
    snap.forEach(d => {
        const c = d.data();
        options += `<option value="${d.id}">${c.classLabel}</option>`;
    });
    ["stu-class-select", "att-class-select", "mark-class-select", "msg-class-select"].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = options;
    });
}

window.createStudent = async () => {
    const admissionNo = document.getElementById("stu-adm").value.trim();
    const fullName = document.getElementById("stu-name").value.trim();
    const classId = document.getElementById("stu-class-select").value;
    const parentName = document.getElementById("stu-parent").value.trim();
    const phone = document.getElementById("stu-phone").value.trim();

    if (!admissionNo || !fullName || !classId) return alert("ඇතුළත් වීමේ අංකය, නම සහ පන්තිය අනිවාර්ය වේ.");
    await db.collection("students").doc(admissionNo).set({ admissionNo, fullName, classId, parentName, phone });
    alert("ශිෂ්‍යයා සාර්ථකව ලියාපදිංචි කරන ලදී!");
    document.getElementById("stu-adm").value = "";
    document.getElementById("stu-name").value = "";
};
// 3. BULK ATTENDANCE
window.loadStudentsForAttendance = async () => {
    const classId = document.getElementById("att-class-select").value;
    const container = document.getElementById("att-list-container");
    const btn = document.getElementById("save-att-btn");
    if (!classId) { container.innerHTML = ""; btn.classList.add("hidden"); return; }

    const snap = await db.collection("students").where("classId", "==", classId).get();
    if (snap.empty) { container.innerHTML = "<p>මෙම පන්තියේ ළමුන් නොමැත.</p>"; btn.classList.add("hidden"); return; }

    let html = `<table><tr><th>ඇතුළත් වීමේ අංකය</th><th>ශිෂ්‍යයාගේ නම</th><th>පැමිණීම</th></tr>`;
    snap.forEach(d => {
        const s = d.data();
        html += `<tr>
            <td>${s.admissionNo}</td>
            <td>${s.fullName}</td>
            <td><input type="checkbox" class="att-chk" data-adm="${s.admissionNo}" data-name="${s.fullName}" checked style="width:20px;height:20px;"> පැමිණ ඇත</td>
        </tr>`;
    });
    html += `</table>`;
    container.innerHTML = html;
    btn.classList.remove("hidden");
};

window.saveBulkAttendance = async () => {
    const classId = document.getElementById("att-class-select").value;
    const date = document.getElementById("att-date").value;
    if (!date) return alert("දිනය තෝරන්න.");

    const checks = document.querySelectorAll(".att-chk");
    for (let chk of checks) {
        const adm = chk.dataset.adm;
        const docId = `${date}_${adm}`;
        await db.collection("attendance").doc(docId).set({
            admissionNo: adm,
            studentName: chk.dataset.name,
            classId,
            date,
            isPresent: chk.checked
        });
    }
    alert("පන්තියේ සියලුම ළමුන්ගේ පැමිණීම සුරකින ලදී!");
};

// 4. BULK EXAM MARKS
window.loadStudentsForMarks = async () => {
    const classId = document.getElementById("mark-class-select").value;
    const container = document.getElementById("marks-list-container");
    const btn = document.getElementById("save-marks-btn");
    if (!classId) { container.innerHTML = ""; btn.classList.add("hidden"); return; }

    const snap = await db.collection("students").where("classId", "==", classId).get();
    if (snap.empty) { container.innerHTML = "<p>මෙම පන්තියේ ළමුන් නොමැත.</p>"; btn.classList.add("hidden"); return; }

    let html = `<table><tr><th>ඇතුළත් වීමේ අංකය</th><th>ශිෂ්‍යයාගේ නම</th><th>ලකුණු (0 - 100)</th></tr>`;
    snap.forEach(d => {
        const s = d.data();
        html += `<tr>
            <td>${s.admissionNo}</td>
            <td>${s.fullName}</td>
            <td><input type="number" class="mark-inp" data-adm="${s.admissionNo}" min="0" max="100" placeholder="ලකුණු"></td>
        </tr>`;
    });
    html += `</table>`;
    container.innerHTML = html;
    btn.classList.remove("hidden");
};

window.saveBulkMarks = async () => {
    const classId = document.getElementById("mark-class-select").value;
    const term = document.getElementById("mark-term").value;
    const subject = document.getElementById("mark-subject").value.trim();
    if (!subject) return alert("විෂය (Subject) ඇතුළත් කරන්න.");

    const inputs = document.querySelectorAll(".mark-inp");
    for (let inp of inputs) {
        if (inp.value !== "") {
            const adm = inp.dataset.adm;
            const docId = `${classId}_T${term}_${subject}_${adm}`;
            await db.collection("marks").doc(docId).set({
                admissionNo: adm,
                classId,
                term,
                subject,
                marks: parseFloat(inp.value)
            });
        }
    }
    alert("විභාග ලකුණු සාර්ථකව සුරකින ලදී!");
};

// 5. MESSAGES
window.sendMessage = async () => {
    const classId = document.getElementById("msg-class-select").value;
    const text = document.getElementById("msg-text").value.trim();
    if (!classId || !text) return alert("පන්තිය තෝරා පණිවිඩය ඇතුළත් කරන්න.");

    await db.collection("messages").add({
        classId,
        sender: currentUserData.name,
        text,
        createdAt: new Date().toLocaleString("si-LK")
    });
    document.getElementById("msg-text").value = "";
    alert("පණිවිඩය යවන ලදී!");
    await loadStaffMessages();
};

window.loadStaffMessages = async () => {
    const classId = document.getElementById("msg-class-select").value;
    const list = document.getElementById("staff-msg-list");
    if (!classId) return list.innerHTML = "";
    const snap = await db.collection("messages").where("classId", "==", classId).get();
    let html = "";
    snap.forEach(d => {
        const m = d.data();
        html += `<div style="padding:10px; border-bottom:1px solid #e2e8f0;"><b>${m.sender}</b> <small>(${m.createdAt})</small><br>${m.text}</div>`;
    });
    list.innerHTML = html || "<p>පණිවිඩ නොමැත.</p>";
};

// 6. USER ROLES
window.toggleAdmissionField = () => {
    const role = document.getElementById("role-type").value;
    document.getElementById("adm-link-box").classList.toggle("hidden", role !== "parent");
};

window.saveUserRole = async () => {
    const email = document.getElementById("role-email").value.trim().toLowerCase();
    const name = document.getElementById("role-name").value.trim();
    const role = document.getElementById("role-type").value;
    const admissionNo = document.getElementById("role-adm").value.trim();

    if (!email || !name) return alert("Email සහ නම ඇතුළත් කරන්න.");
    await db.collection("user_roles").doc(email).set({ email, name, role, admissionNo });
    alert("පරිශීලක අවසරය සාර්ථකව සුරකින ලදී!");
};

// 7. PARENT PORTAL
async function loadParentPortal(admissionNo) {
    if (!admissionNo) {
        document.getElementById("parent-student-title").innerText = "දරුවාගේ තොරතුරු සම්බන්ධ කර නොමැත.";
        return;
    }
    const stuDoc = await db.collection("students").doc(admissionNo).get();
    if (!stuDoc.exists) {
        document.getElementById("parent-student-title").innerText = "ශිෂ්‍ය තොරතුරු හමු නොවීය.";
        return;
    }
    const stu = stuDoc.data();
    document.getElementById("parent-student-title").innerText = `ශිෂ්‍යයා: ${stu.fullName} (ඇතුළත් වීමේ අංකය: ${stu.admissionNo})`;

    const msgSnap = await db.collection("messages").where("classId", "==", stu.classId).get();
    let msgHtml = "";
    msgSnap.forEach(d => {
        const m = d.data();
        msgHtml += `<div style="padding:10px; border-bottom:1px solid #e2e8f0;"><b>${m.sender}</b> <small>(${m.createdAt})</small><br>${m.text}</div>`;
    });
    document.getElementById("parent-msg-list").innerHTML = msgHtml || "<p>නව නිවේදන නොමැත.</p>";

    const attSnap = await db.collection("attendance").where("admissionNo", "==", admissionNo).get();
    let attHtml = `<table><tr><th>දිනය</th><th>තත්ත්වය</th></tr>`;
    attSnap.forEach(d => {
        const a = d.data();
        attHtml += `<tr><td>${a.date}</td><td><span class="badge ${a.isPresent ? 'badge-green' : 'badge-red'}">${a.isPresent ? 'පැමිණ ඇත' : 'නොපැමිණ ඇත'}</span></td></tr>`;
    });
    attHtml += `</table>`;
    document.getElementById("parent-att-list").innerHTML = attSnap.empty ? "<p>පැමිණීමේ වාර්තා නොමැත.</p>" : attHtml;

    const markSnap = await db.collection("marks").where("admissionNo", "==", admissionNo).get();
    let markHtml = `<table><tr><th>වාරය</th><th>විෂය</th><th>ලකුණු</th></tr>`;
    let total = 0, count = 0;
    markSnap.forEach(d => {
        const m = d.data();
        total += m.marks; count++;
        markHtml += `<tr><td>${m.term} වන වාරය</td><td>${m.subject}</td><td><b>${m.marks}</b></td></tr>`;
    });
    if (count > 0) {
        markHtml += `<tr style="background:#f8fafc;"><td colspan="2"><b>මුළු ලකුණු / සාමාන්‍යය (Average)</b></td><td><b>${total} (${(total/count).toFixed(1)}%)</b></td></tr>`;
    }
    markHtml += `</table>`;
    document.getElementById("parent-marks-list").innerHTML = markSnap.empty ? "<p>විභාග ලකුණු ඇතුළත් කර නොමැත.</p>" : markHtml;
}
