import os
from dataclasses import dataclass

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCHEDULE_DIR = os.path.join(PROJECT_DIR, 'data', 'downloads', 'schedule')


@dataclass(frozen=True)
class DataConfig:
    data_dir: str = os.path.join(PROJECT_DIR, 'data')
    db_dir: str = os.path.join(data_dir, 'db')
    downloads_dir: str = os.path.join(data_dir, 'downloads')


INSTITUTES: dict = {
    'economy': {
        'name': 'Экономики и Управления АПК',
        'courses': {
            1: os.path.join(SCHEDULE_DIR, 'economy', '1', 'economy_first_course.pdf'),
            2: os.path.join(SCHEDULE_DIR, 'economy', '2', 'economy_second_course.pdf'),
            3: os.path.join(SCHEDULE_DIR, 'economy', '3', 'economy_third_course.pdf'),
            4: os.path.join(SCHEDULE_DIR, 'economy', '4', 'economy_fourth_course.pdf'),
        }
    },
    'agro_bio': {
        'name': 'Агробиотехнологии',
        'courses': {
            1: os.path.join(SCHEDULE_DIR, 'agro_bio', '1', 'agro_bio_first_course.pdf'),
            2: os.path.join(SCHEDULE_DIR, 'agro_bio', '2', 'agro_bio_second_course.pdf'),
            3: os.path.join(SCHEDULE_DIR, 'agro_bio', '3', 'agro_bio_third_course.pdf'),
            4: os.path.join(SCHEDULE_DIR, 'agro_bio', '4', 'agro_bio_fourth_course.pdf'),
        }
    },
}
