-- Таблиця студентів
CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL
);
-- Таблиця викладачів
CREATE TABLE teachers (
    teacher_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL
);
-- Таблиця навчальних курсів
CREATE TABLE courses (
    course_id SERIAL PRIMARY KEY,
     -- Забороняє створення курсів з однаковими назвами
    course_name VARCHAR(150) NOT NULL UNIQUE,
    teacher_id INTEGER NOT NULL REFERENCES teachers(teacher_id)
);
-- Довідник фіксованих балів
CREATE TABLE grade_types (
    grade_id SERIAL PRIMARY KEY,
    grade_value INTEGER NOT NULL CHECK (grade_value BETWEEN 1 AND 100)
);
-- Таблиця залікових книжок, яка зберігає агреговані дані
CREATE TABLE gradebooks (
    gradebook_id SERIAL PRIMARY KEY,
    -- Посилання на студента
    student_id INTEGER NOT NULL REFERENCES students(student_id),
    -- Кількість оцінок не може бути від'ємною
    grade_count INTEGER NOT NULL DEFAULT 0 CHECK (grade_count >= 0),
    -- Загальна сума балів не може бути від'ємною
    total_score INTEGER NOT NULL DEFAULT 0 CHECK (total_score >= 0)
);
-- Таблиця історії виставлених оцінок
CREATE TABLE grades (
    grade_record_id SERIAL PRIMARY KEY,
    gradebook_id INTEGER NOT NULL REFERENCES gradebooks(gradebook_id),
    course_id INTEGER NOT NULL REFERENCES courses(course_id),
    grade_id INTEGER NOT NULL REFERENCES grade_types(grade_id),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);
-- Індекси для прискорення JOIN при вибірці історії оцінок
CREATE INDEX idx_grades_gradebook ON grades(gradebook_id);
CREATE INDEX idx_grades_course ON grades(course_id);
-- НАПОВНЕННЯ БАЗИ ТЕСТОВИМИ ДАНИМИ
INSERT INTO students (full_name) VALUES ('Іванов І.І.'), ('Петренко П.П.');
INSERT INTO teachers (full_name) VALUES ('Коваленко К.К.');
INSERT INTO courses (course_name, teacher_id) VALUES
    ('Бази даних', 1),
    ('Машинне навчання', 1);
INSERT INTO grade_types (grade_value) VALUES (60), (75), (80), (90), (100);
INSERT INTO gradebooks (student_id, grade_count, total_score) VALUES (1, 0, 0);