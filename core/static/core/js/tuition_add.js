document.addEventListener('DOMContentLoaded', () => {
    const studentSelect = document.getElementById('student');
    const classSelect = document.getElementById('english_class');
    const paidInput = document.getElementById('paid_amount');
    const totalDisplay = document.getElementById('total-fee');
    const remainingDisplay = document.getElementById('remaining-fee');

    // Parse enrolled classes data
    let studentClassesMap = {};
    const dataTag = document.getElementById('studentClassesData');
    if (dataTag) {
        try {
            studentClassesMap = JSON.parse(dataTag.textContent || '{}');
        } catch (e) {
            console.error('Error parsing studentClassesData:', e);
        }
    }

    // Keep all initial class options as fallback
    const initialClassOptions = classSelect ? Array.from(classSelect.options).map(opt => ({
        value: opt.value,
        text: opt.textContent.trim(),
        fee: opt.dataset.fee || '0'
    })) : [];

    function formatMoney(value) {
        return new Intl.NumberFormat('vi-VN').format(value) + ' đ';
    }

    function updateFee() {
        if (!classSelect || classSelect.selectedIndex < 0) {
            if (totalDisplay) totalDisplay.textContent = formatMoney(0);
            if (remainingDisplay) remainingDisplay.textContent = formatMoney(0);
            return;
        }
        const option = classSelect.options[classSelect.selectedIndex];
        const total = Number(option ? option.dataset.fee || 0 : 0);
        const paid = Math.max(0, Number(paidInput ? paidInput.value || 0 : 0));

        if (totalDisplay) totalDisplay.textContent = formatMoney(total);
        if (remainingDisplay) remainingDisplay.textContent = formatMoney(Math.max(total - paid, 0));
    }

    function onStudentChanged() {
        if (!classSelect) return;
        const studentId = studentSelect ? studentSelect.value : '';
        classSelect.innerHTML = '';

        if (!studentId) {
            // Restore default options
            initialClassOptions.forEach(opt => {
                const el = document.createElement('option');
                el.value = opt.value;
                el.textContent = opt.text;
                el.dataset.fee = opt.fee;
                classSelect.appendChild(el);
            });
            updateFee();
            return;
        }

        const enrolledClasses = studentClassesMap[studentId] || [];

        if (enrolledClasses.length > 0) {
            const defaultOpt = document.createElement('option');
            defaultOpt.value = '';
            defaultOpt.textContent = `-- Chọn lớp (${enrolledClasses.length} lớp học viên đang theo học) --`;
            classSelect.appendChild(defaultOpt);

            enrolledClasses.forEach((cls) => {
                const el = document.createElement('option');
                el.value = cls.id;
                el.textContent = `${cls.name} (${cls.course_name})`;
                el.dataset.fee = cls.tuition;
                classSelect.appendChild(el);
            });

            // Tự động chọn nếu học viên chỉ đang theo học đúng 1 lớp
            if (enrolledClasses.length === 1) {
                classSelect.selectedIndex = 1;
            }
        } else {
            const noOpt = document.createElement('option');
            noOpt.value = '';
            noOpt.textContent = '⚠️ Học viên chưa ghi danh vào lớp nào';
            classSelect.appendChild(noOpt);
        }

        updateFee();
    }

    if (studentSelect) {
        studentSelect.addEventListener('change', onStudentChanged);
    }
    if (classSelect) {
        classSelect.addEventListener('change', updateFee);
    }
    if (paidInput) {
        paidInput.addEventListener('input', updateFee);
    }

    updateFee();
});
