import os
import time

import click

from logging_settings import set_logger
from utilits import check_for_changes_in_cabel_conditions_until_it_change, check_file_exist_or_not_empty, \
    connect_monitors_automatically, create_string_for_execute, set_monitors_position_manually, \
    get_monitors_data_from_xrandr, match_monitor_with_cabel


def monitoring_activity():
    while True:
        check_for_changes_in_cabel_conditions_until_it_change(CABELS_CONDITIONS_FILE_PATH)

        if not check_file_exist_or_not_empty(MONITORS_CONFIG_FILE_PATH):

            monitors_data_from_xrandr = get_monitors_data_from_xrandr()
            connect_monitors_automatically(monitors_data_from_xrandr)

            execute_command = create_string_for_execute(monitors_data_from_xrandr)
            logger.info(execute_command)
            # os.system(execute_command)


def position_manually():
    my_monitors_position = set_monitors_position_manually()
    execute_command = create_string_for_execute(my_monitors_position)
    logger.info(execute_command)
    # os.system(execute_command)


def wrong_input(mode, settings):
    line_break = '\n'
    logger.critical(f'\nСкрипт не имеет настройки: {mode}\n\n'
                    f'\nЗапустите скрит с одной из следующих настроек:{line_break}{line_break}\n'
                    f'{f"{line_break}".join(settings)}')


@click.command()
@click.argument('mode', default='monitoring-connectivity')
def start_app(mode):
    options = ['monitoring-connectivity', 'set_monitors_positions_manually']

    start = {
        'monitoring-connectivity': monitoring_activity,
        'set-monitors-positions-manually': position_manually,
        'match-monitor-with-cabel': match_monitor_with_cabel
    }

    if not start.get(mode):
        wrong_input(mode, options)

    else:
        start[mode]()


# TODO: подумать над красивым консольным выводом логгирования
# TODO: help приделать
# TODO: определение, какой монитор является каким
# TODO: приделать сохранение настроек в файл
# TODO: приделать возможность вызова сохраненных настроек из файла
# TODO: help должен вызываться

if __name__ == '__main__':
    logger = set_logger()

    MONITORS_CONFIG_FILE_PATH = 'my_monitor_layout.json'
    CABELS_CONDITIONS_FILE_PATH = 'cabels_conditions_from_card0.json'

    mode = start_app()
