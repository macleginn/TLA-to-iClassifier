CREATE TABLE `bibliography` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `title` TEXT NOT NULL,
        `abbreviation`  TEXT, -- for dictionaries
        `url`   TEXT, -- for online publications
        `comments`      TEXT
);
CREATE TABLE `lemmas` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `transliteration`       TEXT,
        `meaning`       TEXT,
        `root`  TEXT,
        `lb_status`     TEXT,
        `lexical_field` TEXT,
        `demotic`       TEXT,
        `demotic_meaning`       TEXT,
        `coptic`        TEXT,
        `coptic_meaning`        TEXT,
        `comments`      TEXT
, `lexical_field_secondary` TEXT, demotic_lexicon_entry int, coptic_lexicon_entry int, coptic_lexicon_entry_pages text, demotic_lexicon_entry_pages text);
CREATE TABLE `lemma_variants` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `lemma_id` INTEGER NOT NULL,
        `transliteration`       TEXT NOT NULL,
        `meaning`       TEXT,
        `source_id` INTEGER,
        `source_pages`  TEXT,
        `primary` INTEGER NOT NULL CHECK(`primary` in (1,0)),
        FOREIGN KEY(`lemma_id`) REFERENCES `lemmas`(`id`)
        FOREIGN KEY(`source_id`) REFERENCES `bibliography`(`id`)
);
CREATE TABLE `lemma_other_languages` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `lemma_id`      INTEGER NOT NULL,
        `source_root`   TEXT NOT NULL,
        `source_meaning`        TEXT,
        `contact_type`  TEXT,
        `certainty_level`       INTEGER CHECK(`certainty_level` in (1,2,3)),
        `hoch_n_occurrences`    INTEGER,
        `comments`      TEXT,
        FOREIGN KEY(`lemma_id`) REFERENCES `lemmas`(`id`)
);
CREATE TABLE `lemma_other_languages_lexicon_entries` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `lemma_id`      INTEGER NOT NULL,
        `dictionary_id` INTEGER NOT NULL,
        `pages` TEXT,
        `url`   TEXT,
        FOREIGN KEY(`lemma_id`) REFERENCES `lemmas`(`id`),
        FOREIGN KEY(`dictionary_id`) REFERENCES `bibliography`(`id`)
);
CREATE TABLE `texts` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `text_name`     TEXT,
        `comments`      TEXT
);
CREATE TABLE `text_biblio` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `text_id`       INTEGER,
        `publication_id`        INTEGER,
        `page_n`        TEXT,
        `comments`      TEXT,
        FOREIGN KEY(`text_id`) REFERENCES `texts`(`id`),
        FOREIGN KEY(`publication_id`) REFERENCES `bibliography`(`id`)
);
CREATE TABLE `witnesses` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `name`  TEXT NOT NULL,
        `supertext_id`  INTEGER,
        `genre` TEXT,
        `object_type`   TEXT,
        `location`      TEXT,
        `script`        TEXT,
        `period_date_start`     TEXT,
        `period_date_end`       TEXT,
        `chrono_date_start`     TEXT,
        `chrono_date_end`       TEXT,
        `url`   TEXT,
        `comments`      TEXT,
        FOREIGN KEY(`supertext_id`) REFERENCES `texts`(`id`)
);
CREATE TABLE `witness_biblio` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `witness_id`    INTEGER NOT NULL,
        `publication_id`        INTEGER NOT NULL,
        `page_n`        TEXT,
        `comments`      TEXT,
        FOREIGN KEY(`witness_id`) REFERENCES `witnesses`(`id`),
        FOREIGN KEY(`publication_id`) REFERENCES `bibliography`(`id`)
);
CREATE TABLE `witness_pictures` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `witness_id`    INTEGER NOT NULL,
        `base64`        TEXT NOT NULL,
        `comments`      TEXT, `title` text,
        FOREIGN KEY(`witness_id`) REFERENCES `witnesses`(`id`)
);
CREATE TABLE `tokens` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `lemma_id`      INTEGER,
        `is_part_of_compound`   INTEGER CHECK(`is_part_of_compound` in (0,1)),
        `compound_id`   INTEGER,
        `supertext_id`  INTEGER,
        `coordinates_in_txt`    TEXT,
        `witness_id`    INTEGER,
        `coordinates_in_witness`        TEXT,
        `mdc`   TEXT,
        `mdc_w_markup`  TEXT,
        `transliteration`       TEXT,
        `classification_status` TEXT CHECK(`classification_status` in ("CL","NC","NR","TNP")),
        `sign_comments` TEXT,
        `context_meaning`       TEXT,
        `syntactic_relation`    TEXT,
        `pos`   TEXT,
        `register`      TEXT,
        `comments`      TEXT,
        `other` TEXT, `phonetic_reconstruction` text, `translation` text, -- for future use
        FOREIGN KEY (`lemma_id`) REFERENCES `lemmas`(`id`),
        FOREIGN KEY (`compound_id`) REFERENCES `compounds`(`id`),
        FOREIGN KEY (`supertext_id`) REFERENCES `texts`(`id`),
        FOREIGN KEY (`witness_id`) REFERENCES `witnesses`(`id`)
);
CREATE TABLE `token_biblio` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `token_id`      INTEGER,
        `publication_id`        INTEGER,
        `page_n`        TEXT,
        `comments`      TEXT,
        FOREIGN KEY (`token_id`) REFERENCES `tokens`(`id`),
        FOREIGN KEY (`publication_id`) REFERENCES `bibliography`(`id`)
);
CREATE TABLE `clf_pictures` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `clf_parse_id`  INTEGER NOT NULL,
        `base64`        TEXT,
        `coords`        TEXT,
        `comments`      TEXT, `witness_picture_id` int,
        FOREIGN KEY (`clf_parse_id`) REFERENCES `clf_parses`(`id`)
);
CREATE TABLE `token_pictures` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `token_id`      INTEGER,
        `base64`        TEXT,
        `coords`        TEXT,

        `comments`      TEXT, `witness_picture_id` int references `witness_pictures`(`id`), `title` text,
        FOREIGN KEY (`token_id`) REFERENCES `tokens`(`id`)
);
CREATE TABLE `compounds` (
        `id`    INTEGER PRIMARY KEY AUTOINCREMENT,
        `lemma1_id`     INTEGER NOT NULL,
        `lemma2_id`     INTEGER NOT NULL,
        `meaning`       TEXT,
        `comments`      TEXT,
        FOREIGN KEY (`lemma1_id`) REFERENCES `lemmas`(`id`),
        FOREIGN KEY (`lemma2_id`) REFERENCES `lemmas`(`id`)
);
CREATE TABLE `compound_biblio` (
       `id`             INTEGER PRIMARY KEY AUTOINCREMENT,
       `compound_id`    INTEGER NOT NULL,
       `publication_id` INTEGER NOT NULL,
       `page_n`         TEXT,
       `comments`       TEXT,
       FOREIGN KEY (`compound_id`) REFERENCES `compounds`(`id`),
       FOREIGN KEY (`publication_id`) REFERENCES `bibliography`(`id`)
);
CREATE TABLE lemma_cognates
(
  id             integer
    constraint lemma_cognates_pk
      primary key autoincrement,
  language       text,
  cognate        text,
  meaning        text,
  publication_id int
    references bibliography(id),
  page_n         text,
  discussion     text,
  lemma_id       int not null
    references lemmas(id)
);
CREATE TABLE "clf_parses"
(
  id                  INTEGER
    primary key autoincrement,
  token_id            INTEGER
    references tokens,
  gardiner_number     TEXT,
  clf_n               INTEGER,
  clf_type            TEXT,
  clf_level           INTEGER,
  semantic_relation   TEXT,
  phonetic_classifier INTEGER,
  false_etymology     INTEGER,
  comments            TEXT,
  check (`clf_level` in (1, 2, 3, 4, 5, 6)),
  check (`false_etymology` in (0, 1)),
  check (`phonetic_classifier` in (0, 1))
);
CREATE TABLE clf_comments
(
    id      integer
        primary key autoincrement,
    clf     text
        unique,
    comment text
);
CREATE TABLE clf_meanings
(
    id           integer
        primary key autoincrement,
    clf          text,
    meaning      text,
    source_id    integer
        references bibliography,
    source_pages text
);
CREATE TABLE subtokens (
id integer primary key autoincrement,
`token_id` integer,
`subtoken_id` integer
);