BEGIN TRANSACTION;

DELETE FROM exercise_set;
DELETE FROM exercise_log;
DELETE FROM workout_exercise_template;
DELETE FROM user_exercise_template;
DELETE FROM exercise_template;
DELETE FROM workout_log;
DELETE FROM user_workout_template;
DELETE FROM workout_template;
DELETE FROM workout_plan;

-- NOTE: user_ids 1, 2, 3 must exist in the user table when this script is executed
-- To start with a clean slate, first run seed_users.sql and then run seed_workouts.sql

-- Workout template INSERTS

INSERT INTO workout_template (id, creator_id, name, description) VALUES 
-- pekka
(1, 1, 'Pekan Koko Keho', 'Perusvoimaa koko kropalle, keskity puhtaisiin liikeratoihin.'),
-- matti
(2, 2, 'Matin Yläkeho', 'Pumppitreeni yläkropan lihaksille.'),
-- teppo
(3, 3, 'Tepon Kuntopiiri', 'Korkean sykkeen kestävyystreeni oman kehon painolla.');

INSERT INTO exercise_template (id, creator_id, name, category, target_sets, target_reps) VALUES 
-- pekka
(1, 1, 'Kyykky', 'Jalat', 3, 8),
(2, 1, 'Penkkipunnerrus', 'Rinta', 3, 10),
(3, 1, 'Maastaveto', 'Selkä', 3, 5),
-- matti
(4, 2, 'Pystypunnerrus', 'Olkapäät', 4, 10),
(5, 2, 'Leuanveto', 'Selkä', 4, 8),
(6, 2, 'Hauiskääntö', 'Kädet', 3, 12),
-- teppo
(7, 3, 'Etunojapunnerrus', 'Rinta', 4, 15),
(8, 3, 'Askelkyykky', 'Jalat', 3, 12),
(9, 3, 'Lankku', 'Keskivartalo', 3, 60);

INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES 
-- Kyykky, Penkkipunnerrus, Maastaveto -> Pekan Koko Keho
(1, 1, 0),
(1, 2, 1),
(1, 3, 2),
-- Pystypunnerrus, Leuanveto, Hauiskääntö -> Matin Yläkeho
(2, 4, 0),
(2, 5, 1),
(2, 6, 2),
-- Etunojapunnerrus, Askelkyykky, Lankku -> Tepon Kuntopiiri
(3, 7, 0),
(3, 8, 1),
(3, 9, 2);

INSERT OR IGNORE INTO tag (name) VALUES 
('Voima'), 
('Perustreeni'), 
('Koko Keho'),
('Yläkeho'), 
('Hypertrofia'),
('Kardio'), 
('Kehonpaino'), 
('Kiertoharjoittelu');

INSERT INTO workout_template_tag (workout_template_id, tag_id) VALUES 
-- Voima, Perustreeni, Koko Keho -> Pekan Koko Keho
(1, (SELECT id FROM tag WHERE name = 'Voima')),
(1, (SELECT id FROM tag WHERE name = 'Perustreeni')),
(1, (SELECT id FROM tag WHERE name = 'Koko Keho')),
-- Yläkeho, Hypertrofia -> Matin Yläkeho
(2, (SELECT id FROM tag WHERE name = 'Yläkeho')),
(2, (SELECT id FROM tag WHERE name = 'Hypertrofia')),
-- Kardio, Kehonpaino, Kiertoharjoittelu -> Tepon Kuntopiiri
(3, (SELECT id FROM tag WHERE name = 'Kardio')),
(3, (SELECT id FROM tag WHERE name = 'Kehonpaino')),
(3, (SELECT id FROM tag WHERE name = 'Kiertoharjoittelu'));

-- Workout log INSERTS

INSERT INTO workout_log (id, user_id, workout_template_id, name, notes, started_at, ended_at) VALUES 
(1, 1, 1, 'Pekan Koko Keho', 'Tuntui hyvältä, kyykyssä kulki hyvin!', '2026-10-01 10:00:00', '2026-10-01 11:15:00'),
(2, 2, 2, 'Matin Yläkeho', 'Hyvä pystypunnerruksen energiataso.', '2026-10-02 17:00:00', '2026-10-02 18:00:00'),
(3, 3, 3, 'Tepon Kuntopiiri', 'Lyhyet palautusajat sarjojen välissä.', '2026-10-03 08:30:00', '2026-10-03 09:15:00');

INSERT INTO exercise_log (id, workout_id, exercise_template_id, name, notes) VALUES 
-- Kyykky, Penkkipunnerrus, Maastaveto -> Pekan Koko Keho
(1, 1, 1, 'Kyykky', 'Syvyys oli hyvä jokaisessa sarjassa.'),
(2, 1, 2, 'Penkkipunnerrus', 'Viimeinen sarja oli tiukka.'),
(3, 1, 3, 'Maastaveto', 'Ote piti hyvin ilman remmejä.'),
-- Pystypunnerrus, Leuanveto, Hauiskääntö -> Matin Yläkeho
(4, 2, 4, 'Pystypunnerrus', 'Olkapäissä hyvä tuntuma.'),
(5, 2, 5, 'Leuanveto', 'Lisäpainona 5kg vyöllä.'),
(6, 2, 6, 'Hauiskääntö', 'Pumppi kohdillaan.'),
-- Etunojapunnerrus, Askelkyykky, Lankku -> Tepon Kuntopiiri
(7, 3, 7, 'Etunojapunnerrus', 'Omalla kehonpainolla.'),
(8, 3, 8, 'Askelkyykky', 'Käsipainot käsissä.'),
(9, 3, 9, 'Lankku', 'Toistot ilmoitettu sekunteina.');

INSERT INTO exercise_set (exercise_id, order_index, reps, weight) VALUES
-- Kyykky (Pekan Koko Keho)
(1, 0, 8, 80.0),
(1, 1, 8, 85.0),
(1, 2, 8, 90.0),
-- Penkkipunnerrus (Pekan Koko Keho)
(2, 0, 10, 60.0),
(2, 1, 10, 62.5),
(2, 2, 8, 65.0),
-- Maastaveto (Pekan Koko Keho)
(3, 0, 5, 100.0),
(3, 1, 5, 110.0),
(3, 2, 5, 120.0),
-- Pystypunnerrus (Matin Yläkeho)
(4, 0, 10, 40.0),
(4, 1, 10, 42.5),
(4, 2, 10, 45.0),
(4, 3, 8, 45.0),
-- Leuanveto (Matin Yläkeho)
(5, 0, 8, 5.0),
(5, 1, 8, 5.0),
(5, 2, 8, 5.0),
(5, 3, 6, 5.0),
-- Hauiskääntö (Matin Yläkeho)
(6, 0, 12, 12.5),
(6, 1, 12, 12.5),
(6, 2, 10, 15.0),
-- Etunojapunnerrus (Tepon Kuntopiiri)
(7, 0, 15, 0.0),
(7, 1, 15, 0.0),
(7, 2, 15, 0.0),
(7, 3, 12, 0.0),
-- Askelkyykky (Tepon Kuntopiiri)
(8, 0, 12, 10.0),
(8, 1, 12, 10.0),
(8, 2, 12, 10.0),
-- Lankku (Tepon Kuntopiiri)
(9, 0, 60, 0.0),
(9, 1, 60, 0.0),
(9, 2, 45, 0.0);

-- User comment INSERTS

INSERT INTO user_comment (user_id, workout_template_id, content, created_at) VALUES
(2, 1, 'Hyvältä näyttää tämä krapulaton perussetti! Sopii hyvin viikon alkuun.', '2026-10-02 12:30:00'),
(3, 1, 'Pohjessa voisi olla vielä pohjenousu mukana, mutta toimii näinkin.', '2026-10-02 14:15:00'),
(1, 3, 'Rankka setti! Syke nousee kyllä todella nopeasti tässä.', '2026-10-03 10:00:00');

INSERT INTO user_comment (user_id, exercise_template_id, content, created_at) VALUES 
(3, 1, 'Muista pitää keskivartalo tiukkana heti alasmenossa.', '2026-10-02 15:00:00'),
(1, 5, 'Vedätkö leuat myötä- vai vastaotteella?', '2026-10-02 18:45:00'),
(2, 5, 'Aina myötäotteella niin ottaa paremmin yläselkään!', '2026-10-02 19:10:00');

COMMIT;
