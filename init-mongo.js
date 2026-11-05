// Вибірка бази даних, що створено у контейнері
db = db.getSiblingDB('labdb');
// Створення колекції зі схемою валідації
db.createCollection("course_profiles", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         // Додаємо course_id до обов'язкових полів
         required: [ "course_id", "course_name", "teacher", "credits" ],
         properties: {
            course_id: { 
               bsonType: "int",
               description: "ID курсу з реляційної бази"
            },
            course_name: { bsonType: "string" },
            teacher: { bsonType: "string" },
            credits: { bsonType: "int", minimum: 1, maximum: 15 },
            attributes: { bsonType: "object" }
         }
      }
   }
});
// Вставка коректних документів
db.course_profiles.insertMany([
    {
        course_id: NumberInt(1),
        course_name: "Бази даних",
        teacher: "Коваленко К.К.",
        credits: NumberInt(5),
        attributes: {
            prerequisites: ["SQL", "Реляційна алгебра"],
            materials: {
                book: "Kleppmann M. Designing Data-Intensive Applications",
                lab_software: ["PostgreSQL", "Docker"]
            }
        }
    },
    {
        course_id: NumberInt(2),
        course_name: "Машинне навчання",
        teacher: "Коваленко К.К.",
        credits: NumberInt(6),
        attributes: {
            prerequisites: ["Лінійна алгебра", "Python"],
            exam_type: "Проєкт",
            github_repo_provided: true
        }
    }
]);
// Приклад А: Перевищення ліміту кредитів
try {
    db.course_profiles.insertOne({
        course_id: NumberInt(3),
        course_name: "Квантові обчислення",
        teacher: "Петренко П.П.",
        credits: NumberInt(20)
    });
} catch (e) {
    print("=== ОЧІКУВАНА ПОМИЛКА ВАЛІДАЦІЇ (Кредити > 15) ===");
    printjson(e); // Виведе детальну структуру помилки у лог
}
// Приклад Б: Відсутнє обов'язкове поле 'teacher'
try {
    db.course_profiles.insertOne({
        course_id: NumberInt(4),
        course_name: "Основи програмування",
        credits: NumberInt(5)
    });
} catch (e) {
    print("=== ОЧІКУВАНА ПОМИЛКА ВАЛІДАЦІЇ (Відсутній teacher) ===");
    printjson(e);
}